"""Yahoo Finance data fetching module.

This module provides the YFinanceFetcher class for fetching market data
from Yahoo Finance using the yfinance library.

Classes
-------
YFinanceFetcher
    Data fetcher using Yahoo Finance API

Examples
--------
>>> from market.yfinance import YFinanceFetcher
>>> fetcher = YFinanceFetcher()
>>> results = fetcher.fetch(FetchOptions(symbols=["AAPL"]))
"""

from market.errors import DataFetchError, ErrorCode, ValidationError
from market.yfinance.fetcher import YFinanceFetcher
from market.yfinance.types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)

__all__ = [
    "CacheConfig",
    "DataFetchError",
    "DataSource",
    "ErrorCode",
    "FetchOptions",
    "Interval",
    "MarketDataResult",
    "RetryConfig",
    "ValidationError",
    "YFinanceFetcher",
]
