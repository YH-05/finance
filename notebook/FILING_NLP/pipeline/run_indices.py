"""indices_v1 ランナー: universe + membership parquet から index_filter 絞り込み.

``run_pilot.py`` の汎用化版. ランダムサンプリングを廃止し,
``universe_indices_v1.parquet`` と ``membership_indices_v1.parquet`` を
CIK で join, ``--index-filter`` (in_spx / in_sox / in_riy / in_ray) で絞り込んで
``runner.run_pipeline`` に渡す薄い CLI ラッパー.

出力先は ``config.py`` の indices_v1 定数に統一:

- sections/indices_v1/
- chunks/indices_v1/
- checkpoints/indices_v1_progress.json
- logs/indices_v1_run.log, logs/indices_v1_errors.jsonl, logs/indices_v1_summary.json

実行例
------
::

    uv run python -m notebook.FILING_NLP.pipeline.run_indices \\
        --run-id indices_v1 \\
        --universe /Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet \\
        --membership /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet \\
        --index-filter in_spx \\
        [--workers 8] [--rate-rps 5] [--rate-burst 10] [--flush-every 5]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# EDGAR_IDENTITY の .env ロードは main() 内で実行する (import 時の副作用を排除)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATH = _REPO_ROOT / ".env"

import pandas as pd  # noqa: E402

sys.path.insert(0, str(_REPO_ROOT))
from notebook.FILING_NLP.pipeline import config, runner, utils  # noqa: E402

log = logging.getLogger(__name__)

# index_filter として受け付ける値 (utils 経由で参照)
_INDEX_FILTER_CHOICES: tuple[str, ...] = utils.INDEX_FILTER_CHOICES


# ----------------------------------------------------------------------------
# logging / tokenizer
# ----------------------------------------------------------------------------
def _setup_logging(run_id: str, logs_dir: Path) -> None:
    """StreamHandler + FileHandler の logging 設定 (utils.setup_pipeline_logging に委譲)."""
    utils.setup_pipeline_logging(run_id, logs_dir, suffix="run")


def _load_tokenizer() -> Any:
    """HuggingFace tokenizer をロード (config.TOKENIZER_MODEL_ID)."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        config.TOKENIZER_MODEL_ID, trust_remote_code=True
    )


# ----------------------------------------------------------------------------
# universe loader
# ----------------------------------------------------------------------------
def _load_universe(
    universe_path: Path, membership_path: Path, index_filter: str
) -> pd.DataFrame:
    """universe + membership parquet をロードして index_filter で絞り込む.

    Parameters
    ----------
    universe_path : Path
        ``universe_indices_v1.parquet`` のパス.
        必須列: ``cik``, ``ticker`` (+ メタデータ列).
    membership_path : Path
        ``membership_indices_v1.parquet`` のパス.
        必須列: ``cik``, ``in_spx`` / ``in_sox`` / ``in_riy`` / ``in_ray``.
    index_filter : str
        ``in_spx`` / ``in_sox`` / ``in_riy`` / ``in_ray`` のいずれか.
        membership の該当列が True の CIK のみを返す.

    Returns
    -------
    pd.DataFrame
        ``runner.run_pipeline`` が期待する universe_v2 互換形式
        (少なくとも ``cik`` / ``ticker`` 列を含む).
    """
    if index_filter not in _INDEX_FILTER_CHOICES:
        raise ValueError(
            f"index_filter must be one of {_INDEX_FILTER_CHOICES}, got {index_filter!r}"
        )

    universe = pd.read_parquet(universe_path)
    membership = pd.read_parquet(membership_path)

    utils.validate_index_filter(index_filter, membership)

    # CIK で inner join し、index_filter == True を抽出
    target_ciks = membership.loc[membership[index_filter].astype(bool), ["cik"]]
    target_ciks["cik"] = target_ciks["cik"].astype("int64")

    merged = universe.merge(target_ciks, on="cik", how="inner")
    merged["cik"] = merged["cik"].astype("int64")
    # runner は ticker を str として扱う
    if "ticker" in merged.columns:
        merged["ticker"] = merged["ticker"].astype(str)
    return merged.reset_index(drop=True)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_indices",
        description="FILING_NLP v2 indices_v1 runner (universe + membership 絞り込み)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="run id (出力ディレクトリ名 / log prefix)",
    )
    parser.add_argument(
        "--universe",
        type=str,
        required=True,
        help="universe_indices_v1.parquet のパス",
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
        "--workers",
        type=int,
        default=config.DEFAULT_MAX_WORKERS,
        help="ThreadPoolExecutor の最大 workers 数",
    )
    parser.add_argument(
        "--rate-rps",
        type=float,
        default=config.RATE_LIMIT_RPS,
        help="req/sec 上限 (TokenBucket rate)",
    )
    parser.add_argument(
        "--rate-burst",
        type=int,
        default=config.RATE_LIMIT_BURST,
        help="TokenBucket burst capacity",
    )
    parser.add_argument(
        "--flush-every",
        type=int,
        default=5,
        help="N CIK ごとに flush (per-CIK writer では no-op)",
    )
    return parser.parse_args(argv)


