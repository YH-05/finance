"""market.fred - FRED (Federal Reserve Economic Data) API integration.

This package provides functionality for fetching economic indicator data
from the Federal Reserve Economic Data (FRED) service.

Classes
-------
FREDFetcher
    Main class for fetching FRED data
HistoricalCache
    Local cache manager for FRED historical data

Constants
---------
FRED_API_KEY_ENV
    Environment variable name for the API key
FRED_SERIES_PATTERN
    Regex pattern for valid FRED series IDs

Examples
--------
>>> from market.fred import FREDFetcher
>>> from market.fred.types import FetchOptions
>>>
>>> fetcher = FREDFetcher()  # Uses FRED_API_KEY env var
>>> options = FetchOptions(symbols=["GDP", "CPIAUCSL"])
>>> results = fetcher.fetch(options)

For historical data caching:
>>> from market.fred import HistoricalCache
>>>
>>> cache = HistoricalCache()
>>> cache.sync_series("DGS10")
>>> df = cache.get_series_df("DGS10")
"""

from .constants import FRED_API_KEY_ENV, FRED_SERIES_PATTERN
from .fetcher import FREDFetcher
from .historical_cache import HistoricalCache

__all__ = [
    "FRED_API_KEY_ENV",
    "FRED_SERIES_PATTERN",
    "FREDFetcher",
    "HistoricalCache",
]
