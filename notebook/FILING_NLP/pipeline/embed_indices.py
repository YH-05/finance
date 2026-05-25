"""indices_v1 embedding ランナー: per-CIK chunks → gte-Qwen2 embedding 生成.

``05_embedding.ipynb`` Cell 4-6 のエンコードロジックをモジュール化した CLI.
NAS の ``chunks/indices_v1/chunks_cik{cik:010d}.parquet`` を per-CIK で順次読み込み、
gte-Qwen2-1.5B-instruct (MPS bfloat16) で encode し、
``embeddings/indices_v1/embeddings_cik{cik:010d}.npy`` (float32 1536 dim,
L2 normalized) + ``chunks_meta_cik{cik:010d}.parquet`` を per-CIK 分離で出力する.

設計方針 (HF1 確定済み)
-----------------------
- **per-CIK shard**: chunks も embeddings も per-CIK ファイル分離
- **NaN マーカー resume**: ``np.full((N, 1536), np.nan, dtype=np.float32)`` で初期化、
  ``np.isnan(arr).any(axis=1)`` で未処理 index を取得
- **CIK 単位 Checkpoint**: ``checkpoints/indices_v1_embed_progress.json`` で完了 CIK を記録
- **リトライなし**: バッチ単位失敗は ``unresolved_chunks.jsonl`` に append-only 記録
- **rate limiter 不要**: SEC 通信なし、HF cache 前提

実行例
------
::

    uv run python -m notebook.FILING_NLP.pipeline.embed_indices \\
        --run-id indices_v1 \\
        --membership /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/\
membership_indices_v1.parquet \\
        --index-filter in_spx \\
        [--batch-size 16] [--max-length 512] [--device mps] [--dtype bfloat16] \\
        [--checkpoint-every-n-batches 10] [--force-reencode]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from notebook.FILING_NLP.pipeline import config, utils  # noqa: E402

log = logging.getLogger(__name__)

# index_filter として受け付ける値 (utils 経由で参照)
_INDEX_FILTER_CHOICES: tuple[str, ...] = utils.INDEX_FILTER_CHOICES
_DTYPE_CHOICES: tuple[str, ...] = ("bfloat16", "float16", "float32")
_DEVICE_CHOICES: tuple[str, ...] = ("mps", "cpu", "cuda")


# ----------------------------------------------------------------------------
# Model / tokenizer loader
# ----------------------------------------------------------------------------
def _load_model(model_id: str, device: str, dtype: str) -> tuple[Any, Any]:
    """gte-Qwen2-1.5B-instruct と tokenizer をロードする.

    ``AutoModel.from_pretrained(model_id, trust_remote_code=True, dtype=torch.bfloat16,
    device_map='mps', low_cpu_mem_usage=True)`` で MPS bfloat16 配置する。
    ``use_cache=False`` を forward 時に渡すことで modeling_qwen.py の
    DynamicCache 互換性問題を回避する (encode 側で対応)。

    Parameters
    ----------
    model_id : str
        HuggingFace モデル ID (例: ``Alibaba-NLP/gte-Qwen2-1.5B-instruct``).
    device : str
        ``mps`` / ``cpu`` / ``cuda``.
    dtype : str
        ``bfloat16`` / ``float16`` / ``float32``.

    Returns
    -------
    tuple[Any, Any]
        ``(model, tokenizer)``. ``model`` は ``.eval()`` 済み.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer

    dtype_map: dict[str, torch.dtype] = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    torch_dtype = dtype_map[dtype]

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_id,
        trust_remote_code=True,
        dtype=torch_dtype,
        device_map=device,
        low_cpu_mem_usage=True,
    )
    model.eval()
    return model, tokenizer


# ----------------------------------------------------------------------------
# Pooling
# ----------------------------------------------------------------------------
def last_token_pool(last_hidden_states: Any, attention_mask: Any) -> Any:
    """各サンプルで最終 non-pad トークンの hidden state を取り出す.

    right-padding / left-padding 両対応 (05_embedding.ipynb 流用).

    Parameters
    ----------
    last_hidden_states : torch.Tensor
        shape (batch, seq, hidden) のモデル出力.
    attention_mask : torch.Tensor
        shape (batch, seq) の attention mask.

    Returns
    -------
    torch.Tensor
        shape (batch, hidden) の pooled vector.
    """
    import torch

    left_padding = bool((attention_mask[:, -1].sum() == attention_mask.shape[0]).item())
    if left_padding:
        return last_hidden_states[:, -1]
    seq_lens = attention_mask.sum(dim=1) - 1
    batch_size = last_hidden_states.shape[0]
    return last_hidden_states[
        torch.arange(batch_size, device=last_hidden_states.device), seq_lens
    ]


