"""Constants for ASEAN common foundation module — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common.constants``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common.constants`` directly.
"""

from market.market_common.constants import (
    DB_PATH,
    SCREENER_EXCHANGE_MAP,
    SCREENER_MARKET_MAP,
    TABLE_TICKERS,
    YFINANCE_SUFFIX_MAP,
    MarketExchange,
)

# Backward-compatible alias: AseanMarket → MarketExchange
AseanMarket = MarketExchange

__all__ = [
    "DB_PATH",
    "SCREENER_EXCHANGE_MAP",
    "SCREENER_MARKET_MAP",
    "TABLE_TICKERS",
    "YFINANCE_SUFFIX_MAP",
    "AseanMarket",
    "MarketExchange",
]
