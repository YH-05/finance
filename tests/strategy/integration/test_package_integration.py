"""Tests for strategy package integration with market, analyze, and factor packages.

This module tests the complete data flow from market -> analyze -> factor -> strategy.
"""

import pandas as pd

from strategy.integration import (
    FactorBasedRiskCalculator,
    IntegratedStrategyBuilder,
    StrategyMarketDataProvider,
    TechnicalSignalProvider,
    create_factor_risk_calculator,
    create_integrated_builder,
    create_signal_provider,
    create_strategy_market_provider,
)


class TestStrategyMarketDataProvider:
    """Test StrategyMarketDataProvider class."""

    def test_正常系_プロバイダーの初期化(self) -> None:
        """StrategyMarketDataProvider が正常に初期化される."""
        provider = StrategyMarketDataProvider()
        assert provider is not None

    def test_正常系_ファクトリ関数でプロバイダー作成(self) -> None:
        """create_strategy_market_provider でプロバイダーを作成できる."""
        provider = create_strategy_market_provider()
        assert isinstance(provider, StrategyMarketDataProvider)

    def test_正常系_get_prices_メソッドが存在(self) -> None:
        """get_prices メソッドが存在する."""
        provider = StrategyMarketDataProvider()
        assert hasattr(provider, "get_prices")
        assert callable(provider.get_prices)


class TestTechnicalSignalProvider:
    """Test TechnicalSignalProvider class."""

    def test_正常系_プロバイダーの初期化(self) -> None:
        """TechnicalSignalProvider が正常に初期化される."""
        provider = TechnicalSignalProvider()
        assert provider is not None

    def test_正常系_ファクトリ関数でプロバイダー作成(self) -> None:
        """create_signal_provider でプロバイダーを作成できる."""
        provider = create_signal_provider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_正常系_compute_signals_メソッドが存在(self) -> None:
        """compute_signals メソッドが存在する."""
        provider = TechnicalSignalProvider()
        assert hasattr(provider, "compute_signals")
        assert callable(provider.compute_signals)

    def test_正常系_価格データからシグナルを計算(self) -> None:
        """価格データから技術的シグナルを計算できる."""
        provider = TechnicalSignalProvider()
        # Create sample price data
        prices = pd.Series(
            [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
                116.0,
                117.0,
                118.0,
                119.0,
                120.0,
            ],
            index=pd.date_range("2024-01-01", periods=21, freq="D"),
        )
        signals = provider.compute_signals(prices)
        assert isinstance(signals, dict)
        assert "rsi" in signals or "returns" in signals


class TestFactorBasedRiskCalculator:
    """Test FactorBasedRiskCalculator class."""

    def test_正常系_計算機の初期化(self) -> None:
        """FactorBasedRiskCalculator が正常に初期化される."""
        calculator = FactorBasedRiskCalculator()
        assert calculator is not None

    def test_正常系_ファクトリ関数で計算機作成(self) -> None:
        """create_factor_risk_calculator で計算機を作成できる."""
        calculator = create_factor_risk_calculator()
        assert isinstance(calculator, FactorBasedRiskCalculator)

    def test_正常系_calculate_risk_メソッドが存在(self) -> None:
        """calculate_risk メソッドが存在する."""
        calculator = FactorBasedRiskCalculator()
        assert hasattr(calculator, "calculate_risk")
        assert callable(calculator.calculate_risk)

    def test_正常系_リターンデータからリスクを計算(self) -> None:
        """リターンデータからファクターベースのリスクを計算できる."""
        calculator = FactorBasedRiskCalculator()
        # Create sample returns data
        returns = pd.Series(
            [0.01, -0.02, 0.015, -0.005, 0.02, -0.01, 0.008, 0.003, -0.007, 0.012],
            index=pd.date_range("2024-01-01", periods=10, freq="D"),
        )
        risk = calculator.calculate_risk(returns)
        assert isinstance(risk, dict)
        assert "volatility" in risk or "factor_exposure" in risk


