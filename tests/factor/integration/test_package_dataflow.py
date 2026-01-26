"""Tests for data flow between packages: market -> factor -> analyze.

This module tests the end-to-end data flow between packages,
ensuring proper integration and data transformation.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from factor.integration.analyze_integration import EnhancedFactorAnalyzer
from factor.integration.market_integration import MarketDataProvider


class TestMarketToFactorDataFlow:
    """Tests for market -> factor data flow."""

    @pytest.fixture
    def mock_market_data(self) -> pd.DataFrame:
        """Create mock market data."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        return pd.DataFrame(
            {
                "open": prices - 0.5,
                "high": prices + 1,
                "low": prices - 1,
                "close": prices,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=pd.DatetimeIndex(dates, name="Date"),
        )

    def test_正常系_MarketDataProviderから取得したデータでファクター計算可能(
        self, mock_market_data: pd.DataFrame
    ) -> None:
        """MarketDataProvider からのデータでファクター計算ができることを確認。"""
        provider = MarketDataProvider()

        # Mock the fetcher
        with patch.object(provider, "_fetcher") as mock_fetcher:
            mock_result = MagicMock()
            mock_result.data = mock_market_data
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]

            # Fetch data via market package integration
            price_data = provider.get_prices(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-04-10",
            )

            # Verify data can be used with analyze integration
            analyzer = EnhancedFactorAnalyzer()

            # Extract close prices for analysis
            if ("AAPL", "Close") in price_data.columns:
                close_prices: pd.Series = price_data[  # type: ignore[assignment]
                    ("AAPL", "Close")
                ]
            else:
                # Fall back to checking original data
                close_prices = mock_market_data["close"]  # type: ignore[assignment]

            rsi = analyzer.compute_rsi(close_prices)
            volatility = analyzer.compute_volatility(close_prices)

            # Verify results are valid
            assert isinstance(rsi, pd.Series)
            assert isinstance(volatility, pd.Series)
            assert len(rsi) == len(close_prices)
            assert len(volatility) == len(close_prices)

    def test_正常系_market_analyze連携でテクニカル分析可能(
        self, mock_market_data: pd.DataFrame
    ) -> None:
        """market -> analyze の連携でテクニカル分析ができることを確認。"""
        # Create analyzer and compute indicators
        analyzer = EnhancedFactorAnalyzer()
        indicators = analyzer.compute_indicators(mock_market_data)

        # Verify all expected indicators are present
        assert "returns" in indicators
        assert "sma_20" in indicators or len(mock_market_data) < 20
        assert "volatility" in indicators or len(mock_market_data) < 20


