"""NSE (National Stock Exchange of India) data retrieval module.

This package provides tools for fetching market data from the
NSE India website (https://www.nseindia.com).

NSE uses a cookie-based session mechanism: a valid session cookie must be
obtained by visiting the home page before any API call is made.

Modules
-------
constants : API URLs, headers, and configuration defaults.
errors : Exception hierarchy for NSE API operations.
types : Configuration dataclasses, Enums, and data record types.
session : HTTP session with Cookie lifecycle management.
collectors : Data collector implementations.
parsers : Response parsers and numeric cleaning utilities.

Public API
----------
NseSession
    httpx-based HTTP session with Cookie lifecycle management.
NseConfig
    Configuration for NSE API HTTP behaviour.
RetryConfig
    Configuration for retry behaviour with exponential backoff.

Collectors
----------
CorporateCollector
    Collector for NSE corporate data (financial results, event calendar).
IndicesCollector
    Collector for NSE index constituent data and market status.
QuoteCollector
    Collector for NSE equity quote data.
StockListCollector
    Collector for NSE equity stock list and pre-open session data.

Enums
-----
NseIndex
    Major NSE index identifiers.

Data Records
------------
CorporateEvent
    A corporate event from the NSE event calendar.
FinancialResult
    A financial result record from NSE corporate filings.
IndexConstituent
    A single constituent stock within an NSE index.
MarketStatus
    Market status for a single market segment.
ShareholdingPattern
    A shareholding breakdown record (promoter/FII/DII/public) from NSE.
StockQuote
    A single stock quote from NSE equity market.

Error Classes
-------------
NseError
    Base exception for all NSE API operations.
NseAPIError
    Exception for HTTP 4xx/5xx error responses.
NseRateLimitError
    Exception for rate limit (HTTP 429) responses.
NseCookieError
    Exception for expired/invalid NSE session cookies.
NseParseError
    Exception for response parsing failures.
NseValidationError
    Exception for data validation failures.

Parser Functions
----------------
clean_indian_number
    Clean and convert NSE Indian-formatted number string to float.
clean_price
    Clean and convert NSE price string to float.
clean_volume
    Clean and convert NSE volume string to int.
parse_all_indices
    Parse NSE all-indices summary JSON to DataFrame.
parse_event_calendar
    Parse NSE event-calendar JSON to list of CorporateEvent.
parse_financial_results
    Parse NSE results-comparision JSON to list of FinancialResult.
parse_index_constituents
    Parse NSE equity-stockIndices JSON to list of IndexConstituent.
parse_market_status
    Parse NSE marketStatus JSON to list of MarketStatus.
parse_preopen_data
    Parse NSE pre-open session JSON to DataFrame.
parse_quote_response
    Parse NSE quote-equity JSON to StockQuote.
parse_shareholding_pattern
    Parse NSE corporates-shareholding JSON to list of ShareholdingPattern.
parse_stock_list_csv
    Parse NSE EQUITY_L.csv content to DataFrame.
"""

from market.nse.collectors import (
    CorporateCollector,
    IndicesCollector,
    QuoteCollector,
    StockListCollector,
)
from market.nse.errors import (
    NseAPIError,
    NseCookieError,
    NseError,
    NseParseError,
    NseRateLimitError,
    NseValidationError,
)
from market.nse.parsers import (
    clean_indian_number,
    clean_price,
    clean_volume,
    parse_all_indices,
    parse_event_calendar,
    parse_financial_results,
    parse_index_constituents,
    parse_market_status,
    parse_preopen_data,
    parse_quote_response,
    parse_shareholding_pattern,
    parse_stock_list_csv,
)
from market.nse.session import NseSession
from market.nse.types import (
    CorporateEvent,
    FinancialResult,
    IndexConstituent,
    MarketStatus,
    NseConfig,
    NseIndex,
    RetryConfig,
    ShareholdingPattern,
    StockQuote,
)

__all__ = [
    "CorporateCollector",
    "CorporateEvent",
    "FinancialResult",
    "IndexConstituent",
    "IndicesCollector",
    "MarketStatus",
    "NseAPIError",
    "NseConfig",
    "NseCookieError",
    "NseError",
    "NseIndex",
    "NseParseError",
    "NseRateLimitError",
    "NseSession",
    "NseValidationError",
    "QuoteCollector",
    "RetryConfig",
    "ShareholdingPattern",
    "StockListCollector",
    "StockQuote",
    "clean_indian_number",
    "clean_price",
    "clean_volume",
    "parse_all_indices",
    "parse_event_calendar",
    "parse_financial_results",
    "parse_index_constituents",
    "parse_market_status",
    "parse_preopen_data",
    "parse_quote_response",
    "parse_shareholding_pattern",
    "parse_stock_list_csv",
]
