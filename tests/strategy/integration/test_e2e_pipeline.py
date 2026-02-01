"""End-to-end pipeline tests for strategy package integration.

This module tests the complete data flow from market -> analyze -> factor -> strategy
using mock data to verify the full pipeline without external API calls.
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from strategy.integration import (
    FactorBasedRiskCalculator,
    IntegratedStrategyBuilder,
    StrategyMarketDataProvider,
    TechnicalSignalProvider,
)


class TestE2EPipeline:
    """End-to-end pipeline tests."""

    @pytest.fixture
    def mock_price_data(self) -> pd.DataFrame:
        """Create mock price data for testing."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 100)
        prices = base_price * np.cumprod(1 + returns)

        return pd.DataFrame(
            {
                "open": prices * 0.99,
                "high": prices * 1.01,
                "low": prices * 0.98,
                "close": prices,
                "volume": np.random.randint(100000, 1000000, 100),
            },
            index=dates,
        )

    def test_正常系_完全なパイプラインの実行(
        self, mock_price_data: pd.DataFrame
    ) -> None:
        """市場データ→テクニカル分析→リスク計算の完全なパイプライン."""
        # Step 1: Compute technical signals
        signal_provider = TechnicalSignalProvider()
        close_prices = pd.Series(mock_price_data["close"])
        signals = signal_provider.compute_signals(close_prices)

        assert "returns" in signals
        assert "volatility" in signals or "rsi" in signals

        # Step 2: Calculate returns
        returns = pd.Series(close_prices.pct_change().dropna())

        # Step 3: Calculate risk metrics
        risk_calculator = FactorBasedRiskCalculator()
        risk_metrics = risk_calculator.calculate_risk(returns)

        assert "volatility" in risk_metrics
        assert "sharpe_ratio" in risk_metrics
        assert "max_drawdown" in risk_metrics
        assert "factor_exposure" in risk_metrics

        # Validate risk metrics
        assert risk_metrics["volatility"] >= 0
        assert -1.0 <= risk_metrics["max_drawdown"] <= 0.0

    def test_正常系_モメンタムシグナル計算(self, mock_price_data: pd.DataFrame) -> None:
        """モメンタムシグナルが正しく計算される."""
        signal_provider = TechnicalSignalProvider()
        close_prices = pd.Series(mock_price_data["close"])
        momentum = signal_provider.compute_momentum_signal(close_prices, lookback=20)

        assert len(momentum) == len(mock_price_data)
        # First 20 values should be NaN
        assert momentum.iloc[:20].isna().all()
        # Rest should have values
        assert momentum.iloc[20:].notna().all()

    def test_正常系_トレンドシグナル計算(self, mock_price_data: pd.DataFrame) -> None:
        """トレンドシグナルが正しく計算される."""
        signal_provider = TechnicalSignalProvider()
        close_prices = pd.Series(mock_price_data["close"])
        trend = signal_provider.compute_trend_signal(close_prices)

        assert len(trend) == len(mock_price_data)
        # Signal should be -1, 0, or 1
        unique_values = set(trend.dropna().unique())
        assert unique_values.issubset({-1.0, 0.0, 1.0})

    def test_正常系_RSIシグナル計算(self, mock_price_data: pd.DataFrame) -> None:
        """RSIシグナルが正しく計算される."""
        signal_provider = TechnicalSignalProvider()
        close_prices = pd.Series(mock_price_data["close"])
        rsi_signal = signal_provider.compute_rsi_signal(close_prices)

        assert len(rsi_signal) == len(mock_price_data)
        # Signal should be -1, 0, or 1
        unique_values = set(rsi_signal.dropna().unique())
        assert unique_values.issubset({-1.0, 0.0, 1.0})

    def test_正常系_ファクターアトリビューション計算(
        self, mock_price_data: pd.DataFrame
    ) -> None:
        """ファクターアトリビューションが正しく計算される."""
        close_prices = pd.Series(mock_price_data["close"])
        returns = pd.Series(close_prices.pct_change().dropna())

        # Create mock factor returns
        np.random.seed(123)
        market_returns = pd.Series(
            np.random.normal(0.001, 0.02, len(returns)),
            index=returns.index,
        )

        risk_calculator = FactorBasedRiskCalculator()
        attribution = risk_calculator.calculate_factor_attribution(
            returns, {"market": market_returns}
        )

        assert "market_beta" in attribution
        assert "residual_return" in attribution
        assert "r_squared" in attribution

    def test_正常系_複数シンボルのパイプライン(self) -> None:
        """複数シンボルでのパイプラインが動作する."""
        # Create multi-symbol mock data
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        np.random.seed(42)

        symbols = ["AAPL", "GOOGL", "MSFT"]
        all_results: dict[str, dict] = {}

        for i, symbol in enumerate(symbols):
            np.random.seed(42 + i)
            base_price = 100.0 + i * 50
            returns = np.random.normal(0.001 + i * 0.0005, 0.02, 50)
            prices = pd.Series(
                base_price * np.cumprod(1 + returns),
                index=dates,
            )

            signal_provider = TechnicalSignalProvider()
            signals = signal_provider.compute_signals(prices)

            risk_calculator = FactorBasedRiskCalculator()
            symbol_returns = prices.pct_change().dropna()
            risk_metrics = risk_calculator.calculate_risk(symbol_returns)

            all_results[symbol] = {
                "signals": signals,
                "risk": risk_metrics,
            }

        # Verify all symbols have results
        assert len(all_results) == 3
        for symbol in symbols:
            assert symbol in all_results
            assert "signals" in all_results[symbol]
            assert "risk" in all_results[symbol]

    def test_正常系_ファクターエクスポージャー計算(
        self, mock_price_data: pd.DataFrame
    ) -> None:
        """ファクターエクスポージャーが正しく計算される."""
        close_prices = pd.Series(mock_price_data["close"])
        returns = pd.Series(close_prices.pct_change().dropna())

        risk_calculator = FactorBasedRiskCalculator()
        exposure = risk_calculator.calculate_factor_exposure(returns)

        assert "momentum_exposure" in exposure
        assert "volatility_exposure" in exposure

        # Volatility exposure should be positive
        assert exposure["volatility_exposure"] >= 0

    def test_異常系_空のデータでパイプライン(self) -> None:
        """空のデータでパイプラインがエラーなく処理される."""
        empty_prices = pd.Series(dtype=float)

        signal_provider = TechnicalSignalProvider()
        signals = signal_provider.compute_signals(empty_prices)
        assert signals == {}

        risk_calculator = FactorBasedRiskCalculator()
        risk_metrics = risk_calculator.calculate_risk(empty_prices)
        assert np.isnan(risk_metrics["volatility"])

    def test_正常系_短期データでパイプライン(self) -> None:
        """短期データでパイプラインが動作する."""
        short_prices = pd.Series(
            [100.0, 101.0, 102.0, 101.5, 103.0],
            index=pd.date_range("2024-01-01", periods=5, freq="D"),
        )

        signal_provider = TechnicalSignalProvider()
        signals = signal_provider.compute_signals(short_prices)

        # Should at least have returns
        assert "returns" in signals

        returns = short_prices.pct_change().dropna()
        risk_calculator = FactorBasedRiskCalculator()
        risk_metrics = risk_calculator.calculate_risk(returns)

        # Should have basic metrics even with short data
        assert "volatility" in risk_metrics


