"""ETF.com scraping module for market data retrieval.

This package provides tools for scraping ETF data from ETF.com,
including ETF profiles, fund flows, screener data, and classifications.

Classes
-------
TickerCollector
    Scrapes the ETF.com screener page for ETF ticker lists.
FundamentalsCollector
    Scrapes individual ETF profile pages for key-value fundamental data.
FundFlowsCollector
    Scrapes the fund flows page for daily flow data.
ETFComSession
    curl_cffi-based HTTP session with bot-blocking countermeasures.

Error Classes
-------------
ETFComError
    Base exception for all ETF.com scraping operations.
ETFComBlockedError
    Exception raised when bot-blocking is detected.
ETFComScrapingError
    Exception raised when HTML parsing / data extraction fails.
ETFComTimeoutError
    Exception raised when a page load or navigation times out.

Data Types
----------
ETFRecord
    Parsed ETF metadata record with normalised field types.
FundFlowRecord
    A single daily fund flow record for an ETF.
FundamentalsRecord
    A single ETF fundamentals record from an ETF.com profile page.
RetryConfig
    Configuration for retry behaviour with exponential backoff.
ScrapingConfig
    Configuration for ETF.com scraping behaviour.

Examples
--------
>>> from market.etfcom import TickerCollector
>>> collector = TickerCollector()
>>> df = collector.fetch()

>>> from market.etfcom import FundamentalsCollector
>>> collector = FundamentalsCollector()
>>> df = collector.fetch(tickers=["SPY", "VOO"])

>>> from market.etfcom import ETFComSession
>>> with ETFComSession() as session:
...     response = session.get_with_retry("https://www.etf.com/SPY")
"""

from market.etfcom.collectors import (
    FundamentalsCollector,
    FundFlowsCollector,
    TickerCollector,
)
from market.etfcom.errors import (
    ETFComBlockedError,
    ETFComError,
    ETFComScrapingError,
    ETFComTimeoutError,
)
from market.etfcom.session import ETFComSession
from market.etfcom.types import (
    ETFRecord,
    FundamentalsRecord,
    FundFlowRecord,
    RetryConfig,
    ScrapingConfig,
)

__all__ = [
    "ETFComBlockedError",
    "ETFComError",
    "ETFComScrapingError",
    "ETFComSession",
    "ETFComTimeoutError",
    "ETFRecord",
    "FundFlowRecord",
    "FundFlowsCollector",
    "FundamentalsCollector",
    "FundamentalsRecord",
    "RetryConfig",
    "ScrapingConfig",
    "TickerCollector",
]
