"""yfinance news source implementation.

This package provides functionality to fetch news from yfinance
using both Ticker (for specific symbols) and Search (for keywords) APIs.

Modules
-------
base
    Common utilities, conversion functions, retry logic, and validation.
index
    IndexNewsSource for stock market indices (^GSPC, ^DJI, etc.).
"""

from .base import (
    fetch_with_retry,
    search_news_to_article,
    ticker_news_to_article,
    validate_query,
    validate_ticker,
)
from .index import IndexNewsSource

__all__ = [
    "IndexNewsSource",
    "fetch_with_retry",
    "search_news_to_article",
    "ticker_news_to_article",
    "validate_query",
    "validate_ticker",
]
