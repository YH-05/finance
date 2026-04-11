"""ASEAN common foundation module.

Provides shared constants, types, error definitions, storage layer,
and screener integration for all ASEAN market sub-packages
(SGX, Bursa, SET, IDX, HOSE, PSE).

Public API
----------
Constants : MarketExchange, YFINANCE_SUFFIX_MAP, SCREENER_EXCHANGE_MAP,
    SCREENER_MARKET_MAP, TABLE_TICKERS, DB_PATH
Types : TickerRecord
Storage : AseanTickerStorage
Errors : AseanError, AseanStorageError, AseanScreenerError, AseanLookupError,
    ExchangeError, ExchangeAPIError, ExchangeRateLimitError,
    ExchangeParseError, ExchangeValidationError
Screener : fetch_tickers_from_screener, fetch_all_asean_tickers

Examples
--------
>>> from market.market_common import MarketExchange, TickerRecord
>>> record = TickerRecord(
...     ticker="D05",
...     name="DBS Group Holdings Ltd",
...     market=MarketExchange.SGX,
...     yfinance_suffix=".SI",
... )
>>> record.yfinance_ticker
'D05.SI'

See Also
--------
market.market_common.constants : Enum and mapping definitions.
market.market_common.types : TickerRecord dataclass.
market.market_common.storage : DuckDB storage layer.
market.market_common.screener : tradingview-screener integration.
market.market_common.errors : Exception hierarchy.
"""

from market.market_common.constants import (
    DB_PATH,
    SCREENER_EXCHANGE_MAP,
    SCREENER_MARKET_MAP,
    TABLE_TICKERS,
    YFINANCE_SUFFIX_MAP,
    MarketExchange,
)
from market.market_common.errors import (
    AseanError,
    AseanLookupError,
    AseanScreenerError,
    AseanStorageError,
    ExchangeAPIError,
    ExchangeError,
    ExchangeParseError,
    ExchangeRateLimitError,
    ExchangeValidationError,
)
from market.market_common.screener import (
    fetch_all_asean_tickers,
    fetch_tickers_from_screener,
)
from market.market_common.storage import AseanTickerStorage
from market.market_common.types import ExchangeConfig, TickerRecord

__all__ = [
    "DB_PATH",
    "SCREENER_EXCHANGE_MAP",
    "SCREENER_MARKET_MAP",
    "TABLE_TICKERS",
    "YFINANCE_SUFFIX_MAP",
    "AseanError",
    "AseanLookupError",
    "AseanScreenerError",
    "AseanStorageError",
    "AseanTickerStorage",
    "ExchangeAPIError",
    "ExchangeConfig",
    "ExchangeError",
    "ExchangeParseError",
    "ExchangeRateLimitError",
    "ExchangeValidationError",
    "MarketExchange",
    "TickerRecord",
    "fetch_all_asean_tickers",
    "fetch_tickers_from_screener",
]
