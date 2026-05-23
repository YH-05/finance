"""REGIME_SWITCHING/_helpers.py の単体テスト."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pandas as pd


def _load_helpers():
    """notebook/REGIME_SWITCHING/_helpers.py をモジュールとしてロード."""
    here = Path(__file__).resolve()
    repo_root = (
        here.parent.parent.parent.parent
    )  # tests/notebook/regime_switching/ → repo
    helpers_path = repo_root / "notebook" / "REGIME_SWITCHING" / "_helpers.py"
    spec = importlib.util.spec_from_file_location("regime_helpers", helpers_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestModuleConstants:
    def test_PKG_DIR_は_REGIME_SWITCHING_ディレクトリを指す(self) -> None:
        helpers = _load_helpers()
        assert helpers.PKG_DIR.name == "REGIME_SWITCHING"
        assert helpers.PKG_DIR.is_dir()

    def test_DATA_DIR_は_PKG_DIR_配下の_data(self) -> None:
        helpers = _load_helpers()
        assert helpers.DATA_DIR == helpers.PKG_DIR / "data"

    def test_FRED_SERIES_IDS_は7系列を含む(self) -> None:
        helpers = _load_helpers()
        expected = {
            "INDPRO",
            "ICSA",
            "T10YIE",
            "CPIAUCSL",
            "STLFSI4",
            "BAA10Y",
            "T10Y2Y",
        }
        assert set(helpers.FRED_SERIES_IDS) == expected


class TestLoadFredWeekly:
    def test_全7系列を結合してW_FRI週次DataFrameを返す(self) -> None:
        helpers = _load_helpers()

        def fake_get_series_df(self, series_id: str) -> pd.DataFrame:
            # 2024年1月の数日分の架空データ
            return pd.DataFrame(
                {"value": [1.0, 2.0, 3.0]},
                index=pd.to_datetime(["2024-01-05", "2024-01-12", "2024-01-19"]),
            )

        with (
            patch(
                "market.fred.HistoricalCache.sync_series",
                return_value={"success": True},
            ),
            patch("market.fred.HistoricalCache.get_series_df", fake_get_series_df),
        ):
            df = helpers.load_fred_weekly(start="2024-01-01")

        # 列がFRED_SERIES_IDSの全てを含む
        assert set(df.columns) == set(helpers.FRED_SERIES_IDS)
        # インデックスはDatetimeIndex
        assert isinstance(df.index, pd.DatetimeIndex)
        # 全インデックスが金曜日（W-FRI）
        assert all(d.dayofweek == 4 for d in df.index)

    def test_start引数より前のデータは除外される(self) -> None:
        helpers = _load_helpers()

        def fake_get_series_df(self, series_id: str) -> pd.DataFrame:
            return pd.DataFrame(
                {"value": [1.0, 2.0, 3.0, 4.0]},
                index=pd.to_datetime(
                    ["2023-12-01", "2024-01-05", "2024-01-12", "2024-01-19"]
                ),
            )

        with (
            patch(
                "market.fred.HistoricalCache.sync_series",
                return_value={"success": True},
            ),
            patch("market.fred.HistoricalCache.get_series_df", fake_get_series_df),
        ):
            df = helpers.load_fred_weekly(start="2024-01-01")

        assert df.index.min() >= pd.Timestamp("2024-01-01")
