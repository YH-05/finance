"""tradingview-screener integration for ASEAN ticker fetching — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common.screener``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common.screener`` directly.
"""

from market.market_common.screener import (
    _df_to_ticker_records,
    _extract_ticker_symbol,
    _query_screener,
    fetch_all_asean_tickers,
    fetch_tickers_from_screener,
)

__all__ = [
    "_df_to_ticker_records",
    "_extract_ticker_symbol",
    "_query_screener",
    "fetch_all_asean_tickers",
    "fetch_tickers_from_screener",
]
