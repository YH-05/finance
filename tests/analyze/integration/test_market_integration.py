"""Integration tests for analyze.integration.market_integration module.

These tests verify the E2E flow from market data fetching to analysis.
Note: These tests may be skipped in CI environments where network access
or API keys are not available.
"""

import os

import numpy as np
import pandas as pd
import pytest
from analyze.integration.market_integration import (
    MarketDataAnalyzer,
    analyze_market_data,
    fetch_and_analyze,
)
from analyze.statistics.types import DescriptiveStats


class TestMarketDataAnalyzerIntegration:
    """Integration tests for MarketDataAnalyzer class."""

    @pytest.mark.skipif(
        os.getenv("SKIP_NETWORK_TESTS", "false").lower() == "true",
        reason="Network tests skipped in CI",
    )
    def test_統合_実際のYFinanceデータ取得と分析(self) -> None:
        """実際の YFinance API を使用してデータ取得と分析を行う。

        Note: This test requires network access and may be flaky.
        """
        analyzer = MarketDataAnalyzer()

        # Use a stable, large-cap stock for reliability
        result = analyzer.fetch_and_analyze(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Verify structure
        assert "AAPL" in result
        assert "raw_data" in result["AAPL"]
        assert "technical_indicators" in result["AAPL"]
        assert "statistics" in result["AAPL"]

        # Verify data was fetched
        raw_data = result["AAPL"]["raw_data"]
        assert isinstance(raw_data, pd.DataFrame)
        assert len(raw_data) > 0

        # Verify analysis was performed
        indicators = result["AAPL"]["technical_indicators"]
        assert "returns" in indicators
        assert len(indicators["returns"]) == len(raw_data)

        # Verify statistics
        stats = result["AAPL"]["statistics"]
        assert isinstance(stats, DescriptiveStats)
        assert stats.count > 0
        assert not np.isnan(stats.mean)

    @pytest.mark.skipif(
        os.getenv("SKIP_NETWORK_TESTS", "false").lower() == "true",
        reason="Network tests skipped in CI",
    )
    def test_統合_複数シンボルの取得と分析(self) -> None:
        """複数のシンボルを同時に取得して分析する。"""
        analyzer = MarketDataAnalyzer()

        result = analyzer.fetch_and_analyze(
            symbols=["AAPL", "MSFT"],
            start_date="2024-01-01",
            end_date="2024-01-15",
        )

        # Verify both symbols are present
        assert "AAPL" in result
        assert "MSFT" in result

        # Verify both have data
        for symbol in ["AAPL", "MSFT"]:
            assert result[symbol]["data_empty"] is False
            assert len(result[symbol]["raw_data"]) > 0


class TestAnalyzeMarketDataIntegration:
    """Integration tests for analyze_market_data with realistic data."""

    def test_統合_リアルなデータセットでの分析(self) -> None:
        """リアルな OHLCV データに対して分析を行う。"""
        # Create a realistic DataFrame mimicking market data
        np.random.seed(42)
        n_days = 100
        dates = pd.date_range("2024-01-01", periods=n_days)

        # Generate realistic price movements
        base_price = 150.0
        returns = np.random.normal(0.0005, 0.02, n_days)
        close_prices = base_price * np.cumprod(1 + returns)

        data = pd.DataFrame(
            {
                "open": close_prices * (1 + np.random.uniform(-0.01, 0.01, n_days)),
                "high": close_prices * (1 + np.random.uniform(0, 0.02, n_days)),
                "low": close_prices * (1 + np.random.uniform(-0.02, 0, n_days)),
                "close": close_prices,
                "volume": np.random.randint(1000000, 5000000, n_days),
            },
            index=dates,
        )

        result = analyze_market_data(data)

        # Verify technical indicators
        indicators = result["technical_indicators"]
        assert "returns" in indicators
        assert "sma_20" in indicators
        assert "sma_50" in indicators
        assert "ema_12" in indicators
        assert "ema_26" in indicators
        assert "rsi" in indicators
        assert "volatility" in indicators

        # Verify returns are reasonable
        returns_series = indicators["returns"]
        assert -0.5 < returns_series.mean() < 0.5  # Reasonable daily returns

        # Verify RSI is in valid range
        rsi = indicators["rsi"].dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

        # Verify statistics
        stats = result["statistics"]
        assert isinstance(stats, DescriptiveStats)
        assert stats.count == n_days
        assert 100 < stats.mean < 200  # Price should be around 150

    def test_統合_短期データでの分析(self) -> None:
        """短期データ（一部の指標が計算不可）での分析を行う。"""
        # Only 10 days of data - not enough for SMA 20 or 50
        data = pd.DataFrame(
            {
                "open": [100.0 + i * 0.5 for i in range(10)],
                "high": [101.0 + i * 0.5 for i in range(10)],
                "low": [99.0 + i * 0.5 for i in range(10)],
                "close": [100.0 + i * 0.5 for i in range(10)],
                "volume": [1000000 + i * 10000 for i in range(10)],
            },
            index=pd.date_range("2024-01-01", periods=10),
        )

        result = analyze_market_data(data)

        # Returns should be calculated
        assert "returns" in result["technical_indicators"]

        # SMA 20 should NOT be present (not enough data)
        assert "sma_20" not in result["technical_indicators"]

        # But statistics should still work
        stats = result["statistics"]
        assert stats.count == 10


class TestFetchAndAnalyzeIntegration:
    """Integration tests for fetch_and_analyze convenience function."""

    @pytest.mark.skipif(
        os.getenv("SKIP_NETWORK_TESTS", "false").lower() == "true",
        reason="Network tests skipped in CI",
    )
    def test_統合_便利関数でのE2Eフロー(self) -> None:
        """fetch_and_analyze 便利関数による E2E フローをテスト。"""
        result = fetch_and_analyze(
            symbols=["AAPL"],
            start_date="2024-01-02",
            end_date="2024-01-05",
        )

        assert "AAPL" in result
        assert "technical_indicators" in result["AAPL"]
        assert "statistics" in result["AAPL"]


class TestMarketAnalyzeDataFlow:
    """Tests for the data flow from market to analyze."""

    def test_統合_market形式のデータが正しくanalyzeで処理される(self) -> None:
        """market パッケージが返す形式のデータが analyze で正しく処理される。"""
        # Simulate data in the format returned by YFinanceFetcher
        market_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=pd.DatetimeIndex(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                ]
            ),
        )

        result = analyze_market_data(market_data)

        # Verify the flow worked
        assert "technical_indicators" in result
        assert "statistics" in result

        # Verify returns calculation
        returns = result["technical_indicators"]["returns"]
        # Second day return: (101.5 - 100.5) / 100.5 = 0.00995...
        assert returns.iloc[1] == pytest.approx(0.00995, rel=0.01)

        # Verify statistics are correct
        stats = result["statistics"]
        assert stats.count == 5
        assert stats.mean == pytest.approx(102.5, rel=0.01)
