"""notebook/FILING_NLP/pipeline/embed_indices.py の単体テスト.

CLI 引数解析、NaN マーカー resume ロジック、embed_cik の I/O 配線、
unresolved batches ログ追記の振る舞いを検証する.

torch / transformers / numpy 演算は重いので、モデル/トークナイザ/encoder は
ダミーオブジェクト + monkeypatch で置き換え、I/O とロジックのみテストする.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import pytest

if TYPE_CHECKING:
    from types import ModuleType


_EI_MODULE_CACHE: ModuleType | None = None


def _load_embed_indices() -> ModuleType:
    """notebook/FILING_NLP/pipeline/embed_indices.py をモジュールとしてロード.

    Notes
    -----
    モジュールスコープのキャッシュを保持し、重複した ``exec_module`` を回避する。
    これにより複数テスト実行時の ``sys.path`` 累積汚染を抑制する。
    """
    global _EI_MODULE_CACHE  # noqa: PLW0603
    if _EI_MODULE_CACHE is not None:
        return _EI_MODULE_CACHE
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent  # tests/notebook/FILING_NLP/ → repo
    module_path = (
        repo_root / "notebook" / "FILING_NLP" / "pipeline" / "embed_indices.py"
    )
    pkg_root = str(repo_root)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    spec = importlib.util.spec_from_file_location("_ei_test_module", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _EI_MODULE_CACHE = module
    return module


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def chunks_df() -> pd.DataFrame:
    """10 chunk 分のテスト DataFrame."""
    n = 10
    return pd.DataFrame(
        {
            "chunk_id": [str(i).zfill(6) for i in range(n)],
            "filing_id": ["0000000001"] * n,
            "cik": [320193] * n,
            "ticker": ["AAPL"] * n,
            "form": ["10-K"] * n,
            "filing_date": ["2024-01-01"] * n,
            "fiscal_year": [2024] * n,
            "section_key": ["item_1a"] * n,
            "section_role": ["risk_factors"] * n,
            "subsection_idx": [0] * n,
            "subsection_title": [""] * n,
            "chunk_idx": list(range(n)),
            "text": [f"chunk text {i}" for i in range(n)],
            "token_count": [10] * n,
        }
    )


@pytest.fixture
def chunks_parquet(tmp_path: Path, chunks_df: pd.DataFrame) -> Path:
    p = tmp_path / "chunks_cik0000320193.parquet"
    chunks_df.to_parquet(p, index=False)
    return p


@pytest.fixture
def membership_df() -> pd.DataFrame:
    """4 銘柄分の membership_indices_v1 形式 DataFrame."""
    return pd.DataFrame(
        {
            "cik": [320193, 14693, 1067983, 789019],
            "in_spx": [True, True, True, True],
            "in_sox": [False, False, False, True],
            "in_riy": [False, True, False, True],
            "in_ray": [False, False, True, True],
        }
    )


@pytest.fixture
def membership_parquet(tmp_path: Path, membership_df: pd.DataFrame) -> Path:
    p = tmp_path / "membership_indices_v1.parquet"
    membership_df.to_parquet(p, index=False)
    return p


# -----------------------------------------------------------------------------
# Dummy encoder factory
# -----------------------------------------------------------------------------
def _make_dummy_encode(
    dim: int = 1536,
) -> Callable[[list[str], Any, Any, int, int], np.ndarray]:
    """encode_texts と同じシグネチャのダミー encoder を返す.

    入力 list[str] に対して shape (N, dim) の正規化済み float32 array を返す.
    """

    def _encode(
        texts: list[str],
        model: Any,
        tokenizer: Any,
        batch_size: int,
        max_length: int,
    ) -> np.ndarray:
        n = len(texts)
        rng = np.random.default_rng(seed=42)
        arr = rng.standard_normal((n, dim)).astype(np.float32)
        # L2 normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.where(norms == 0, 1.0, norms)

    return _encode


# -----------------------------------------------------------------------------
# last_token_pool
# -----------------------------------------------------------------------------
class TestLastTokenPool:
    def test_正常系_right_padding_attention_maskで最終非paddingトークンを取得(
        self,
    ) -> None:
        torch = pytest.importorskip("torch")
        ei = _load_embed_indices()
        # batch=2, seq=4, hidden=3
        # sample0: seq_len=3 (positions 0,1,2 valid), sample1: seq_len=2 (positions 0,1)
        hidden = torch.tensor(
            [
                [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0], [9.0, 9.0, 9.0]],
                [[4.0, 4.0, 4.0], [5.0, 5.0, 5.0], [9.0, 9.0, 9.0], [9.0, 9.0, 9.0]],
            ]
        )
        mask = torch.tensor(
            [
                [1, 1, 1, 0],  # right-padding, seq_len=3 → take index 2
                [1, 1, 0, 0],  # right-padding, seq_len=2 → take index 1
            ]
        )
        pooled = ei.last_token_pool(hidden, mask)
        assert pooled.shape == (2, 3)
        assert torch.allclose(pooled[0], torch.tensor([3.0, 3.0, 3.0]))
        assert torch.allclose(pooled[1], torch.tensor([5.0, 5.0, 5.0]))

    def test_正常系_left_paddingで最終位置トークンを取得(self) -> None:
        torch = pytest.importorskip("torch")
        ei = _load_embed_indices()
        # left-padding: mask の最終列がすべて 1 (batch_size と一致)
        hidden = torch.tensor(
            [
                [[9.0, 9.0], [9.0, 9.0], [1.0, 1.0], [3.0, 3.0]],
                [[9.0, 9.0], [9.0, 9.0], [2.0, 2.0], [5.0, 5.0]],
            ]
        )
        mask = torch.tensor(
            [
                [0, 0, 1, 1],
                [0, 0, 1, 1],
            ]
        )
        pooled = ei.last_token_pool(hidden, mask)
        assert pooled.shape == (2, 2)
        assert torch.allclose(pooled[0], torch.tensor([3.0, 3.0]))
        assert torch.allclose(pooled[1], torch.tensor([5.0, 5.0]))


# -----------------------------------------------------------------------------
# embed_cik
# -----------------------------------------------------------------------------
class TestEmbedCik:
    def test_正常系_新規エンコードで全chunkがNaNなしのembedding生成(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()
        # encode_texts をダミーに差し替え
        monkeypatch.setattr(ei, "encode_texts", _make_dummy_encode(dim=1536))

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        assert summary["n_chunks"] == 10
        assert summary["n_embedded"] == 10
        assert out_npy.exists()
        assert out_meta.exists()

        arr = np.load(out_npy)
        assert arr.shape == (10, 1536)
        assert arr.dtype == np.float32
        assert not np.isnan(arr).any()
        # L2 ノルムが ~1.0
        norms = np.linalg.norm(arr, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

    def test_正常系_NaNマーカーresume_部分的にエンコード済みなら未処理分のみ再生成(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        # 既存 npy を「半分処理済み (前半 5 行は値, 後半 5 行は NaN)」状態で配置
        n = 10
        dim = 1536
        existing = np.full((n, dim), np.nan, dtype=np.float32)
        rng = np.random.default_rng(seed=0)
        existing[:5] = rng.standard_normal((5, dim)).astype(np.float32)
        existing[:5] /= np.linalg.norm(existing[:5], axis=1, keepdims=True)
        np.save(out_npy, existing)

        # encode_texts は呼ばれたら入力長を記録
        call_log: list[int] = []

        def _spy_encode(
            texts: list[str],
            model: Any,
            tokenizer: Any,
            batch_size: int,
            max_length: int,
        ) -> np.ndarray:
            call_log.append(len(texts))
            n_in = len(texts)
            arr = np.full((n_in, dim), 0.5, dtype=np.float32)
            return arr / np.linalg.norm(arr, axis=1, keepdims=True)

        monkeypatch.setattr(ei, "encode_texts", _spy_encode)

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=10,  # 一括 batch でも未処理分のみが渡される
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        # 5 chunk のみ再エンコード
        assert summary["n_embedded"] == 5
        assert sum(call_log) == 5

        arr = np.load(out_npy)
        # 全行が NaN なし
        assert not np.isnan(arr).any()
        # 前半 5 行は既存値を保持 (上書きされない)
        assert np.allclose(arr[:5], existing[:5])

    def test_正常系_force_reencodeで全件再生成(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        # 既存 npy 全件埋まっている状態 (識別可能な乱数値、seed=1)
        n = 10
        dim = 1536
        rng_existing = np.random.default_rng(seed=1)
        existing = rng_existing.standard_normal((n, dim)).astype(np.float32)
        existing /= np.linalg.norm(existing, axis=1, keepdims=True)
        np.save(out_npy, existing)

        call_log: list[int] = []
        rng_new = np.random.default_rng(seed=2)

        def _spy_encode(
            texts: list[str],
            model: Any,
            tokenizer: Any,
            batch_size: int,
            max_length: int,
        ) -> np.ndarray:
            call_log.append(len(texts))
            n_in = len(texts)
            arr = rng_new.standard_normal((n_in, dim)).astype(np.float32)
            return arr / np.linalg.norm(arr, axis=1, keepdims=True)

        monkeypatch.setattr(ei, "encode_texts", _spy_encode)

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=10,
            max_length=512,
            force_reencode=True,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        assert summary["n_embedded"] == 10
        assert sum(call_log) == 10

        # force_reencode=True により既存 npy が新しい値で上書きされていることを検証
        arr = np.load(out_npy)
        assert arr.shape == (n, dim)
        assert not np.allclose(arr, existing), (
            "force_reencode=True で既存 npy が上書きされていない"
        )
        # 新しい値は 0.9 ベースで L2 正規化されている
        assert np.allclose(np.linalg.norm(arr, axis=1), 1.0, atol=1e-5)

    def test_異常系_encode_texts例外発生時バッチがunresolved_jsonlに記録される(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        # encode_texts は常に RuntimeError を投げる
        def _failing_encode(
            texts: list[str],
            model: Any,
            tokenizer: Any,
            batch_size: int,
            max_length: int,
        ) -> np.ndarray:
            raise RuntimeError("MPS OOM simulated")

        monkeypatch.setattr(ei, "encode_texts", _failing_encode)

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,  # 10 chunks / 4 = 3 batches
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        # 全 batch 失敗
        assert summary["n_embedded"] == 0
        assert unresolved_path.exists()
        # 失敗 batch が記録 (3 batches: 4+4+2)
        lines = unresolved_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        for line in lines:
            rec = json.loads(line)
            assert rec["cik"] == 320193
            assert "batch_idx" in rec
            assert "MPS OOM" in rec["error"]

    def test_エッジケース_空のchunks_parquetでzeros保存_n_embedded0(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """空の chunks parquet (len==0) を渡したとき、zeros (0, 1536) が保存される."""
        ei = _load_embed_indices()
        monkeypatch.setattr(ei, "encode_texts", _make_dummy_encode(dim=1536))

        empty_chunks = pd.DataFrame(
            {
                "chunk_id": pd.Series([], dtype="int64"),
                "text": pd.Series([], dtype="str"),
            }
        )
        empty_path = tmp_path / "chunks_empty.parquet"
        empty_chunks.to_parquet(empty_path, index=False)

        out_npy = tmp_path / "embeddings_cik0000000001.npy"
        out_meta = tmp_path / "chunks_meta_cik0000000001.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        summary = ei.embed_cik(
            cik=1,
            chunks_parquet=empty_path,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        assert summary["n_chunks"] == 0
        assert summary["n_embedded"] == 0
        assert out_npy.exists()
        arr = np.load(out_npy)
        assert arr.shape == (0, 1536)

    def test_エッジケース_既存npyのshape不一致でNaN初期化にフォールバック(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """既存 .npy が想定外 shape の場合に NaN 初期化へフォールバックする."""
        ei = _load_embed_indices()
        monkeypatch.setattr(ei, "encode_texts", _make_dummy_encode(dim=1536))

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        # 期待 shape (10, 1536) と異なる (8, 512) の壊れた既存ファイル
        np.save(out_npy, np.ones((8, 512), dtype=np.float32))

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        # NaN 初期化にフォールバックして全件再生成される
        assert summary["n_embedded"] == 10
        arr = np.load(out_npy)
        assert arr.shape == (10, 1536)
        assert not np.isnan(arr).any()

    def test_エッジケース_既存npyの破損でOSErrorからNaN初期化にフォールバック(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """既存 .npy が壊れている場合 OSError/ValueError からフォールバックする."""
        ei = _load_embed_indices()
        monkeypatch.setattr(ei, "encode_texts", _make_dummy_encode(dim=1536))

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        # 0 バイトの壊れたファイル
        out_npy.write_bytes(b"")

        summary = ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        # フォールバックで NaN 初期化 → 全件エンコード
        assert summary["n_embedded"] == 10
        arr = np.load(out_npy)
        assert arr.shape == (10, 1536)
        assert not np.isnan(arr).any()

    def test_正常系_metaファイルが先に書き出される(
        self,
        tmp_path: Path,
        chunks_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()
        monkeypatch.setattr(ei, "encode_texts", _make_dummy_encode(dim=1536))

        out_npy = tmp_path / "embeddings_cik0000320193.npy"
        out_meta = tmp_path / "chunks_meta_cik0000320193.parquet"
        unresolved_path = tmp_path / "unresolved_chunks.jsonl"

        ei.embed_cik(
            cik=320193,
            chunks_parquet=chunks_parquet,
            out_npy=out_npy,
            out_meta=out_meta,
            model=object(),
            tokenizer=object(),
            batch_size=4,
            max_length=512,
            force_reencode=False,
            checkpoint_every_n_batches=1,
            unresolved_path=unresolved_path,
        )
        # meta が出力されており、chunk_id 列を持つ
        assert out_meta.exists()
        meta = pd.read_parquet(out_meta)
        assert "chunk_id" in meta.columns
        assert len(meta) == 10


# -----------------------------------------------------------------------------
# _parse_args
# -----------------------------------------------------------------------------
class TestParseArgs:
    def test_正常系_必須引数のみ指定でデフォルト値が設定される(self) -> None:
        ei = _load_embed_indices()
        args = ei._parse_args(
            [
                "--run-id",
                "indices_v1",
                "--membership",
                "/tmp/membership.parquet",
                "--index-filter",
                "in_spx",
            ]
        )
        assert args.run_id == "indices_v1"
        assert args.membership == "/tmp/membership.parquet"
        assert args.index_filter == "in_spx"
        # デフォルト値
        assert args.batch_size > 0
        assert args.max_length > 0
        assert args.device in ("mps", "cpu", "cuda")
        assert args.dtype in ("bfloat16", "float16", "float32")
        assert args.checkpoint_every_n_batches > 0
        assert args.force_reencode is False

    def test_正常系_index_filterの4種類全てを受け付ける(self) -> None:
        ei = _load_embed_indices()
        for f in ("in_spx", "in_sox", "in_riy", "in_ray"):
            args = ei._parse_args(
                [
                    "--run-id",
                    "indices_v1",
                    "--membership",
                    "/tmp/m.parquet",
                    "--index-filter",
                    f,
                ]
            )
            assert args.index_filter == f

    def test_異常系_index_filterに無効値でSystemExit(self) -> None:
        ei = _load_embed_indices()
        with pytest.raises(SystemExit):
            ei._parse_args(
                [
                    "--run-id",
                    "x",
                    "--membership",
                    "/tmp/m.parquet",
                    "--index-filter",
                    "in_invalid",
                ]
            )

    def test_正常系_オプション引数を全て指定できる(self) -> None:
        ei = _load_embed_indices()
        args = ei._parse_args(
            [
                "--run-id",
                "indices_v1",
                "--membership",
                "/tmp/m.parquet",
                "--index-filter",
                "in_spx",
                "--batch-size",
                "8",
                "--max-length",
                "256",
                "--device",
                "cpu",
                "--dtype",
                "float32",
                "--checkpoint-every-n-batches",
                "20",
                "--force-reencode",
            ]
        )
        assert args.batch_size == 8
        assert args.max_length == 256
        assert args.device == "cpu"
        assert args.dtype == "float32"
        assert args.checkpoint_every_n_batches == 20
        assert args.force_reencode is True


# -----------------------------------------------------------------------------
# _load_target_ciks
# -----------------------------------------------------------------------------
class TestLoadTargetCiks:
    def test_正常系_in_spxフィルタでSPX該当CIKが全件返る(
        self, membership_parquet: Path
    ) -> None:
        ei = _load_embed_indices()
        ciks = ei._load_target_ciks(membership_parquet, "in_spx")
        assert set(ciks) == {320193, 14693, 1067983, 789019}

    def test_正常系_in_soxフィルタでSOX該当CIKのみ返る(
        self, membership_parquet: Path
    ) -> None:
        ei = _load_embed_indices()
        ciks = ei._load_target_ciks(membership_parquet, "in_sox")
        assert ciks == [789019]

    def test_異常系_未知のindex_filterでValueError(
        self, membership_parquet: Path
    ) -> None:
        ei = _load_embed_indices()
        with pytest.raises(ValueError, match="index_filter"):
            ei._load_target_ciks(membership_parquet, "in_unknown")


# -----------------------------------------------------------------------------
# main (smoke test with mocked model load & embed_cik)
# -----------------------------------------------------------------------------
class TestMain:
    def test_正常系_CIK単位resumeで既完了CIKはskipされる(
        self,
        tmp_path: Path,
        membership_parquet: Path,
        chunks_df: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ei = _load_embed_indices()

        # NAS / 出力先 を tmp_path に差し替え
        nas_root = tmp_path / "nas"
        nas_root.mkdir(parents=True)
        chunks_dir = nas_root / "chunks" / "indices_v1"
        chunks_dir.mkdir(parents=True)
        embeddings_dir = nas_root / "embeddings"
        checkpoints_dir = nas_root / "checkpoints"
        logs_dir = nas_root / "logs"

        # 4 CIK 分の chunks parquet を配置 (SPX 該当のみ)
        for cik in (320193, 14693, 1067983, 789019):
            df = chunks_df.copy()
            df["cik"] = cik
            df.to_parquet(chunks_dir / f"chunks_cik{cik:010d}.parquet", index=False)

        monkeypatch.setattr(ei.config, "NAS_ROOT", nas_root)
        monkeypatch.setattr(ei.config, "CHUNKS_DIR", nas_root / "chunks")
        monkeypatch.setattr(ei.config, "EMBEDDINGS_DIR", embeddings_dir)
        monkeypatch.setattr(ei.config, "CHECKPOINTS_DIR", checkpoints_dir)
        monkeypatch.setattr(ei.config, "LOGS_DIR", logs_dir)
        monkeypatch.setattr(
            ei.config,
            "INDICES_V1_EMBED_PROGRESS_PATH",
            checkpoints_dir / "indices_v1_embed_progress.json",
        )

        # モデルロードをスタブ化
        monkeypatch.setattr(ei, "_load_model", lambda *a, **k: (object(), object()))

        # embed_cik をスタブ化して呼ばれた CIK を記録
        called_ciks: list[int] = []

        def _spy_embed(
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
        ) -> dict:
            called_ciks.append(cik)
            # 空の embedding を作って書き出す (resume チェックパス用)
            out_npy.parent.mkdir(parents=True, exist_ok=True)
            np.save(out_npy, np.zeros((1, 1536), dtype=np.float32))
            return {"n_chunks": 1, "n_embedded": 1, "elapsed_sec": 0.0}

        monkeypatch.setattr(ei, "embed_cik", _spy_embed)

        # 事前に CHECKPOINTS_DIR を作って 1 CIK 完了済みのマーカーを置く
        checkpoints_dir.mkdir(parents=True)
        progress_path = checkpoints_dir / "indices_v1_embed_progress.json"
        progress_path.write_text(
            json.dumps(
                {
                    "run_id": "test",
                    "started_at": "2026-05-25T00:00:00",
                    "completed": {
                        "320193": {
                            "finished_at": "2026-05-25T00:00:00",
                            "n_chunks": 1,
                            "n_embedded": 1,
                        }
                    },
                }
            )
        )

        ei.main(
            [
                "--run-id",
                "indices_v1",
                "--membership",
                str(membership_parquet),
                "--index-filter",
                "in_spx",
                "--batch-size",
                "4",
                "--max-length",
                "128",
                "--device",
                "cpu",
                "--dtype",
                "float32",
            ]
        )

        # 完了済み CIK (320193) はスキップ、残り 3 CIK が呼ばれる
        assert 320193 not in called_ciks
        assert set(called_ciks) == {14693, 1067983, 789019}

        # summary.json が出力されている
        summary_path = logs_dir / "indices_v1_embed_summary.json"
        assert summary_path.exists()
