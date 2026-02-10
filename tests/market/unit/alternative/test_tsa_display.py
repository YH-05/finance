"""Unit tests for TSAPassengerDataCollector get_data_summary and format_summary.

This module tests the refactored display_data_info method which was
split into get_data_summary() and format_summary() to separate
data retrieval from presentation concerns.

Tests cover:
- get_data_summary() returns correct dict structure
- format_summary() produces formatted string from summary dict
- No print() calls remain in the module
- Logging is used instead of print for data info
"""

from unittest.mock import patch

import pandas as pd
import pytest

from market.alternative.tsa import TSAPassengerDataCollector


@pytest.fixture
def collector() -> TSAPassengerDataCollector:
    """Create a TSAPassengerDataCollector instance."""
    return TSAPassengerDataCollector()


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return (
        pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    ["2024-01-15", "2024-01-14", "2024-01-13", "2024-01-12"]
                ),
                "Numbers": [2_500_000, 2_400_000, 2_600_000, 2_300_000],
            }
        )
        .sort_values("Date", ascending=False)
        .reset_index(drop=True)
    )


class TestGetDataSummary:
    """Test get_data_summary method."""

    def test_正常系_dictを返す(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert isinstance(result, dict)

    def test_正常系_データ期間が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert "date_min" in result
        assert "date_max" in result
        assert result["date_min"] == "2024/01/12"
        assert result["date_max"] == "2024/01/15"

    def test_正常系_データ件数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert "row_count" in result
        assert result["row_count"] == 4

    def test_正常系_最大旅客数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert "max_passengers" in result
        assert result["max_passengers"] == 2_600_000
        assert "max_passengers_date" in result
        assert result["max_passengers_date"] == "2024/01/13"

    def test_正常系_最小旅客数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert "min_passengers" in result
        assert result["min_passengers"] == 2_300_000
        assert "min_passengers_date" in result
        assert result["min_passengers_date"] == "2024/01/12"

    def test_正常系_平均旅客数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        result = collector.get_data_summary(sample_df)
        assert "avg_passengers" in result
        expected_avg = (2_500_000 + 2_400_000 + 2_600_000 + 2_300_000) / 4
        assert result["avg_passengers"] == pytest.approx(expected_avg, rel=1e-2)

    def test_正常系_loggerが呼ばれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        with patch("market.alternative.tsa.logger") as mock_logger:
            collector.get_data_summary(sample_df)
            # Verify structured log context: summary kwargs must be present
            mock_logger.info.assert_called()
            info_kwargs = mock_logger.info.call_args.kwargs
            assert "row_count" in info_kwargs, (
                "Expected 'row_count' in structured log kwargs"
            )
            assert info_kwargs["row_count"] == len(sample_df)

    def test_異常系_Noneを渡すとValueError(
        self, collector: TSAPassengerDataCollector
    ) -> None:
        with pytest.raises((TypeError, ValueError)):
            collector.get_data_summary(None)

    def test_エッジケース_1行のDataFrame(
        self, collector: TSAPassengerDataCollector
    ) -> None:
        df = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-15"]),
                "Numbers": [2_500_000],
            }
        )
        result = collector.get_data_summary(df)
        assert result["row_count"] == 1
        assert result["max_passengers"] == 2_500_000
        assert result["min_passengers"] == 2_500_000


class TestFormatSummary:
    """Test format_summary method."""

    def test_正常系_文字列を返す(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert isinstance(result, str)

    def test_正常系_データ期間が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert "2024/01/12" in result
        assert "2024/01/15" in result

    def test_正常系_データ件数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert "4" in result

    def test_正常系_旅客数情報が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert "2,600,000" in result
        assert "2,300,000" in result

    def test_正常系_平均旅客数が含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert "2450000" in result or "2,450,000" in result

    def test_正常系_TSAヘッダーが含まれる(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        result = collector.format_summary(summary)
        assert "TSA" in result


class TestNoPrintCalls:
    """Test that print() is not called anywhere in the module."""

    def test_正常系_get_data_summaryでprintが呼ばれない(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        with patch("builtins.print") as mock_print:
            collector.get_data_summary(sample_df)
            mock_print.assert_not_called()

    def test_正常系_format_summaryでprintが呼ばれない(
        self, collector: TSAPassengerDataCollector, sample_df: pd.DataFrame
    ) -> None:
        summary = collector.get_data_summary(sample_df)
        with patch("builtins.print") as mock_print:
            collector.format_summary(summary)
            mock_print.assert_not_called()

    def test_正常系_モジュールにprint文がない(self) -> None:
        """Verify no print() calls exist in the tsa.py source code."""
        import inspect

        import market.alternative.tsa as tsa_module

        source = inspect.getsource(tsa_module)
        # Check that there are no print( calls in the source
        # (excluding comments and docstrings is tricky, so we check
        # for print( at the beginning of a stripped line)
        lines = source.split("\n")
        print_lines = [
            line.strip()
            for line in lines
            if line.strip().startswith("print(") and not line.strip().startswith("#")
        ]
        assert print_lines == [], f"Found print() calls: {print_lines}"
