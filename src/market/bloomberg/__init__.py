"""Bloomberg data fetching module for market package.

This module provides Bloomberg Terminal integration for market data:
- Historical price data
- Reference data
- Financial data
- News data
- Field information
- Identifier conversion
- Index constituents

Example
-------
>>> from market.bloomberg import BloombergFetcher, BloombergFetchOptions
>>> fetcher = BloombergFetcher()
>>> options = BloombergFetchOptions(
...     securities=["AAPL US Equity"],
...     fields=["PX_LAST", "PX_VOLUME"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> results = fetcher.get_historical_data(options)
"""

from market.bloomberg.errors import (
    BloombergConnectionError,
    BloombergDataError,
    BloombergError,
    BloombergSessionError,
    BloombergValidationError,
    ErrorCode,
)
from market.bloomberg.fetcher import BloombergFetcher
from market.bloomberg.types import (
    BloombergDataResult,
    BloombergFetchOptions,
    DataSource,
    FieldInfo,
    IDType,
    NewsStory,
    OverrideOption,
    Periodicity,
)

__all__ = [
    "BloombergConnectionError",
    "BloombergDataError",
    "BloombergDataResult",
    "BloombergError",
    "BloombergFetchOptions",
    "BloombergFetcher",
    "BloombergSessionError",
    "BloombergValidationError",
    "DataSource",
    "ErrorCode",
    "FieldInfo",
    "IDType",
    "NewsStory",
    "OverrideOption",
    "Periodicity",
]
