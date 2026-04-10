"""Custom exception classes for the ASEAN common module — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common.errors``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common.errors`` directly.
"""

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

__all__ = [
    "AseanError",
    "AseanLookupError",
    "AseanScreenerError",
    "AseanStorageError",
    "ExchangeAPIError",
    "ExchangeError",
    "ExchangeParseError",
    "ExchangeRateLimitError",
    "ExchangeValidationError",
]
