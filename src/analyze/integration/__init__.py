"""Integration module for connecting analyze with external data sources.

This module provides integration with the market package to fetch
and analyze financial data in a unified workflow.

Classes
-------
MarketDataAnalyzer
    Main class for fetching market data and running analysis

Functions
---------
analyze_market_data
    Analyze a DataFrame of market data
fetch_and_analyze
    Convenience function to fetch and analyze market data
"""

from analyze.integration.market_integration import (
    MarketDataAnalyzer,
    analyze_market_data,
    fetch_and_analyze,
)

__all__ = [
    "MarketDataAnalyzer",
    "analyze_market_data",
    "fetch_and_analyze",
]