class TestIntegratedStrategyBuilder:
    """Test IntegratedStrategyBuilder class."""

    def test_正常系_ビルダーの初期化(self) -> None:
        """IntegratedStrategyBuilder が正常に初期化される."""
        builder = IntegratedStrategyBuilder()
        assert builder is not None

    def test_正常系_ファクトリ関数でビルダー作成(self) -> None:
        """create_integrated_builder でビルダーを作成できる."""
        builder = create_integrated_builder()
        assert isinstance(builder, IntegratedStrategyBuilder)

    def test_正常系_各統合モジュールへのアクセス(self) -> None:
        """ビルダーから各統合モジュールにアクセスできる."""
        builder = IntegratedStrategyBuilder()
        assert hasattr(builder, "market_provider")
        assert hasattr(builder, "signal_provider")
        assert hasattr(builder, "risk_calculator")

    def test_正常系_build_strategy_メソッドが存在(self) -> None:
        """build_strategy メソッドが存在する."""
        builder = IntegratedStrategyBuilder()
        assert hasattr(builder, "build_strategy")
        assert callable(builder.build_strategy)


class TestDataFlowIntegration:
    """Test complete data flow: market -> analyze -> factor -> strategy."""

    def test_正常系_市場データ取得から戦略構築まで(self) -> None:
        """市場データ取得から戦略構築までの完全なフローが動作する."""
        builder = IntegratedStrategyBuilder()

        # Mock the external data fetching
        # In real integration test, this would use actual data
        mock_price_data = pd.DataFrame(
            {
                "close": [100.0 + i for i in range(30)],
                "open": [99.0 + i for i in range(30)],
                "high": [101.0 + i for i in range(30)],
                "low": [98.0 + i for i in range(30)],
                "volume": [1000000 + i * 10000 for i in range(30)],
            },
            index=pd.date_range("2024-01-01", periods=30, freq="D"),
        )

        # Step 1: Compute technical signals from analyze package
        close_prices = pd.Series(mock_price_data["close"])
        signals = builder.signal_provider.compute_signals(close_prices)
        assert isinstance(signals, dict)

        # Step 2: Calculate risk with factor considerations
        returns_series = pd.Series(close_prices.pct_change().dropna())
        risk_metrics = builder.risk_calculator.calculate_risk(returns_series)
        assert isinstance(risk_metrics, dict)

    def test_正常系_ファクターエクスポージャー計算(self) -> None:
        """ファクターエクスポージャーが計算できる."""
        calculator = FactorBasedRiskCalculator()
        returns = pd.Series(
            [0.01, -0.02, 0.015, -0.005, 0.02],
            index=pd.date_range("2024-01-01", periods=5, freq="D"),
        )
        result = calculator.calculate_factor_exposure(returns)
        assert result is not None


class TestImportCompatibility:
    """Test that all expected imports work correctly."""

    def test_正常系_strategyからmarket連携モジュールをインポート(self) -> None:
        """strategy から market 連携モジュールをインポートできる."""
        from strategy.integration import StrategyMarketDataProvider

        assert StrategyMarketDataProvider is not None

    def test_正常系_strategyからanalyze連携モジュールをインポート(self) -> None:
        """strategy から analyze 連携モジュールをインポートできる."""
        from strategy.integration import TechnicalSignalProvider

        assert TechnicalSignalProvider is not None

    def test_正常系_strategyからfactor連携モジュールをインポート(self) -> None:
        """strategy から factor 連携モジュールをインポートできる."""
        from strategy.integration import FactorBasedRiskCalculator

        assert FactorBasedRiskCalculator is not None

    def test_正常系_統合ビルダーをインポート(self) -> None:
        """IntegratedStrategyBuilder をインポートできる."""
        from strategy.integration import IntegratedStrategyBuilder

        assert IntegratedStrategyBuilder is not None
