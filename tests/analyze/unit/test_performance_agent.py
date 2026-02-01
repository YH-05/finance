"""PerformanceAnalyzer4Agent のテスト."""

import pandas as pd
import pytest
from pandas import DataFrame

from analyze.reporting.performance_agent import (
    PerformanceAnalyzer4Agent,
    PerformanceResult,
)


class TestPerformanceResult:
    """PerformanceResult のテスト."""

    def test_正常系_to_dictで全フィールドが辞書に変換される(self) -> None:
        result = PerformanceResult(
            group="mag7",
            subgroup=None,
            generated_at="2026-01-26T12:00:00",
            periods=["1D", "1W"],
            symbols={"AAPL": {"1D": 1.5, "1W": 3.2}},
            summary={
                "best_performer": {"symbol": "AAPL", "period": "1W", "return_pct": 3.2}
            },
            latest_dates={"AAPL": "2026-01-24"},
            data_freshness={
                "newest_date": "2026-01-24",
                "oldest_date": "2026-01-24",
                "has_date_gap": False,
            },
        )

        dict_result = result.to_dict()

        assert dict_result["group"] == "mag7"
        assert dict_result["subgroup"] is None
        assert dict_result["generated_at"] == "2026-01-26T12:00:00"
        assert dict_result["periods"] == ["1D", "1W"]
        assert dict_result["symbols"]["AAPL"]["1D"] == 1.5
        assert dict_result["summary"]["best_performer"]["symbol"] == "AAPL"
        assert dict_result["latest_dates"]["AAPL"] == "2026-01-24"
        assert dict_result["data_freshness"]["has_date_gap"] is False


