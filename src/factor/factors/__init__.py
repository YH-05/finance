"""factors package - Factor implementations for various asset classes.

This package contains factor implementations organized by category:
- macro: Macroeconomic factors (interest rates, inflation, etc.)
- price: Price-based factors (momentum, etc.)
- quality: Quality factors (ROIC, etc.)
"""

from .price import MomentumFactor
from .quality import ROICFactor, ROICTransitionLabeler

__all__ = [
    "MomentumFactor",
    "ROICFactor",
    "ROICTransitionLabeler",
]
