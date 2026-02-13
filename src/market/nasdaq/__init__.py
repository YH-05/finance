"""NASDAQ Stock Screener module for market data retrieval.

This package provides tools for fetching stock screening data from the
NASDAQ Stock Screener API (https://api.nasdaq.com/api/screener/stocks).

Modules
-------
collector : ScreenerCollector (DataCollector ABC) for stock screening data.
constants : API URLs, headers, and configuration defaults.
errors : Exception hierarchy for NASDAQ API operations.
parser : JSON response parser and numeric cleaning utilities.
session : NasdaqSession with bot-blocking countermeasures.
types : Filter enums, configuration dataclasses, and type aliases.

Public API
----------
ScreenerCollector
    Collector for NASDAQ Stock Screener data (DataCollector ABC).
NasdaqSession
    curl_cffi-based HTTP session with bot-blocking countermeasures.
ScreenerFilter
    Filter conditions for the NASDAQ Stock Screener API.
NasdaqConfig
    Configuration for NASDAQ Stock Screener HTTP behaviour.
RetryConfig
    Configuration for retry behaviour with exponential backoff.

Enums
-----
Exchange, MarketCap, Sector, Recommendation, Region, Country
    Filter enums for the NASDAQ Screener API.

Error Classes
-------------
NasdaqError
    Base exception for all NASDAQ API operations.
NasdaqAPIError
    Exception raised when the NASDAQ API returns an error response.
NasdaqRateLimitError
    Exception raised when the NASDAQ API rate limit is exceeded.
NasdaqParseError
    Exception raised when NASDAQ API response parsing fails.

Data Types
----------
StockRecord
    A single stock record from the NASDAQ Screener API response.
FilterCategory
    Type alias for filter category Enum classes.

Examples
--------
>>> from market.nasdaq import ScreenerCollector, ScreenerFilter, Exchange
>>> collector = ScreenerCollector()
>>> df = collector.fetch(filter=ScreenerFilter(exchange=Exchange.NASDAQ))
"""

from market.nasdaq.collector import ScreenerCollector
from market.nasdaq.errors import (
    NasdaqAPIError,
    NasdaqError,
    NasdaqParseError,
    NasdaqRateLimitError,
)
from market.nasdaq.session import NasdaqSession
from market.nasdaq.types import (
    Country,
    Exchange,
    FilterCategory,
    MarketCap,
    NasdaqConfig,
    Recommendation,
    Region,
    RetryConfig,
    ScreenerFilter,
    Sector,
    StockRecord,
)

__all__ = [
    "Country",
    "Exchange",
    "FilterCategory",
    "MarketCap",
    "NasdaqAPIError",
    "NasdaqConfig",
    "NasdaqError",
    "NasdaqParseError",
    "NasdaqRateLimitError",
    "NasdaqSession",
    "Recommendation",
    "Region",
    "RetryConfig",
    "ScreenerCollector",
    "ScreenerFilter",
    "Sector",
    "StockRecord",
]