def _assert_nas_mounted() -> None:
    """NAS マウントの存在を起動時に検証. 未マウントなら fail-fast (utils 経由)."""
    utils.assert_nas_mounted(Path(config.NAS_ROOT))


def _setup_edgar_identity() -> None:
    """EDGAR_IDENTITY を edgar.set_identity に登録し、legacy parser 警告を抑制."""
    import edgar

    if "EDGAR_IDENTITY" not in os.environ:
        raise RuntimeError(
            "EDGAR_IDENTITY 環境変数 (または .env) が必要です。 "
            "'Name email@example.com' 形式で設定してください。"
        )
    edgar.set_identity(os.environ["EDGAR_IDENTITY"])

    class _LegacyParserFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return "falling back to legacy parser" not in record.getMessage()

    logging.getLogger("edgar.core").addFilter(_LegacyParserFilter())


def main(argv: list[str] | None = None) -> None:
    """CLI エントリポイント."""
    args = _parse_args(argv)

    # .env から EDGAR_IDENTITY を取り込み (import 時の副作用を排除し main 内で実行)
    utils.load_edgar_identity_from_env(_ENV_PATH)

    # 起動時 fail-fast (NAS マウント確認)
    _assert_nas_mounted()

    # 出力先 (config.py の indices_v1 定数 + run_id で構築)
    sections_dir = config.SECTIONS_DIR / args.run_id
    chunks_dir = config.CHUNKS_DIR / args.run_id
    filings_dir = config.FILINGS_METADATA_DIR / args.run_id
    checkpoint_path = config.INDICES_V1_PROGRESS_PATH
    errors_path = config.LOGS_DIR / f"{args.run_id}_errors.jsonl"
    summary_path = config.LOGS_DIR / f"{args.run_id}_summary.json"

    _setup_logging(args.run_id, config.LOGS_DIR)
    log.info("=" * 80)
    log.info("INDICES_V1 RUN: %s", args.run_id)
    log.info("=" * 80)
    log.info("args: %s", vars(args))
    log.info("output sections:   %s", sections_dir)
    log.info("output chunks:     %s", chunks_dir)
    log.info("checkpoint:        %s", checkpoint_path)
    log.info("errors log:        %s", errors_path)

    # universe + membership ロード + 絞り込み
    universe_path = Path(args.universe)
    membership_path = Path(args.membership)
    log.info("loading universe:   %s", universe_path)
    log.info("loading membership: %s", membership_path)
    universe = _load_universe(universe_path, membership_path, args.index_filter)
    log.info(
        "filtered universe: %d CIKs (--index-filter %s)",
        len(universe),
        args.index_filter,
    )
    if len(universe) > 0:
        log.info(
            "sample tickers head: %s",
            universe[["cik", "ticker"]].head(10).to_string(index=False),
        )

    # EDGAR identity / tokenizer (NAS 検証後・universe 確定後にロード)
    _setup_edgar_identity()
    log.info("EDGAR_IDENTITY: %s", utils.mask_edgar_identity(os.environ.get("EDGAR_IDENTITY")))
    log.info("loading tokenizer: %s", config.TOKENIZER_MODEL_ID)
    tokenizer = _load_tokenizer()
    log.info("tokenizer ready: %s", type(tokenizer).__name__)

    # 実行: runner.run_pipeline に委譲
    log.info(
        "starting pipeline workers=%d rate=%.1f burst=%d flush_every=%d",
        args.workers,
        args.rate_rps,
        args.rate_burst,
        args.flush_every,
    )
    summary = runner.run_pipeline(
        universe=universe,
        tokenizer=tokenizer,
        sections_dir=sections_dir,
        chunks_dir=chunks_dir,
        filings_metadata_dir=filings_dir,
        checkpoint_path=checkpoint_path,
        errors_path=errors_path,
        max_workers=args.workers,
        rate_rps=args.rate_rps,
        rate_burst=args.rate_burst,
        flush_every=args.flush_every,
    )

    log.info("=" * 80)
    log.info("INDICES_V1 FINISHED: %s", args.run_id)
    log.info("=" * 80)
    for k, v in summary.items():
        log.info("  %s: %s", k, v)

    # summary 保存
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("summary saved: %s", summary_path)


if __name__ == "__main__":
    main()
