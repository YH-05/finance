"""InterestRateAnalyzer4Agent のテスト.

TDDに基づいてテストを先に作成し、実装を後から行う。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from analyze.reporting.interest_rate_agent import (
    InterestRateAnalyzer4Agent,
    InterestRateResult,
)
from pandas import DataFrame


class TestInterestRateResult:
    """InterestRateResult のテスト."""

    def test_正常系_to_dictで全フィールドが辞書に変換される(self) -> None:
        """InterestRateResultのto_dictが全フィールドを含む辞書を返すことを確認."""
        result = InterestRateResult(
            group="interest_rates",
            generated_at="2026-01-29T12:00:00",
            periods=["1D", "1W", "1M"],
            data={
                "DGS2": {"latest": 4.5, "changes": {"1D": 0.02, "1W": 0.1, "1M": 0.3}},
                "DGS10": {
                    "latest": 4.0,
                    "changes": {"1D": 0.01, "1W": 0.05, "1M": 0.2},
                },
            },
            yield_curve={
                "is_inverted": True,
                "spread_10y_2y": -0.5,
                "slope_status": "inverted",
                "dgs2_latest": 4.5,
                "dgs10_latest": 4.0,
                "dgs30_latest": 4.2,
            },
            data_freshness={
                "newest_date": "2026-01-28",
                "oldest_date": "2026-01-28",
                "has_date_gap": False,
            },
        )

        dict_result = result.to_dict()

        assert dict_result["group"] == "interest_rates"
        assert dict_result["generated_at"] == "2026-01-29T12:00:00"
        assert dict_result["periods"] == ["1D", "1W", "1M"]
        assert dict_result["data"]["DGS2"]["latest"] == 4.5
        assert dict_result["data"]["DGS2"]["changes"]["1D"] == 0.02
        assert dict_result["yield_curve"]["is_inverted"] is True
        assert dict_result["yield_curve"]["spread_10y_2y"] == -0.5
        assert dict_result["data_freshness"]["has_date_gap"] is False

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """InterestRateResultがデフォルト値で初期化できることを確認."""
        result = InterestRateResult(
            group="interest_rates",
            generated_at="2026-01-29T12:00:00",
            periods=[],
            data={},
        )

        dict_result = result.to_dict()

        assert dict_result["group"] == "interest_rates"
        assert dict_result["periods"] == []
        assert dict_result["data"] == {}
        assert dict_result["yield_curve"] == {}
        assert dict_result["data_freshness"] == {}


class TestInterestRateAnalyzer4Agent:
    """InterestRateAnalyzer4Agent のテスト."""

    @pytest.fixture
    def sample_fetched_data(self) -> dict[str, DataFrame]:
        """InterestRateAnalyzer.fetch_data() の戻り値をモック."""
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

    @pytest.fixture
    def sample_changes(self) -> dict[str, dict[str, float | None]]:
        """InterestRateAnalyzer.calculate_changes() の戻り値をモック."""
        return {
            "DGS2": {"1D": 0.01, "1W": 0.05, "1M": 0.21},
            "DGS10": {"1D": 0.01, "1W": 0.05, "1M": 0.21},
            "DGS30": {"1D": 0.01, "1W": 0.05, "1M": 0.21},
            "FEDFUNDS": {"1D": 0.0, "1W": 0.0, "1M": 0.0},
            "T10Y2Y": {"1D": 0.01, "1W": 0.05, "1M": 0.21},
        }

    @pytest.fixture
    def sample_yield_curve(self) -> dict[str, Any]:
        """InterestRateAnalyzer.analyze_yield_curve() の戻り値をモック."""
        return {
            "is_inverted": True,
            "spread_10y_2y": -0.21,
            "slope_status": "inverted",
            "dgs2_latest": 4.79,
            "dgs10_latest": 4.29,
            "dgs30_latest": 4.49,
        }

    def test_正常系_初期化が成功する(self) -> None:
        """InterestRateAnalyzer4Agentがデフォルト設定で初期化できることを確認."""
        analyzer = InterestRateAnalyzer4Agent()

        assert analyzer is not None
        assert hasattr(analyzer, "logger")

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_get_interest_rate_dataでInterestRateResultが返される(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """get_interest_rate_dataがInterestRateResultを返すことを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        assert isinstance(result, InterestRateResult)
        assert result.group == "interest_rates"

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_dataに全シリーズのlatest値とchangesが含まれる(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """dataに各シリーズのlatest値と変化量が含まれることを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        # 全シリーズがdataに含まれる
        assert "DGS2" in result.data
        assert "DGS10" in result.data
        assert "DGS30" in result.data
        assert "FEDFUNDS" in result.data
        assert "T10Y2Y" in result.data

        # latestとchangesが含まれる
        assert "latest" in result.data["DGS10"]
        assert "changes" in result.data["DGS10"]
        assert result.data["DGS10"]["changes"]["1D"] == 0.01

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_yield_curveが正しく設定される(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """yield_curveにイールドカーブ分析結果が含まれることを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        assert result.yield_curve["is_inverted"] is True
        assert result.yield_curve["spread_10y_2y"] == -0.21
        assert result.yield_curve["slope_status"] == "inverted"

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_data_freshnessが正しく計算される(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """data_freshnessにデータ鮮度情報が含まれることを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        assert "newest_date" in result.data_freshness
        assert "oldest_date" in result.data_freshness
        assert "has_date_gap" in result.data_freshness

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_periodsが正しく設定される(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """periodsに分析対象期間が含まれることを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        assert "1D" in result.periods
        assert "1W" in result.periods
        assert "1M" in result.periods

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_エッジケース_空データでも空のInterestRateResultが返される(
        self,
        mock_analyzer_class: MagicMock,
    ) -> None:
        """空のデータでも空のInterestRateResultが返されることを確認."""
        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = {}
        mock_analyzer.calculate_changes.return_value = {}
        mock_analyzer.analyze_yield_curve.return_value = {
            "is_inverted": False,
            "spread_10y_2y": None,
            "slope_status": "unknown",
            "dgs2_latest": None,
            "dgs10_latest": None,
            "dgs30_latest": None,
        }
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        assert isinstance(result, InterestRateResult)
        assert result.group == "interest_rates"
        assert result.data == {}

    @patch("analyze.reporting.interest_rate_agent.InterestRateAnalyzer")
    def test_正常系_to_dictでJSON変換可能な辞書が返される(
        self,
        mock_analyzer_class: MagicMock,
        sample_fetched_data: dict[str, DataFrame],
        sample_changes: dict[str, dict[str, float | None]],
        sample_yield_curve: dict[str, Any],
    ) -> None:
        """to_dictで返される辞書がJSON変換可能であることを確認."""
        import json

        mock_analyzer = MagicMock()
        mock_analyzer.fetch_data.return_value = sample_fetched_data
        mock_analyzer.calculate_changes.return_value = sample_changes
        mock_analyzer.analyze_yield_curve.return_value = sample_yield_curve
        mock_analyzer.TARGET_SERIES = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]
        mock_analyzer_class.return_value = mock_analyzer

        agent_analyzer = InterestRateAnalyzer4Agent()
        result = agent_analyzer.get_interest_rate_data()

        # JSON変換が例外なく完了することを確認
        json_str = json.dumps(result.to_dict(), ensure_ascii=False)
        assert json_str is not None
        assert len(json_str) > 0


class TestDataFreshnessCalculation:
    """データ鮮度計算のテスト."""

    def test_正常系_日付ズレがない場合has_date_gapがFalse(self) -> None:
        """全シリーズの最新日付が同じ場合、has_date_gapがFalseになることを確認."""
        analyzer = InterestRateAnalyzer4Agent()
        # 同じ日付のデータ
        dates = pd.date_range("2026-01-25", periods=5, freq="D")
        data = {
            "DGS2": DataFrame({"value": [4.5, 4.6, 4.7, 4.8, 4.9]}, index=dates),
            "DGS10": DataFrame({"value": [4.0, 4.1, 4.2, 4.3, 4.4]}, index=dates),
        }

        freshness = analyzer._calculate_data_freshness(data)

        assert freshness["has_date_gap"] is False
        assert freshness["newest_date"] == freshness["oldest_date"]

    def test_正常系_日付ズレがある場合has_date_gapがTrue(self) -> None:
        """シリーズ間で最新日付が異なる場合、has_date_gapがTrueになることを確認."""
        analyzer = InterestRateAnalyzer4Agent()
        # 異なる日付のデータ
        dates1 = pd.date_range("2026-01-25", periods=5, freq="D")
        dates2 = pd.date_range("2026-01-24", periods=5, freq="D")  # 1日遅れ
        data = {
            "DGS2": DataFrame({"value": [4.5, 4.6, 4.7, 4.8, 4.9]}, index=dates1),
            "DGS10": DataFrame({"value": [4.0, 4.1, 4.2, 4.3, 4.4]}, index=dates2),
        }

        freshness = analyzer._calculate_data_freshness(data)

        assert freshness["has_date_gap"] is True
        assert freshness["newest_date"] != freshness["oldest_date"]

    def test_エッジケース_空データで空の辞書が返される(self) -> None:
        """空のデータで空の辞書が返されることを確認."""
        analyzer = InterestRateAnalyzer4Agent()
        data: dict[str, DataFrame] = {}

        freshness = analyzer._calculate_data_freshness(data)

        assert freshness == {}


class TestLogging:
    """ロギングのテスト."""

    def test_正常系_loggerが設定されている(self) -> None:
        """InterestRateAnalyzer4Agentにloggerが設定されていることを確認."""
        analyzer = InterestRateAnalyzer4Agent()

        assert hasattr(analyzer, "logger")
