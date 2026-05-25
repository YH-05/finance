"""notebook/FILING_NLP/pipeline/run_indices.py の単体テスト.

CLI 引数解析、universe + membership ロード + index_filter 絞り込み、
NAS マウント未検出時の fail-fast の振る舞いを検証する.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
import pytest

if TYPE_CHECKING:
    from types import ModuleType


def _load_run_indices() -> ModuleType:
    """notebook/FILING_NLP/pipeline/run_indices.py をモジュールとしてロード."""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent  # tests/notebook/FILING_NLP/ → repo
    module_path = repo_root / "notebook" / "FILING_NLP" / "pipeline" / "run_indices.py"
    pkg_root = str(repo_root)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    spec = importlib.util.spec_from_file_location("_ri_test_module", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -----------------------------------------------------------------------------
# Fixtures: universe + membership parquet を tmp_path に書き出す
# -----------------------------------------------------------------------------
@pytest.fixture
def universe_df() -> pd.DataFrame:
    """4 銘柄分の universe_indices_v1 形式 DataFrame."""
    return pd.DataFrame(
        {
            "cik": [320193, 14693, 1067983, 789019],
            "ticker": ["AAPL", "BF-B", "BRK-B", "MSFT"],
            "isin": ["US0378331005", "US1156372096", "US0846707026", "US5949181045"],
            "sedol": ["2046251", "2236820", "2073390", "2588173"],
            "mkt_cap": [4.5e12, 1.0e11, 8.0e11, 3.0e12],
            "gics_sector": [
                "Information Technology",
                "Consumer Staples",
                "Financials",
                "Information Technology",
            ],
            "gics_industry_group": ["A", "B", "C", "A"],
            "gics_industry": ["A1", "B1", "C1", "A1"],
            "gics_sub_industry": ["A1a", "B1a", "C1a", "A1a"],
            "index_name": ["SPX", "SPX", "SPX", "SPX"],
        }
    )


@pytest.fixture
def membership_df() -> pd.DataFrame:
    """4 銘柄分の membership_indices_v1 形式 DataFrame.

    - AAPL: SPX のみ
    - BF-B: SPX + RIY
    - BRK-B: SPX + RAY
    - MSFT: SPX + SOX + RIY + RAY (全 index 該当)
    """
    return pd.DataFrame(
        {
            "cik": [320193, 14693, 1067983, 789019],
            "in_spx": [True, True, True, True],
            "in_sox": [False, False, False, True],
            "in_riy": [False, True, False, True],
            "in_ray": [False, False, True, True],
            "snapshot_date": [
                "2026-05-22",
                "2026-05-22",
                "2026-05-22",
                "2026-05-22",
            ],
        }
    )


@pytest.fixture
def universe_parquet(tmp_path: Path, universe_df: pd.DataFrame) -> Path:
    p = tmp_path / "universe_indices_v1.parquet"
    universe_df.to_parquet(p, index=False)
    return p


@pytest.fixture
def membership_parquet(tmp_path: Path, membership_df: pd.DataFrame) -> Path:
    p = tmp_path / "membership_indices_v1.parquet"
    membership_df.to_parquet(p, index=False)
    return p


# -----------------------------------------------------------------------------
# _load_universe
# -----------------------------------------------------------------------------
class TestLoadUniverse:
    def test_正常系_in_spxフィルタでSPX該当銘柄が全件返る(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        ri = _load_run_indices()
        df = ri._load_universe(universe_parquet, membership_parquet, "in_spx")
        # SPX には 4 銘柄全てが該当
        assert len(df) == 4
        assert set(df["cik"].tolist()) == {320193, 14693, 1067983, 789019}

    def test_正常系_in_soxフィルタでSOX該当銘柄のみ返る(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        ri = _load_run_indices()
        df = ri._load_universe(universe_parquet, membership_parquet, "in_sox")
        # SOX には MSFT のみ
        assert len(df) == 1
        assert int(df.iloc[0]["cik"]) == 789019
        assert df.iloc[0]["ticker"] == "MSFT"

    def test_正常系_in_riyフィルタでRIY該当銘柄のみ返る(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        ri = _load_run_indices()
        df = ri._load_universe(universe_parquet, membership_parquet, "in_riy")
        # RIY には BF-B, MSFT
        assert len(df) == 2
        assert set(df["cik"].tolist()) == {14693, 789019}

    def test_正常系_in_rayフィルタでRAY該当銘柄のみ返る(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        ri = _load_run_indices()
        df = ri._load_universe(universe_parquet, membership_parquet, "in_ray")
        # RAY には BRK-B, MSFT
        assert len(df) == 2
        assert set(df["cik"].tolist()) == {1067983, 789019}

    def test_正常系_runner互換のcik_ticker列を持つ(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        """runner.run_pipeline は cik / ticker カラムを期待する."""
        ri = _load_run_indices()
        df = ri._load_universe(universe_parquet, membership_parquet, "in_spx")
        assert "cik" in df.columns
        assert "ticker" in df.columns

    def test_異常系_未知のindex_filterでValueError(
        self, universe_parquet: Path, membership_parquet: Path
    ) -> None:
        ri = _load_run_indices()
        with pytest.raises(ValueError, match="index_filter"):
            ri._load_universe(universe_parquet, membership_parquet, "in_unknown")

    def test_異常系_membership列が存在しない時にValueError(
        self,
        universe_parquet: Path,
        tmp_path: Path,
    ) -> None:
        """membership parquet に in_spx 列がない場合 utils.validate_index_filter が raise."""
        ri = _load_run_indices()
        broken_membership_path = tmp_path / "membership_broken.parquet"
        # in_spx 列を持たない壊れた membership
        broken_df = pd.DataFrame({"cik": [320193, 14693], "other_col": [True, False]})
        broken_df.to_parquet(broken_membership_path, index=False)
        with pytest.raises(ValueError, match="not found in membership columns"):
            ri._load_universe(universe_parquet, broken_membership_path, "in_spx")


# -----------------------------------------------------------------------------
# _setup_edgar_identity
# -----------------------------------------------------------------------------
class TestSetupEdgarIdentity:
    def test_異常系_EDGAR_IDENTITY未設定でRuntimeError(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """EDGAR_IDENTITY 環境変数が未設定の場合に RuntimeError が raise される."""
        ri = _load_run_indices()
        monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
        with pytest.raises(RuntimeError, match="EDGAR_IDENTITY"):
            ri._setup_edgar_identity()


# -----------------------------------------------------------------------------
# _parse_args
# -----------------------------------------------------------------------------
class TestParseArgs:
    def test_正常系_必須引数のみ指定でデフォルト値が設定される(self) -> None:
        ri = _load_run_indices()
        args = ri._parse_args(
            [
                "--run-id",
                "indices_v1",
                "--universe",
                "/tmp/universe.parquet",
                "--membership",
                "/tmp/membership.parquet",
                "--index-filter",
                "in_spx",
            ]
        )
        ri_mod = _load_run_indices()
        assert args.run_id == "indices_v1"
        assert args.universe == "/tmp/universe.parquet"
        assert args.membership == "/tmp/membership.parquet"
        assert args.index_filter == "in_spx"
        # デフォルト値は config の値と一致すること (範囲チェックではなく具体値で検証)
        assert args.workers == ri_mod.config.DEFAULT_MAX_WORKERS
        assert args.rate_rps == ri_mod.config.RATE_LIMIT_RPS
        assert args.rate_burst == ri_mod.config.RATE_LIMIT_BURST
        assert args.flush_every == 5

    @pytest.mark.parametrize("filter_value", ["in_spx", "in_sox", "in_riy", "in_ray"])
    def test_正常系_index_filterの4種類全てを受け付ける(
        self, filter_value: str
    ) -> None:
        ri = _load_run_indices()
        args = ri._parse_args(
            [
                "--run-id",
                "indices_v1",
                "--universe",
                "/tmp/u.parquet",
                "--membership",
                "/tmp/m.parquet",
                "--index-filter",
                filter_value,
            ]
        )
        assert args.index_filter == filter_value

    def test_異常系_index_filterに無効値でSystemExit(self) -> None:
        ri = _load_run_indices()
        with pytest.raises(SystemExit) as exc_info:
            ri._parse_args(
                [
                    "--run-id",
                    "x",
                    "--universe",
                    "/tmp/u.parquet",
                    "--membership",
                    "/tmp/m.parquet",
                    "--index-filter",
                    "in_invalid",
                ]
            )
        # argparse のエラー終了は exit code 2
        assert exc_info.value.code == 2

    def test_正常系_オプション引数を全て指定できる(self) -> None:
        ri = _load_run_indices()
        args = ri._parse_args(
            [
                "--run-id",
                "indices_v1",
                "--universe",
                "/tmp/u.parquet",
                "--membership",
                "/tmp/m.parquet",
                "--index-filter",
                "in_spx",
                "--workers",
                "16",
                "--rate-rps",
                "8.0",
                "--rate-burst",
                "20",
                "--flush-every",
                "5",
            ]
        )
        assert args.workers == 16
        assert args.rate_rps == 8.0
        assert args.rate_burst == 20
        assert args.flush_every == 5


# -----------------------------------------------------------------------------
# main (smoke test with mocked runner)
# -----------------------------------------------------------------------------
class TestMain:
    def test_異常系_NAS未マウント時にSystemExitでfail_fastする(
        self,
        universe_parquet: Path,
        membership_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        ri = _load_run_indices()
        # NAS 検証関数を fail させる
        # config.NAS_ROOT を存在しないパスに差し替え
        monkeypatch.setattr(ri.config, "NAS_ROOT", tmp_path / "nonexistent_nas")
        with pytest.raises(SystemExit) as exc_info:
            ri.main(
                [
                    "--run-id",
                    "indices_v1",
                    "--universe",
                    str(universe_parquet),
                    "--membership",
                    str(membership_parquet),
                    "--index-filter",
                    "in_spx",
                ]
            )
        assert exc_info.value.code == 2

    def test_正常系_runner_run_pipelineが期待引数で呼ばれる(
        self,
        universe_parquet: Path,
        membership_parquet: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        ri = _load_run_indices()

        # NAS をテスト用 tmp_path に差し替えて exists() を成功させる
        nas_root = tmp_path / "nas"
        nas_root.mkdir(parents=True)
        monkeypatch.setattr(ri.config, "NAS_ROOT", nas_root)
        monkeypatch.setattr(ri.config, "SECTIONS_DIR", nas_root / "sections")
        monkeypatch.setattr(ri.config, "CHUNKS_DIR", nas_root / "chunks")
        monkeypatch.setattr(
            ri.config, "FILINGS_METADATA_DIR", nas_root / "filings_metadata"
        )
        monkeypatch.setattr(ri.config, "CHECKPOINTS_DIR", nas_root / "checkpoints")
        monkeypatch.setattr(ri.config, "LOGS_DIR", nas_root / "logs")
        monkeypatch.setattr(
            ri.config,
            "INDICES_V1_PROGRESS_PATH",
            nas_root / "checkpoints" / "indices_v1_progress.json",
        )

        # tokenizer ロード / EDGAR identity 設定をスタブ化
        monkeypatch.setattr(ri, "_load_tokenizer", lambda: object())
        monkeypatch.setattr(ri, "_setup_edgar_identity", lambda: None)

        # runner.run_pipeline をスタブ化
        called: dict[str, Any] = {}

        def fake_run_pipeline(**kwargs: Any) -> dict[str, Any]:
            called.update(kwargs)
            return {
                "n_processed": len(kwargs["universe"]),
                "n_failed": 0,
                "n_filings": 0,
                "n_sections": 0,
                "n_chunks": 0,
                "elapsed_sec": 0.0,
            }

        monkeypatch.setattr(ri.runner, "run_pipeline", fake_run_pipeline)

        ri.main(
            [
                "--run-id",
                "indices_v1",
                "--universe",
                str(universe_parquet),
                "--membership",
                str(membership_parquet),
                "--index-filter",
                "in_sox",
                "--workers",
                "4",
                "--rate-rps",
                "6.0",
                "--rate-burst",
                "12",
                "--flush-every",
                "3",
            ]
        )

        # universe は in_sox 該当の MSFT 1 件のみ
        assert "universe" in called
        assert len(called["universe"]) == 1
        assert int(called["universe"].iloc[0]["cik"]) == 789019
        # CLI 引数が runner に伝搬している
        assert called["max_workers"] == 4
        assert called["rate_rps"] == 6.0
        assert called["rate_burst"] == 12
        assert called["flush_every"] == 3
        # 出力パスが indices_v1 用に構築されている
        assert called["sections_dir"] == nas_root / "sections" / "indices_v1"
        assert called["chunks_dir"] == nas_root / "chunks" / "indices_v1"
        assert (
            called["checkpoint_path"]
            == nas_root / "checkpoints" / "indices_v1_progress.json"
        )

        # summary.json が書き出されている
        summary_path = nas_root / "logs" / "indices_v1_summary.json"
        assert summary_path.exists()
