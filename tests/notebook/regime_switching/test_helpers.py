"""REGIME_SWITCHING/_helpers.py の単体テスト."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import numpy as np
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


class TestTransformFeatures:
    def _make_input(self) -> pd.DataFrame:
        """週次52週分の架空7系列データを返す."""
        n = 200  # YoY計算に十分な52週超
        idx = pd.date_range("2020-01-03", periods=n, freq="W-FRI")
        rng = np.random.default_rng(0)
        data = {
            "INDPRO": 100 + np.cumsum(rng.normal(0, 0.5, n)),
            "ICSA": 200_000 + np.cumsum(rng.normal(0, 1000, n)),
            "T10YIE": 2.0 + rng.normal(0, 0.1, n),
            "CPIAUCSL": 260 + np.cumsum(rng.normal(0.05, 0.2, n)),
            "STLFSI4": rng.normal(0, 0.5, n),
            "BAA10Y": 2.0 + rng.normal(0, 0.2, n),
            "T10Y2Y": 1.0 + rng.normal(0, 0.3, n),
        }
        return pd.DataFrame(data, index=idx)

    def test_出力は7列のDataFrameで標準化されている(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        assert set(df_out.columns) == set(helpers.FRED_SERIES_IDS)
        # 各列の平均はおよそ0、標準偏差はおよそ1
        for col in df_out.columns:
            assert abs(df_out[col].mean()) < 1e-6
            assert abs(df_out[col].std(ddof=0) - 1.0) < 1e-6

    def test_INDPRO_と_CPIAUCSL_はYoY変換後に標準化(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        # YoY計算で最初の52週はNaN→drop。ICSA は 4 週移動平均が先頭 3 週欠損
        # するためさらに +3 週分が落ち、合計 55 週が削除される。
        assert len(df_out) == len(df_in) - 55

    def test_ICSAは4週移動平均のYoY(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        # 出力にICSAが含まれ、ICSAの値は標準化されているはず
        assert "ICSA" in df_out.columns
        assert df_out["ICSA"].isna().sum() == 0

    def test_ICSAは4週MAステップが実装されていることを確認(self) -> None:
        """ICSA に明示的なステップ変化を入れ、4 週 MA がそれを平滑化することを検出する.

        raw ICSA YoY と 4-week MA ICSA YoY は線形でない入力で値が異なる.
        定数→ステップ→定数 の入力を作り、ICSA 出力が滑らかに遷移することを確認する.
        """
        helpers = _load_helpers()
        n = 200
        idx = pd.date_range("2020-01-03", periods=n, freq="W-FRI")
        rng = np.random.default_rng(0)
        data = {
            "INDPRO": 100 + np.cumsum(rng.normal(0, 0.5, n)),
            "ICSA": np.concatenate([np.full(100, 200_000.0), np.full(100, 400_000.0)]),
            "T10YIE": 2.0 + rng.normal(0, 0.1, n),
            "CPIAUCSL": 260 + np.cumsum(rng.normal(0.05, 0.2, n)),
            "STLFSI4": rng.normal(0, 0.5, n),
            "BAA10Y": 2.0 + rng.normal(0, 0.2, n),
            "T10Y2Y": 1.0 + rng.normal(0, 0.3, n),
        }
        df_in = pd.DataFrame(data, index=idx)
        df_out = helpers.transform_features(df_in)

        # ステップ直後の数週間で raw YoY なら +100% の急変だが、4-week MA を挟むと先に
        # MA が遷移していくため、YoY 値が滑らかに上昇する。Z-score 後でもこの滑らかさが残る。
        # 具体的に: ICSA YoY が単調増加する区間 (MA 遷移期 4 週) が存在することを確認する。
        icsa = df_out["ICSA"]
        # 連続する 3 週で単調増加している区間が少なくとも 1 か所存在
        diffs = icsa.diff()
        monotonic_segments = (diffs > 0).rolling(3).sum()
        assert (monotonic_segments >= 3).any(), (
            "4-week MA による滑らかな遷移が検出されなかった"
        )


class TestFetchSP500WeeklyReturns:
    def test_週次対数リターンSeriesを返す(self) -> None:
        helpers = _load_helpers()

        # 100日分の架空日次データ
        idx = pd.date_range("2024-01-01", periods=100, freq="B")
        fake_daily = pd.DataFrame(
            {"close": 4000 + np.cumsum(np.random.default_rng(0).normal(0, 5, 100))},
            index=idx,
        )

        from datetime import datetime

        from market.yfinance.types import DataSource, MarketDataResult

        fake_result = MarketDataResult(
            data=fake_daily,
            source=DataSource.YFINANCE,
            symbol="^GSPC",
            fetched_at=datetime.now(),
            from_cache=False,
        )

        with patch(
            "market.yfinance.fetcher.YFinanceFetcher.fetch",
            return_value=[fake_result],
        ):
            ret = helpers.fetch_sp500_weekly_returns(start="2024-01-01")

        assert isinstance(ret, pd.Series)
        assert ret.name == "sp500_logret"
        # インデックスは金曜
        assert all(d.dayofweek == 4 for d in ret.index)
        # 最初の値はNaN除去済み
        assert not ret.isna().any()
