"""factors package - Factor implementations for various asset classes.

This package contains factor implementations organized by category:
- macro: Macroeconomic factors (interest rates, inflation, etc.)
- price: Price-based factors (momentum, etc.)
- quality: Quality factors (ROE, ROA, ROIC, etc.)
- size: Size factors (market cap, revenue, total assets)
- value: Value factors (PER, PBR, dividend yield, EV/EBITDA)
"""

from .price import MomentumFactor
from .quality import QualityFactor, ROICFactor, ROICTransitionLabeler
from .size import SizeFactor
from .value import ValueFactor

__all__ = [
    "MomentumFactor",
    "QualityFactor",
    "ROICFactor",
    "ROICTransitionLabeler",
    "SizeFactor",
    "ValueFactor",
]
