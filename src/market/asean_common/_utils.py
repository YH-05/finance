"""Internal utility helpers for ASEAN common module — backward-compatibility shim.

.. deprecated::
    This module has been renamed to ``market.market_common._utils``.
    All symbols are re-exported here for backward compatibility.
    Please update your imports to use ``market.market_common._utils`` directly.
"""

from market.market_common._utils import (
    _coerce_optional_int,
    _coerce_optional_str,
    _is_nan,
)

__all__ = [
    "_coerce_optional_int",
    "_coerce_optional_str",
    "_is_nan",
]
