"""market.fred - FRED (Federal Reserve Economic Data) API integration.

This package provides functionality for fetching economic indicator data
from the Federal Reserve Economic Data (FRED) service.

Classes
-------
FREDFetcher
    Main class for fetching FRED data

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
"""

from .constants import FRED_API_KEY_ENV, FRED_SERIES_PATTERN
from .fetcher import FREDFetcher

__all__ = [
    "FRED_API_KEY_ENV",
    "FRED_SERIES_PATTERN",
    "FREDFetcher",
]
