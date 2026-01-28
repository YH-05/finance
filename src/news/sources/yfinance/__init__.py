"""yfinance news source implementation.

This package provides functionality to fetch news from yfinance
using both Ticker (for specific symbols) and Search (for keywords) APIs.

Modules
-------
base
    Common utilities, conversion functions, retry logic, and validation.
commodity
    CommodityNewsSource for commodity futures (GC=F, CL=F, etc.).
index
    IndexNewsSource for stock market indices (^GSPC, ^DJI, etc.).
sector
    SectorNewsSource for sector ETFs (XLF, XLK, etc.).
stock
    StockNewsSource for individual stocks (MAG7 and sector representatives).
"""

from .base import (
    fetch_with_retry,
    search_news_to_article,
    ticker_news_to_article,
    validate_query,
    validate_ticker,
)
from .commodity import CommodityNewsSource
from .index import IndexNewsSource
from .sector import SectorNewsSource
from .stock import StockNewsSource

__all__ = [
    "CommodityNewsSource",
    "IndexNewsSource",
    "SectorNewsSource",
    "StockNewsSource",
    "fetch_with_retry",
    "search_news_to_article",
    "ticker_news_to_article",
    "validate_query",
    "validate_ticker",
]
