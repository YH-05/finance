"""DuckDB storage layer for ASEAN ticker master data — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common.storage``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common.storage`` directly.
"""

from market.market_common.storage import TICKER_DF_SCHEMA, AseanTickerStorage

__all__ = [
    "TICKER_DF_SCHEMA",
    "AseanTickerStorage",
]