class TestPerformanceAnalyzer4Agent:
    """PerformanceAnalyzer4Agent のテスト."""

    @pytest.fixture
    def sample_returns_df(self) -> DataFrame:
        """テスト用の騰落率DataFrame."""
        return DataFrame(
            {
                "symbol": ["AAPL", "AAPL", "MSFT", "MSFT"],
                "period": ["1D", "1W", "1D", "1W"],
                "return_pct": [1.5, 3.2, 0.8, 2.1],
            }
        )

    @pytest.fixture
    def sample_price_df(self) -> DataFrame:
        """テスト用の価格DataFrame."""
        return DataFrame(
            {
                "Date": pd.to_datetime(
                    ["2026-01-24", "2026-01-23", "2026-01-24", "2026-01-23"]
                ),
                "symbol": ["AAPL", "AAPL", "MSFT", "MSFT"],
                "variable": ["close", "close", "close", "close"],
                "value": [180.0, 178.0, 400.0, 395.0],
            }
        )

    def test_正常系_convert_to_resultでDataFrameがPerformanceResultに変換される(
        self,
        sample_returns_df: DataFrame,
        sample_price_df: DataFrame,
    ) -> None:
        analyzer = PerformanceAnalyzer4Agent()

        result = analyzer._convert_to_result(
            sample_returns_df, sample_price_df, "test_group", None
        )

        assert result.group == "test_group"
        assert result.subgroup is None
        assert "1D" in result.periods
        assert "1W" in result.periods
        assert result.symbols["AAPL"]["1D"] == 1.5
        assert result.symbols["MSFT"]["1W"] == 2.1
        # 最新日付の確認
        assert result.latest_dates["AAPL"] == "2026-01-24"
        assert result.latest_dates["MSFT"] == "2026-01-24"

    def test_正常系_summaryに最良最悪パフォーマーが含まれる(
        self,
        sample_returns_df: DataFrame,
        sample_price_df: DataFrame,
    ) -> None:
        analyzer = PerformanceAnalyzer4Agent()

        result = analyzer._convert_to_result(
            sample_returns_df, sample_price_df, "test_group", None
        )

        assert result.summary["best_performer"]["symbol"] == "AAPL"
        assert result.summary["best_performer"]["period"] == "1W"
        assert result.summary["best_performer"]["return_pct"] == 3.2
        assert result.summary["worst_performer"]["symbol"] == "MSFT"
        assert result.summary["worst_performer"]["period"] == "1D"
        assert result.summary["worst_performer"]["return_pct"] == 0.8

    def test_正常系_period_averagesが正しく計算される(
        self,
        sample_returns_df: DataFrame,
        sample_price_df: DataFrame,
    ) -> None:
        analyzer = PerformanceAnalyzer4Agent()

        result = analyzer._convert_to_result(
            sample_returns_df, sample_price_df, "test_group", None
        )

        # 1D: (1.5 + 0.8) / 2 = 1.15
        # 1W: (3.2 + 2.1) / 2 = 2.65
        assert result.summary["period_averages"]["1D"] == 1.15
        assert result.summary["period_averages"]["1W"] == 2.65

    def test_正常系_period_bestとperiod_worstが正しく計算される(
        self,
        sample_returns_df: DataFrame,
        sample_price_df: DataFrame,
    ) -> None:
        analyzer = PerformanceAnalyzer4Agent()

        result = analyzer._convert_to_result(
            sample_returns_df, sample_price_df, "test_group", None
        )

        assert result.summary["period_best"]["1D"]["symbol"] == "AAPL"
        assert result.summary["period_best"]["1D"]["return_pct"] == 1.5
        assert result.summary["period_worst"]["1D"]["symbol"] == "MSFT"
        assert result.summary["period_worst"]["1D"]["return_pct"] == 0.8

    def test_エッジケース_空のDataFrameで空のPerformanceResultが返される(self) -> None:
        analyzer = PerformanceAnalyzer4Agent()
        empty_returns_df = DataFrame({"symbol": [], "period": [], "return_pct": []})
        empty_price_df = DataFrame(
            {"Date": [], "symbol": [], "variable": [], "value": []}
        )

        result = analyzer._convert_to_result(
            empty_returns_df, empty_price_df, "empty_group", None
        )

        assert result.group == "empty_group"
        assert result.periods == []
        assert result.symbols == {}
        assert result.summary == {}
        assert result.latest_dates == {}
        assert result.data_freshness == {}

    def test_正常系_periodsが正しい順序で並ぶ(self) -> None:
        analyzer = PerformanceAnalyzer4Agent()
        returns_df = DataFrame(
            {
                "symbol": ["AAPL", "AAPL", "AAPL"],
                "period": ["YTD", "1D", "MTD"],  # 順番をバラバラに
                "return_pct": [10.0, 1.0, 5.0],
            }
        )
        price_df = DataFrame(
            {
                "Date": pd.to_datetime(["2026-01-24"]),
                "symbol": ["AAPL"],
                "variable": ["close"],
                "value": [180.0],
            }
        )

        result = analyzer._convert_to_result(returns_df, price_df, "test", None)

        # 期待される順序: 1D, MTD, YTD
        assert result.periods == ["1D", "MTD", "YTD"]

    def test_正常系_data_freshnessで日付ズレが検出される(self) -> None:
        analyzer = PerformanceAnalyzer4Agent()
        returns_df = DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "period": ["1D", "1D"],
                "return_pct": [1.5, 0.8],
            }
        )
        # 日付が異なる価格データ
        price_df = DataFrame(
            {
                "Date": pd.to_datetime(["2026-01-24", "2026-01-23"]),
                "symbol": ["AAPL", "MSFT"],
                "variable": ["close", "close"],
                "value": [180.0, 400.0],
            }
        )

        result = analyzer._convert_to_result(returns_df, price_df, "test", None)

        assert result.data_freshness["has_date_gap"] is True
        assert result.data_freshness["newest_date"] == "2026-01-24"
        assert result.data_freshness["oldest_date"] == "2026-01-23"
        assert "2026-01-24" in result.data_freshness["symbols_by_date"]
        assert "2026-01-23" in result.data_freshness["symbols_by_date"]
