"""Integration module for strategy package.

This module provides integration between the strategy package and
market, analyze, and factor packages.

Classes
-------
IntegratedStrategyBuilder
    Builds portfolio strategies using data from market, analyze, and factor packages
FactorBasedRiskCalculator
    Calculates risk metrics considering factor exposures
TechnicalSignalProvider
    Provides trading signals based on technical indicators from analyze package

Functions
---------
create_integrated_builder
    Factory function to create an IntegratedStrategyBuilder
"""

from .analyze_integration import TechnicalSignalProvider, create_signal_provider
from .builder import IntegratedStrategyBuilder, create_integrated_builder
from .factor_integration import FactorBasedRiskCalculator, create_factor_risk_calculator
from .market_integration import (
    StrategyMarketDataProvider,
    create_strategy_market_provider,
)

__all__ = [
    "FactorBasedRiskCalculator",
    "IntegratedStrategyBuilder",
    "StrategyMarketDataProvider",
    "TechnicalSignalProvider",
    "create_factor_risk_calculator",
    "create_integrated_builder",
    "create_signal_provider",
    "create_strategy_market_provider",
]
