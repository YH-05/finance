"""Data providers for the strategy package.

This module provides abstract interfaces and concrete implementations
for data providers used in portfolio strategy analysis.
"""

from .market_analysis import MarketAnalysisProvider
from .protocol import DataProvider

__all__ = [
    "DataProvider",
    "MarketAnalysisProvider",
]
