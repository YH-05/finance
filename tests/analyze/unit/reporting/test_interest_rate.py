"""InterestRateAnalyzer のテスト.

TDDに基づいてテストを先に作成し、実装を後から行う。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas import DataFrame

from analyze.reporting.interest_rate import InterestRateAnalyzer


class TestInterestRateAnalyzerInit:
    """InterestRateAnalyzer の初期化テスト."""

    def test_正常系_デフォルト初期化が成功する(self) -> None:
        """InterestRateAnalyzerがデフォルト設定で初期化できることを確認."""
        analyzer = InterestRateAnalyzer()

        assert analyzer is not None

    def test_正常系_対象シリーズが正しく設定される(self) -> None:
        """対象の5シリーズが正しく設定されることを確認."""
        analyzer = InterestRateAnalyzer()

        expected_series = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        assert analyzer.target_series == expected_series


class TestFetchData:
    """データ取得のテスト."""

    @pytest.fixture
    def mock_fred_results(self) -> list[MagicMock]:
        """FREDFetcher.fetch の戻り値をモック."""
        results = []
        series_data = {
            "DGS2": [4.5, 4.6, 4.7],
            "DGS10": [4.0, 4.1, 4.2],
            "DGS30": [4.2, 4.3, 4.4],
            "FEDFUNDS": [5.25, 5.25, 5.25],
            "T10Y2Y": [-0.5, -0.4, -0.3],
        }
        dates = pd.date_range("2026-01-25", periods=3, freq="D")

        for series_id, values in series_data.items():
            mock_result = MagicMock()
            mock_result.symbol = series_id
            mock_result.data = DataFrame({"value": values}, index=dates)
            mock_result.is_empty = False
            results.append(mock_result)

        return results

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_正常系_5シリーズのデータを取得できる(
        self,
        mock_fetcher_class: MagicMock,
        mock_fred_results: list[MagicMock],
    ) -> None:
        """FREDFetcher を使用して5シリーズのデータを取得できることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_fred_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()
        data = analyzer.fetch_data()

        assert "DGS2" in data
        assert "DGS10" in data
        assert "DGS30" in data
        assert "FEDFUNDS" in data
        assert "T10Y2Y" in data
        assert len(data) == 5

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_正常系_各シリーズがDataFrameとして返される(
        self,
        mock_fetcher_class: MagicMock,
        mock_fred_results: list[MagicMock],
    ) -> None:
        """各シリーズのデータがDataFrameとして返されることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_fred_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()
        data = analyzer.fetch_data()

        for _series_id, df in data.items():
            assert isinstance(df, DataFrame)
            assert "value" in df.columns


class TestCalculateChanges:
    """変化量計算のテスト."""

    @pytest.fixture
    def sample_rate_data(self) -> dict[str, DataFrame]:
        """テスト用の金利データ."""
        # 30日分のデータを生成
        dates = pd.date_range("2025-12-27", periods=30, freq="D")
        return {
            "DGS10": DataFrame(
                {"value": [4.0 + i * 0.01 for i in range(30)]},
                index=dates,
            ),
            "DGS2": DataFrame(
                {"value": [4.5 + i * 0.005 for i in range(30)]},
                index=dates,
            ),
        }

    def test_正常系_1日変化量が正しく計算される(
        self,
        sample_rate_data: dict[str, DataFrame],
    ) -> None:
        """1日の変化量（差分）が正しく計算されることを確認."""
        analyzer = InterestRateAnalyzer()

        changes = analyzer.calculate_changes(sample_rate_data, periods=["1D"])

        # DGS10: 最新値 - 1日前 = (4.0 + 0.29) - (4.0 + 0.28) = 0.01
        assert "DGS10" in changes
        assert "1D" in changes["DGS10"]
        change_1d = changes["DGS10"]["1D"]
        assert change_1d is not None
        assert abs(change_1d - 0.01) < 0.001

    def test_正常系_1週間変化量が正しく計算される(
        self,
        sample_rate_data: dict[str, DataFrame],
    ) -> None:
        """1週間の変化量が正しく計算されることを確認."""
        analyzer = InterestRateAnalyzer()

        changes = analyzer.calculate_changes(sample_rate_data, periods=["1W"])

        # DGS10: 1W = 5営業日分の変化量
        # 最新値(index 29) - 5日前(index 23) = (4.0 + 0.29) - (4.0 + 0.24) = 0.05
        assert "DGS10" in changes
        assert "1W" in changes["DGS10"]
        change_1w = changes["DGS10"]["1W"]
        assert change_1w is not None
        assert abs(change_1w - 0.05) < 0.001

    def test_正常系_1ヶ月変化量が正しく計算される(
        self,
        sample_rate_data: dict[str, DataFrame],
    ) -> None:
        """1ヶ月の変化量が正しく計算されることを確認."""
        analyzer = InterestRateAnalyzer()

        changes = analyzer.calculate_changes(sample_rate_data, periods=["1M"])

        # DGS10: 最新値 - 約30日前
        assert "DGS10" in changes
        assert "1M" in changes["DGS10"]

    def test_正常系_複数期間を一度に計算できる(
        self,
        sample_rate_data: dict[str, DataFrame],
    ) -> None:
        """複数期間の変化量を一度に計算できることを確認."""
        analyzer = InterestRateAnalyzer()

        changes = analyzer.calculate_changes(
            sample_rate_data, periods=["1D", "1W", "1M"]
        )

        assert "DGS10" in changes
        assert all(p in changes["DGS10"] for p in ["1D", "1W", "1M"])

    def test_エッジケース_データ不足時はNoneが返される(self) -> None:
        """データ不足時にNoneが返されることを確認."""
        analyzer = InterestRateAnalyzer()
        short_data = {
            "DGS10": DataFrame(
                {"value": [4.0, 4.1]},
                index=pd.date_range("2026-01-25", periods=2, freq="D"),
            )
        }

        changes = analyzer.calculate_changes(short_data, periods=["1M"])

        assert changes["DGS10"]["1M"] is None


class TestYieldCurveAnalysis:
    """イールドカーブ分析のテスト."""

    @pytest.fixture
    def inverted_curve_data(self) -> dict[str, DataFrame]:
        """逆イールドのテストデータ."""
        dates = pd.date_range("2026-01-25", periods=1, freq="D")
        return {
            "DGS2": DataFrame({"value": [4.5]}, index=dates),  # 短期金利が高い
            "DGS10": DataFrame({"value": [4.0]}, index=dates),  # 長期金利が低い
            "T10Y2Y": DataFrame({"value": [-0.5]}, index=dates),  # スプレッドがマイナス
        }

    @pytest.fixture
    def normal_curve_data(self) -> dict[str, DataFrame]:
        """正常なイールドカーブのテストデータ."""
        dates = pd.date_range("2026-01-25", periods=1, freq="D")
        return {
            "DGS2": DataFrame({"value": [3.5]}, index=dates),  # 短期金利が低い
            "DGS10": DataFrame({"value": [4.5]}, index=dates),  # 長期金利が高い
            "T10Y2Y": DataFrame({"value": [1.0]}, index=dates),  # スプレッドがプラス
        }

    def test_正常系_逆イールドを検出できる(
        self,
        inverted_curve_data: dict[str, DataFrame],
    ) -> None:
        """逆イールド（10年-2年スプレッドがマイナス）を検出できることを確認."""
        analyzer = InterestRateAnalyzer()

        result = analyzer.analyze_yield_curve(inverted_curve_data)

        assert result["is_inverted"] is True
        assert result["spread_10y_2y"] == -0.5

    def test_正常系_正常なイールドカーブを判定できる(
        self,
        normal_curve_data: dict[str, DataFrame],
    ) -> None:
        """正常なイールドカーブを判定できることを確認."""
        analyzer = InterestRateAnalyzer()

        result = analyzer.analyze_yield_curve(normal_curve_data)

        assert result["is_inverted"] is False
        assert result["spread_10y_2y"] == 1.0

    def test_正常系_イールドカーブの傾斜判定ができる(
        self,
        normal_curve_data: dict[str, DataFrame],
    ) -> None:
        """イールドカーブの傾斜（スティープ/フラット）判定ができることを確認."""
        analyzer = InterestRateAnalyzer()

        result = analyzer.analyze_yield_curve(normal_curve_data)

        # スプレッドが1.0%は通常「スティープ」
        assert "slope_status" in result
        assert result["slope_status"] in ["steep", "normal", "flat", "inverted"]


class TestGetSummary:
    """サマリー取得のテスト."""

    @pytest.fixture
    def sample_full_data(self) -> dict[str, DataFrame]:
        """テスト用の完全なデータセット."""
        dates = pd.date_range("2025-12-27", periods=30, freq="D")
        return {
            "DGS2": DataFrame(
                {"value": [4.5 + i * 0.01 for i in range(30)]}, index=dates
            ),
            "DGS10": DataFrame(
                {"value": [4.0 + i * 0.01 for i in range(30)]}, index=dates
            ),
            "DGS30": DataFrame(
                {"value": [4.2 + i * 0.01 for i in range(30)]}, index=dates
            ),
            "FEDFUNDS": DataFrame({"value": [5.25] * 30}, index=dates),
            "T10Y2Y": DataFrame(
                {"value": [-0.5 + i * 0.01 for i in range(30)]}, index=dates
            ),
        }

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_正常系_サマリーに全情報が含まれる(
        self,
        mock_fetcher_class: MagicMock,
        sample_full_data: dict[str, DataFrame],
    ) -> None:
        """サマリーに全ての必要な情報が含まれることを確認."""
        # FREDFetcherをモック
        mock_results = []
        for series_id, df in sample_full_data.items():
            mock_result = MagicMock()
            mock_result.symbol = series_id
            mock_result.data = df
            mock_result.is_empty = False
            mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()
        summary = analyzer.get_summary()

        # 全シリーズの最新値
        assert "latest_values" in summary
        assert all(
            s in summary["latest_values"]
            for s in ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        )

        # 期間別変化量
        assert "changes" in summary
        assert all(p in summary["changes"]["DGS10"] for p in ["1D", "1W", "1M"])

        # イールドカーブ分析
        assert "yield_curve" in summary
        assert "is_inverted" in summary["yield_curve"]

        # データ取得日時
        assert "generated_at" in summary


class TestAPIErrorHandling:
    """APIエラー時の挙動テスト."""

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_異常系_APIエラー時にFREDFetchErrorがスローされる(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """API エラー発生時に FREDFetchError がスローされることを確認."""
        from market.errors import FREDFetchError

        # モックの設定: fetchが例外をスロー
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = FREDFetchError("API rate limit exceeded")
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()

        with pytest.raises(FREDFetchError, match="API rate limit exceeded"):
            analyzer.fetch_data()

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_異常系_ネットワークエラー時にFREDFetchErrorがスローされる(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """ネットワークエラー発生時に FREDFetchError がスローされることを確認."""
        from market.errors import FREDFetchError

        # モックの設定: ネットワークエラーをシミュレート
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = FREDFetchError(
            "Connection timeout while fetching DGS10"
        )
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()

        with pytest.raises(FREDFetchError, match="Connection timeout"):
            analyzer.fetch_data()

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_異常系_一部シリーズの取得失敗時は空データとして処理される(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """一部シリーズの取得失敗時、そのシリーズは空データとして処理されることを確認."""
        # モックの設定: 一部のシリーズが空データを返す
        dates = pd.date_range("2026-01-25", periods=3, freq="D")

        def create_mock_result(series_id: str, is_empty: bool = False) -> MagicMock:
            mock_result = MagicMock()
            mock_result.symbol = series_id
            if is_empty:
                mock_result.data = DataFrame()
                mock_result.is_empty = True
            else:
                mock_result.data = DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
                mock_result.is_empty = False
            return mock_result

        mock_results = [
            create_mock_result("DGS2"),
            create_mock_result("DGS10"),
            create_mock_result("DGS30", is_empty=True),  # このシリーズは取得失敗
            create_mock_result("FEDFUNDS"),
            create_mock_result("T10Y2Y"),
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()
        data = analyzer.fetch_data()

        # 空でないシリーズは4つ（DGS30は空）
        assert len(data) == 4
        assert "DGS30" not in data


class TestEdgeCases:
    """エッジケースのテスト."""

    def test_エッジケース_空のデータで空の結果が返される(self) -> None:
        """空のデータで空の結果が返されることを確認."""
        analyzer = InterestRateAnalyzer()
        empty_data: dict[str, DataFrame] = {}

        changes = analyzer.calculate_changes(empty_data, periods=["1D"])

        assert changes == {}

    def test_エッジケース_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータが適切に処理されることを確認."""
        analyzer = InterestRateAnalyzer()
        dates = pd.date_range("2026-01-20", periods=10, freq="D")
        data_with_nan = {
            "DGS10": DataFrame(
                {
                    "value": [
                        4.0,
                        float("nan"),
                        4.2,
                        4.3,
                        4.4,
                        4.5,
                        float("nan"),
                        4.7,
                        4.8,
                        4.9,
                    ]
                },
                index=dates,
            )
        }

        changes = analyzer.calculate_changes(data_with_nan, periods=["1D"])

        # NaNを含んでいても最新の有効な値から計算される
        assert "DGS10" in changes
        # 結果がNoneでないことを確認（最新値と前日の有効値から計算）
        assert changes["DGS10"]["1D"] is not None


class TestLogging:
    """ロギングのテスト."""

    @patch("analyze.reporting.interest_rate.FREDFetcher")
    def test_正常系_ロギングが実装されている(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """適切なロギングが実装されていることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = InterestRateAnalyzer()

        # loggerが存在することを確認
        assert hasattr(analyzer, "logger")
