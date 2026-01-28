"""yfinance news source implementation.

This package provides functionality to fetch news from yfinance
using both Ticker (for specific symbols) and Search (for keywords) APIs.

Modules
-------
base
    Common utilities, conversion functions, retry logic, and validation.
index
    IndexNewsSource for stock market indices (^GSPC, ^DJI, etc.).
sector
    SectorNewsSource for sector ETFs (XLF, XLK, etc.).
"""

from .base import (
    fetch_with_retry,
    search_news_to_article,
    ticker_news_to_article,
    validate_query,
    validate_ticker,
)
from .index import IndexNewsSource
from .sector import SectorNewsSource

__all__ = [
    "IndexNewsSource",
    "SectorNewsSource",
    "fetch_with_retry",
    "search_news_to_article",
    "ticker_news_to_article",
    "validate_query",
    "validate_ticker",
]
