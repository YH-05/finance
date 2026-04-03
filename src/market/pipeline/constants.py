"""Constants for the pipeline persistence layer.

This module defines database name constants, environment variable names,
SQLite table name constants, and default values for the pipeline package.
All constants use ``Final`` to prevent accidental mutation.

Databases managed
-----------------
- ``nasdaq_calendar`` -- NASDAQ earnings calendar data
- ``sec_edgar`` -- SEC EDGAR financial statement data
- ``yfinance`` -- Yahoo Finance daily price data

Tables managed
--------------
- ``nc_earnings_calendar`` -- NASDAQ earnings calendar records
- ``nc_collection_queue`` -- Collection task queue for NASDAQ calendar
- ``se_financial_statements`` -- SEC EDGAR financial statement records
- ``yf_daily_prices`` -- Yahoo Finance daily OHLCV price records

See Also
--------
market.alphavantage.storage_constants : Reference implementation pattern.
market.pipeline.models : Record types that correspond to these tables.
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. Database name constants
# ---------------------------------------------------------------------------

NASDAQ_CALENDAR_DB_NAME: Final[str] = "nasdaq_calendar"
"""Default database name for NASDAQ earnings calendar data.

Used as the second argument to ``get_db_path()`` when resolving the
default database path. The resulting file is ``nasdaq_calendar.db``.
"""

SEC_EDGAR_DB_NAME: Final[str] = "sec_edgar"
"""Default database name for SEC EDGAR financial statement data.

Used as the second argument to ``get_db_path()`` when resolving the
default database path. The resulting file is ``sec_edgar.db``.
"""

YFINANCE_DB_NAME: Final[str] = "yfinance"
"""Default database name for Yahoo Finance daily price data.

Used as the second argument to ``get_db_path()`` when resolving the
default database path. The resulting file is ``yfinance.db``.
"""

# ---------------------------------------------------------------------------
# 2. Environment variable names
# ---------------------------------------------------------------------------

PIPELINE_NASDAQ_DB_PATH_ENV: Final[str] = "PIPELINE_NASDAQ_DB_PATH"
"""Environment variable name for overriding the NASDAQ calendar SQLite path.

When set, this takes precedence over the default path resolved by
``get_db_path("sqlite", NASDAQ_CALENDAR_DB_NAME)``.
"""

PIPELINE_SEC_EDGAR_DB_PATH_ENV: Final[str] = "PIPELINE_SEC_EDGAR_DB_PATH"
"""Environment variable name for overriding the SEC EDGAR SQLite path.

When set, this takes precedence over the default path resolved by
``get_db_path("sqlite", SEC_EDGAR_DB_NAME)``.
"""

PIPELINE_YFINANCE_DB_PATH_ENV: Final[str] = "PIPELINE_YFINANCE_DB_PATH"
"""Environment variable name for overriding the yfinance SQLite path.

When set, this takes precedence over the default path resolved by
``get_db_path("sqlite", YFINANCE_DB_NAME)``.
"""

# ---------------------------------------------------------------------------
# 3. SQLite table names
# ---------------------------------------------------------------------------

TABLE_NC_EARNINGS_CALENDAR: Final[str] = "nc_earnings_calendar"
"""SQLite table name for NASDAQ earnings calendar records.

Primary key: ``(symbol, report_date)``. Contains expected earnings report
dates, EPS estimates, and report timing (before/after market).
"""

TABLE_NC_COLLECTION_QUEUE: Final[str] = "nc_collection_queue"
"""SQLite table name for the NASDAQ calendar collection task queue.

Primary key: ``(symbol, queue_date)``. Tracks which tickers are pending,
in-progress, or completed for each collection run.
"""

TABLE_SE_FINANCIAL_STATEMENTS: Final[str] = "se_financial_statements"
"""SQLite table name for SEC EDGAR financial statement records.

Primary key: ``(symbol, fiscal_date_ending, statement_type, report_type)``.
Contains income statement, balance sheet, and cash flow data sourced from
SEC EDGAR XBRL filings.
"""

TABLE_YF_DAILY_PRICES: Final[str] = "yf_daily_prices"
"""SQLite table name for Yahoo Finance daily OHLCV price records.

Primary key: ``(symbol, date)``. Contains open, high, low, close,
adjusted_close, and volume for each trading day.
"""

# ---------------------------------------------------------------------------
# 4. Default values
# ---------------------------------------------------------------------------

AV_DEFAULT_DAILY_BUDGET: Final[int] = 25
"""Default daily API-call budget for AlphaVantage within the pipeline.

The free-tier Alpha Vantage plan allows 25 requests per day. This constant
is used as the default ``daily_budget`` parameter when constructing pipeline
runs that incorporate Alpha Vantage data collection.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "AV_DEFAULT_DAILY_BUDGET",
    "NASDAQ_CALENDAR_DB_NAME",
    "PIPELINE_NASDAQ_DB_PATH_ENV",
    "PIPELINE_SEC_EDGAR_DB_PATH_ENV",
    "PIPELINE_YFINANCE_DB_PATH_ENV",
    "SEC_EDGAR_DB_NAME",
    "TABLE_NC_COLLECTION_QUEUE",
    "TABLE_NC_EARNINGS_CALENDAR",
    "TABLE_SE_FINANCIAL_STATEMENTS",
    "TABLE_YF_DAILY_PRICES",
    "YFINANCE_DB_NAME",
]