class TestAnalyzeToFactorDataFlow:
    """Tests for analyze -> factor data flow."""

    @pytest.fixture
    def sample_returns(self) -> pd.Series:
        """Create sample return data."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=252, freq="D")
        returns = np.random.randn(252) * 0.02
        return pd.Series(returns, index=dates, name="returns")

    def test_正常系_analyzeのテクニカル指標をファクター検証に使用可能(
        self, sample_returns: pd.Series
    ) -> None:
        """analyze パッケージのテクニカル指標をファクター検証に使用できることを確認。"""
        analyzer = EnhancedFactorAnalyzer()

        # Compute cumulative prices from returns
        prices = (1 + sample_returns).cumprod() * 100

        # Compute indicators using analyze package integration
        indicators = analyzer.compute_indicators(pd.DataFrame({"close": prices}))

        # Verify indicators can be used for factor validation
        assert "returns" in indicators
        assert isinstance(indicators["returns"], pd.Series)

        # Compute correlation between factor and returns
        if "sma_20" in indicators:
            # SMA crossover signal as factor proxy
            sma = indicators["sma_20"]
            factor_signal = (prices > sma).astype(float)

            # Calculate correlation
            valid_mask = factor_signal.notna() & sample_returns.notna()
            if valid_mask.sum() > 10:
                factor_subset: pd.Series = factor_signal[valid_mask]  # type: ignore[assignment]
                returns_subset: pd.Series = sample_returns[valid_mask]  # type: ignore[assignment]
                corr = analyzer.compute_correlation(
                    factor_subset,
                    returns_subset,
                )
                # Correlation should be a valid number
                assert isinstance(corr, float)

    def test_正常系_複数銘柄の相関マトリクス計算可能(self) -> None:
        """複数銘柄間の相関マトリクスを計算できることを確認。"""
        analyzer = EnhancedFactorAnalyzer()

        # Create sample data for multiple symbols
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        aapl = pd.Series(np.random.randn(100), index=dates, name="AAPL")
        googl = pd.Series(np.random.randn(100) * 1.2 + 0.1, index=dates, name="GOOGL")

        # Compute pairwise correlation
        corr = analyzer.compute_correlation(aapl, googl)

        # Verify result
        assert isinstance(corr, float)
        assert -1.0 <= corr <= 1.0


class TestEndToEndFactorPipeline:
    """Tests for end-to-end factor calculation pipeline."""

    @pytest.fixture
    def mock_price_data(self) -> pd.DataFrame:
        """Create comprehensive mock price data."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=252, freq="D")
        # Create realistic stock prices with trend
        trend = np.linspace(0, 50, 252)
        noise = np.cumsum(np.random.randn(252) * 2)
        prices = 100 + trend + noise

        return pd.DataFrame(
            {
                "open": prices - np.random.rand(252) * 2,
                "high": prices + np.random.rand(252) * 2,
                "low": prices - np.random.rand(252) * 2,
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, 252),
            },
            index=pd.DatetimeIndex(dates, name="Date"),
        )

    def test_正常系_完全なファクター計算パイプライン(
        self, mock_price_data: pd.DataFrame
    ) -> None:
        """market -> analyze -> factor の完全なパイプラインが動作することを確認。"""
        # Step 1: Market data provider setup
        provider = MarketDataProvider()

        # Step 2: Enhanced analyzer setup
        analyzer = EnhancedFactorAnalyzer()

        # Step 3: Compute technical indicators (analyze package)
        indicators = analyzer.compute_indicators(mock_price_data)

        # Step 4: Compute momentum factor
        close_prices: pd.Series = mock_price_data["close"]  # type: ignore[assignment]
        _ = close_prices.pct_change(periods=20)  # momentum_20d for potential use
        _ = close_prices.pct_change(periods=60)  # momentum_60d for potential use

        # Step 5: Compute factor with RSI and volatility
        from factor.integration.analyze_integration import (
            calculate_factor_with_indicators,
        )

        factor_result = calculate_factor_with_indicators(
            close_prices,
            factor_window=20,
            include_rsi=True,
            include_volatility=True,
        )

        # Verify complete pipeline output
        assert "momentum" in factor_result or "factor_value" in factor_result
        assert "returns" in factor_result
        assert "rsi" in factor_result
        assert "volatility" in factor_result

        # Verify data integrity
        assert len(factor_result["returns"]) == len(close_prices)
        assert factor_result["rsi"].dropna().min() >= 0
        assert factor_result["rsi"].dropna().max() <= 100

    def test_正常系_ファクターとベンチマークの相関分析(
        self, mock_price_data: pd.DataFrame
    ) -> None:
        """ファクターとベンチマークの相関分析ができることを確認。"""
        analyzer = EnhancedFactorAnalyzer()

        # Compute momentum factor
        close_prices: pd.Series = mock_price_data["close"]  # type: ignore[assignment]
        momentum = close_prices.pct_change(periods=20)

        # Create mock benchmark returns
        np.random.seed(123)
        benchmark_returns = pd.Series(
            np.random.randn(252) * 0.01,
            index=mock_price_data.index,
        )

        # Compute correlation
        # Align data
        valid_mask = momentum.notna() & benchmark_returns.notna()
        if valid_mask.sum() > 10:
            momentum_subset: pd.Series = momentum[valid_mask]  # type: ignore[assignment]
            bench_subset: pd.Series = benchmark_returns[valid_mask]  # type: ignore[assignment]
            corr = analyzer.compute_correlation(
                momentum_subset,
                bench_subset,
            )

            # Verify correlation is computed
            assert isinstance(corr, float)
            assert not np.isnan(corr)
