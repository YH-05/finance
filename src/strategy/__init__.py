"""strategy package.

This package provides portfolio strategy analysis tools including:
- Risk calculation and metrics
- Portfolio optimization
- Result formatting and output
- Portfolio visualization
- Integration with market, analyze, and factor packages
"""

from .integration import (
    FactorBasedRiskCalculator,
    IntegratedStrategyBuilder,
    StrategyMarketDataProvider,
    TechnicalSignalProvider,
    create_factor_risk_calculator,
    create_integrated_builder,
    create_signal_provider,
    create_strategy_market_provider,
)
from .output import ResultFormatter
from .risk import RiskCalculator, RiskMetricsResult
from .utils.logging_config import get_logger
from .visualization import ChartGenerator

__all__ = [
    "ChartGenerator",
    # Integration
    "FactorBasedRiskCalculator",
    "IntegratedStrategyBuilder",
    "ResultFormatter",
    "RiskCalculator",
    "RiskMetricsResult",
    "StrategyMarketDataProvider",
    "TechnicalSignalProvider",
    # Integration factory functions
    "create_factor_risk_calculator",
    "create_integrated_builder",
    "create_signal_provider",
    "create_strategy_market_provider",
    "get_logger",
]

__version__ = "0.1.0"