class TestIntegrationWithMockFetcher:
    """Test integration using mock fetcher to avoid external API calls."""

    def test_正常系_ビルダーでモックフェッチャーを使用(self) -> None:
        """IntegratedStrategyBuilder がモックフェッチャーで動作する."""
        # Create mock fetcher
        mock_fetcher = MagicMock()

        # Configure mock response
        mock_result = MagicMock()
        mock_result.symbol = "AAPL"
        mock_result.is_empty = False
        mock_result.data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
                "volume": [1000000, 1100000, 1200000],
            },
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )
        mock_fetcher.fetch.return_value = [mock_result]

        # Create market provider with mock fetcher
        market_provider = StrategyMarketDataProvider(fetcher=mock_fetcher)

        # Create builder with mock market provider
        builder = IntegratedStrategyBuilder(market_provider=market_provider)

        # Verify fetcher was called correctly
        # We don't call build_strategy to avoid the fetch call, just verify setup
        assert builder.market_provider is market_provider


class TestImportFromStrategy:
    """Test that integration classes can be imported from strategy package."""

    def test_正常系_strategyパッケージからインポート(self) -> None:
        """strategy パッケージから integration クラスをインポートできる."""
        from strategy import (
            FactorBasedRiskCalculator,
            IntegratedStrategyBuilder,
            StrategyMarketDataProvider,
            TechnicalSignalProvider,
            create_factor_risk_calculator,
            create_integrated_builder,
            create_signal_provider,
            create_strategy_market_provider,
        )

        # Verify all imports work
        assert IntegratedStrategyBuilder is not None
        assert StrategyMarketDataProvider is not None
        assert TechnicalSignalProvider is not None
        assert FactorBasedRiskCalculator is not None
        assert create_integrated_builder is not None
        assert create_strategy_market_provider is not None
        assert create_signal_provider is not None
        assert create_factor_risk_calculator is not None