# ----------------------------------------------------------------------------
# Encoder
# ----------------------------------------------------------------------------
def encode_texts(
    texts: list[str],
    model: Any,
    tokenizer: Any,
    batch_size: int,
    max_length: int,
) -> np.ndarray:
    """テキストのリストを 1536 次元の正規化済みベクトルにエンコード.

    バッチ encode → last_token_pool → ``F.normalize(p=2, dim=1)`` →
    float32 numpy array (N, hidden_dim) を返す.

    ``use_cache=False`` で modeling_qwen.py の DynamicCache 互換性問題を回避.

    Parameters
    ----------
    texts : list[str]
        対象テキスト.
    model : Any
        ``AutoModel`` ロード済みモデル.
    tokenizer : Any
        対応 ``AutoTokenizer``.
    batch_size : int
        バッチサイズ.
    max_length : int
        トークン上限 (chunks は 512 tok 以下なので 512 で十分).

    Returns
    -------
    np.ndarray
        shape (len(texts), hidden_dim), float32, L2 normalized.
    """
    import torch
    import torch.nn.functional as F

    if not texts:
        return np.zeros((0, config.EMBEDDING_VECTOR_DIM), dtype=np.float32)

    # model のデバイスを取得 (どこに配置されているか)
    try:
        device = next(model.parameters()).device
    except StopIteration:
        device = torch.device("cpu")

    all_vecs: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tokenizer(
                batch,
                max_length=max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(device)
            out = model(**enc, use_cache=False, return_dict=True)
            vecs = last_token_pool(out.last_hidden_state, enc["attention_mask"])
            vecs = F.normalize(vecs, p=2, dim=1)
            all_vecs.append(vecs.to(torch.float32).cpu().numpy())
    return np.vstack(all_vecs)


# ----------------------------------------------------------------------------
# Per-CIK embedding
# ----------------------------------------------------------------------------
def _try_resume(
    out_npy: Path, n: int, dim: int, force_reencode: bool
) -> tuple[np.ndarray, np.ndarray]:
    """既存 .npy から resume 用配列と未処理マスクを構築.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(embeddings (N, dim) array, unprocessed_mask (N,) bool)``.
    """
    if force_reencode or not out_npy.exists():
        return (
            np.full((n, dim), np.nan, dtype=np.float32),
            np.ones(n, dtype=bool),
        )
    try:
        existing = np.load(out_npy, allow_pickle=False)
    except (OSError, ValueError, EOFError) as e:
        log.warning("既存 %s の読み込み失敗 (%s). 新規作成.", out_npy, e)
        return (
            np.full((n, dim), np.nan, dtype=np.float32),
            np.ones(n, dtype=bool),
        )
    if existing.shape != (n, dim) or existing.dtype != np.float32:
        log.warning(
            "%s の shape/dtype 不一致 (%s/%s vs (%d, %d)/float32). 新規作成.",
            out_npy,
            existing.shape,
            existing.dtype,
            n,
            dim,
        )
        return (
            np.full((n, dim), np.nan, dtype=np.float32),
            np.ones(n, dtype=bool),
        )
    unprocessed = np.isnan(existing).any(axis=1)
    return existing, unprocessed


def _append_unresolved(
    unresolved_path: Path, cik: int, batch_idx: int, error: str
) -> None:
    """失敗 batch を unresolved_chunks.jsonl に append-only で記録."""
    unresolved_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(),
        "cik": cik,
        "batch_idx": batch_idx,
        "error": error,
    }
    with unresolved_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")


