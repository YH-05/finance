"""Type definitions for the market.asean_common module — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common.types``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common.types`` directly.
"""

from market.market_common.types import ExchangeConfig, TickerRecord

__all__ = [
    "ExchangeConfig",
    "TickerRecord",
]
