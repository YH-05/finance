"""Integration module for factor package.

This module provides integration between factor package and other
packages such as market and analyze.

Submodules
----------
market_integration
    Integration with market package for data fetching
analyze_integration
    Integration with analyze package for technical analysis
"""

from factor.integration.analyze_integration import (
    EnhancedFactorAnalyzer,
    calculate_factor_with_indicators,
    create_enhanced_analyzer,
)
from factor.integration.market_integration import (
    MarketDataProvider,
    create_market_provider,
)

__all__ = [
    "EnhancedFactorAnalyzer",
    "MarketDataProvider",
    "calculate_factor_with_indicators",
    "create_enhanced_analyzer",
    "create_market_provider",
]