def embed_cik(
    cik: int,
    chunks_parquet: Path,
    out_npy: Path,
    out_meta: Path,
    model: Any,
    tokenizer: Any,
    batch_size: int,
    max_length: int,
    force_reencode: bool,
    checkpoint_every_n_batches: int,
    unresolved_path: Path,
) -> dict[str, Any]:
    """1 CIK の chunks を読み込み embedding を生成する.

    - 既存 .npy があれば NaN マーカー (``np.isnan(arr).any(axis=1)``) で未処理 index 取得
    - ``force_reencode=True`` で全件再生成
    - ``checkpoint_every_n_batches`` バッチごとに ``np.save`` で永続化
    - 失敗バッチは ``unresolved_chunks.jsonl`` に append-only

    Parameters
    ----------
    cik : int
        対象 CIK.
    chunks_parquet : Path
        ``chunks_cik{cik:010d}.parquet`` のパス.
    out_npy : Path
        embedding 出力先 ``embeddings_cik{cik:010d}.npy``.
    out_meta : Path
        meta 出力先 ``chunks_meta_cik{cik:010d}.parquet``.
    model : Any
        ロード済みモデル.
    tokenizer : Any
        ロード済み tokenizer.
    batch_size : int
        encode バッチサイズ.
    max_length : int
        tokenizer 最大トークン長.
    force_reencode : bool
        True なら既存 .npy を破棄して全件再生成.
    checkpoint_every_n_batches : int
        N バッチごとに ``np.save`` で中間保存.
    unresolved_path : Path
        失敗 batch 記録先 jsonl.

    Returns
    -------
    dict
        ``{'n_chunks': int, 'n_embedded': int, 'elapsed_sec': float}``.
    """
    t_start = time.perf_counter()
    df = pd.read_parquet(chunks_parquet)
    n = len(df)
    dim = config.EMBEDDING_VECTOR_DIM

    # meta を先に書き出す (途中クラッシュでも meta は残る)
    out_meta.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_meta, index=False)

    if n == 0:
        out_npy.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_npy, np.zeros((0, dim), dtype=np.float32))
        return {"n_chunks": 0, "n_embedded": 0, "elapsed_sec": 0.0}

    embeddings, unprocessed_mask = _try_resume(out_npy, n, dim, force_reencode)
    unprocessed_idx = np.where(unprocessed_mask)[0]

    if len(unprocessed_idx) == 0:
        log.info(
            "CIK %d: 既に全 %d chunk エンコード済み (skip).",
            cik,
            n,
        )
        return {
            "n_chunks": n,
            "n_embedded": 0,
            "elapsed_sec": round(time.perf_counter() - t_start, 2),
        }

    texts_all: list[str] = df["text"].tolist()
    pending_texts = [texts_all[i] for i in unprocessed_idx]

    out_npy.parent.mkdir(parents=True, exist_ok=True)

    n_embedded = 0
    batches_since_ckpt = 0
    for batch_idx, start in enumerate(range(0, len(pending_texts), batch_size)):
        end = min(start + batch_size, len(pending_texts))
        batch_texts = pending_texts[start:end]
        batch_indices = unprocessed_idx[start:end]
        try:
            vecs = encode_texts(
                batch_texts,
                model=model,
                tokenizer=tokenizer,
                batch_size=batch_size,
                max_length=max_length,
            )
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            log.error(
                "CIK %d: batch %d (size %d) failed: %s",
                cik,
                batch_idx,
                len(batch_texts),
                err,
            )
            _append_unresolved(unresolved_path, cik, batch_idx, err)
            continue

        embeddings[batch_indices] = vecs
        n_embedded += len(batch_indices)
        batches_since_ckpt += 1

        if batches_since_ckpt >= checkpoint_every_n_batches:
            np.save(out_npy, embeddings)
            batches_since_ckpt = 0

    # 最終保存
    np.save(out_npy, embeddings)

    elapsed = round(time.perf_counter() - t_start, 2)
    log.info(
        "CIK %d: %d/%d chunks embedded (%.1f s).",
        cik,
        n_embedded,
        len(unprocessed_idx),
        elapsed,
    )
    return {"n_chunks": n, "n_embedded": n_embedded, "elapsed_sec": elapsed}


# ----------------------------------------------------------------------------
# Membership loader (CIK list 抽出)
# ----------------------------------------------------------------------------
def _load_target_ciks(membership_path: Path, index_filter: str) -> list[int]:
    """membership parquet から index_filter == True の CIK list を取得.

    Parameters
    ----------
    membership_path : Path
        ``membership_indices_v1.parquet`` のパス.
        必須列: ``cik``, ``in_spx`` / ``in_sox`` / ``in_riy`` / ``in_ray``.
    index_filter : str
        ``in_spx`` / ``in_sox`` / ``in_riy`` / ``in_ray`` のいずれか.

    Returns
    -------
    list[int]
        該当 CIK の int リスト.
    """
    if index_filter not in _INDEX_FILTER_CHOICES:
        raise ValueError(
            f"index_filter must be one of {_INDEX_FILTER_CHOICES}, got {index_filter!r}"
        )
    membership = pd.read_parquet(membership_path)
    utils.validate_index_filter(index_filter, membership)
    target = membership.loc[membership[index_filter].astype(bool), "cik"]
    return [int(x) for x in target.tolist()]


