"""Price-based factor implementations.

This module provides price-based factors including:
- ReversalFactor: Short-term reversal factor

Examples
--------
>>> from factor.factors.price import ReversalFactor
>>> factor = ReversalFactor(lookback=5)
"""

from factor.factors.price.reversal import ReversalFactor

__all__ = [
    "ReversalFactor",
]