# ----------------------------------------------------------------------------
# Checkpoint (CIK 単位)
# ----------------------------------------------------------------------------
class _EmbedCheckpoint:
    """CIK 単位の embedding 完了状況を JSON で永続化."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {
                "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "started_at": datetime.now().isoformat(),
                "completed": {},
            }
            self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp.json")
        tmp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        tmp.replace(self.path)

    def is_done(self, cik: int) -> bool:
        return str(cik) in self.data["completed"]

    def mark_done(self, cik: int, summary: dict[str, Any]) -> None:
        self.data["completed"][str(cik)] = {
            "finished_at": datetime.now().isoformat(),
            **summary,
        }
        self._save()


# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
def _setup_logging(run_id: str, logs_dir: Path) -> None:
    """logging 設定 (utils.setup_pipeline_logging に委譲、suffix=embed_run)."""
    utils.setup_pipeline_logging(run_id, logs_dir, suffix="embed_run")


# ----------------------------------------------------------------------------
# HF cache (notebook/FILING_NLP/_helpers.py 流儀)
# ----------------------------------------------------------------------------
def _setup_hf_cache() -> Path:
    """HuggingFace モデルキャッシュを notebook/FILING_NLP/data/hf_cache に向ける.

    ``transformers`` を import する前に呼ぶこと.
    """
    hf_cache_dir = _REPO_ROOT / "notebook" / "FILING_NLP" / "data" / "hf_cache"
    hf_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(hf_cache_dir))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_cache_dir / "hub"))
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    return hf_cache_dir


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="embed_indices",
        description=(
            "FILING_NLP v2 indices_v1 embedding runner "
            "(per-CIK chunks → gte-Qwen2 embedding)"
        ),
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="run id (chunks/embeddings サブディレクトリ名 / log prefix)",
    )
    parser.add_argument(
        "--membership",
        type=str,
        required=True,
        help="membership_indices_v1.parquet のパス",
    )
    parser.add_argument(
        "--index-filter",
        type=str,
        required=True,
        choices=list(_INDEX_FILTER_CHOICES),
        help="絞り込む index (membership 列名)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=config.EMBEDDING_BATCH_SIZE,
        help="encode バッチサイズ (MPS OOM 時は引き下げ)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=config.EMBEDDING_MAX_LENGTH,
        help="tokenizer 最大トークン長",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=config.EMBEDDING_DEVICE,
        choices=list(_DEVICE_CHOICES),
        help="torch device",
    )
    parser.add_argument(
        "--dtype",
        type=str,
        default=config.EMBEDDING_DTYPE,
        choices=list(_DTYPE_CHOICES),
        help="torch dtype",
    )
    parser.add_argument(
        "--checkpoint-every-n-batches",
        type=int,
        default=10,
        help="N バッチごとに .npy を中間保存",
    )
    parser.add_argument(
        "--force-reencode",
        action="store_true",
        help="既存 .npy を無視して全件再生成",
    )
    return parser.parse_args(argv)


def _assert_nas_mounted() -> None:
    """NAS マウントの存在を起動時に検証. 未マウントなら fail-fast (utils 経由)."""
    utils.assert_nas_mounted(Path(config.NAS_ROOT))


_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def main(argv: list[str] | None = None) -> None:
    """CLI エントリポイント."""
    args = _parse_args(argv)

    # run_id のバリデーション (パストラバーサル防止)
    if not _RUN_ID_RE.fullmatch(args.run_id):
        raise SystemExit(
            f"--run-id must match [A-Za-z0-9_-]{{1,64}}, got {args.run_id!r}"
        )

    # 起動時 fail-fast (NAS マウント確認)
    _assert_nas_mounted()

    # 出力先 (config.py の indices_v1 定数 + run_id で構築)
    chunks_dir = config.CHUNKS_DIR / args.run_id
    embeddings_dir = config.EMBEDDINGS_DIR / args.run_id
    checkpoint_path = config.INDICES_V1_EMBED_PROGRESS_PATH
    unresolved_path = config.LOGS_DIR / "unresolved_chunks.jsonl"
    errors_path = config.LOGS_DIR / f"{args.run_id}_embed_errors.jsonl"
    summary_path = config.LOGS_DIR / f"{args.run_id}_embed_summary.json"

    _setup_logging(args.run_id, config.LOGS_DIR)
    log.info("=" * 80)
    log.info("INDICES_V1 EMBED RUN: %s", args.run_id)
    log.info("=" * 80)
    log.info("args: %s", vars(args))
    log.info("chunks dir:        %s", chunks_dir)
    log.info("embeddings dir:    %s", embeddings_dir)
    log.info("checkpoint:        %s", checkpoint_path)
    log.info("unresolved log:    %s", unresolved_path)

    # membership ロード + 絞り込み
    membership_path = Path(args.membership)
    log.info("loading membership: %s", membership_path)
    target_ciks = _load_target_ciks(membership_path, args.index_filter)
    log.info(
        "filtered CIKs: %d (--index-filter %s)",
        len(target_ciks),
        args.index_filter,
    )

    # CIK 単位 Checkpoint
    checkpoint = _EmbedCheckpoint(checkpoint_path)
    todo = [c for c in target_ciks if not checkpoint.is_done(c)]
    log.info(
        "todo CIKs: %d (skipped %d via checkpoint)",
        len(todo),
        len(target_ciks) - len(todo),
    )

    embeddings_dir.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "run_id": args.run_id,
        "index_filter": args.index_filter,
        "n_target_ciks": len(target_ciks),
        "n_todo_ciks": len(todo),
        "n_processed": 0,
        "n_failed": 0,
        "n_skipped_no_chunks": 0,
        "total_chunks": 0,
        "total_embedded": 0,
        "started_at": datetime.now().isoformat(),
    }

    if not todo:
        log.info("全 CIK 完了済み. 終了.")
        summary["finished_at"] = datetime.now().isoformat()
        summary["elapsed_sec"] = 0.0
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    # モデルロード (todo がある場合のみ)
    _setup_hf_cache()
    log.info(
        "loading model: %s (device=%s, dtype=%s)",
        config.TOKENIZER_MODEL_ID,
        args.device,
        args.dtype,
    )
    model, tokenizer = _load_model(
        config.TOKENIZER_MODEL_ID, device=args.device, dtype=args.dtype
    )
    log.info("model loaded: %s", type(model).__name__)

    t0 = time.time()
    errors_fp = errors_path.open("a", encoding="utf-8")
    try:
        for cik in todo:
            chunks_parquet = chunks_dir / f"chunks_cik{cik:010d}.parquet"
            if not chunks_parquet.exists():
                log.warning(
                    "CIK %d: chunks parquet not found (%s). skip.", cik, chunks_parquet
                )
                summary["n_skipped_no_chunks"] += 1
                checkpoint.mark_done(
                    cik, {"status": "skipped_no_chunks", "n_chunks": 0, "n_embedded": 0}
                )
                continue

            out_npy = embeddings_dir / f"embeddings_cik{cik:010d}.npy"
            out_meta = embeddings_dir / f"chunks_meta_cik{cik:010d}.parquet"
            try:
                result = embed_cik(
                    cik=cik,
                    chunks_parquet=chunks_parquet,
                    out_npy=out_npy,
                    out_meta=out_meta,
                    model=model,
                    tokenizer=tokenizer,
                    batch_size=args.batch_size,
                    max_length=args.max_length,
                    force_reencode=args.force_reencode,
                    checkpoint_every_n_batches=args.checkpoint_every_n_batches,
                    unresolved_path=unresolved_path,
                )
            except Exception as e:
                summary["n_failed"] += 1
                err = f"{type(e).__name__}: {e}"
                log.error("CIK %d fatal: %s", cik, err)
                errors_fp.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "cik": cik,
                            "phase": "embed_cik",
                            "error": err,
                            "traceback": traceback.format_exc(limit=3),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                errors_fp.flush()
                # 失敗時は checkpoint に記録せず, resume で再試行可能にする
                continue

            checkpoint.mark_done(cik, {"status": "success", **result})
            summary["n_processed"] += 1
            summary["total_chunks"] += result["n_chunks"]
            summary["total_embedded"] += result["n_embedded"]
    finally:
        errors_fp.close()

    summary["finished_at"] = datetime.now().isoformat()
    summary["elapsed_sec"] = round(time.time() - t0, 1)

    log.info("=" * 80)
    log.info("INDICES_V1 EMBED FINISHED: %s", args.run_id)
    log.info("=" * 80)
    for k, v in summary.items():
        log.info("  %s: %s", k, v)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("summary saved: %s", summary_path)


if __name__ == "__main__":
    main()
