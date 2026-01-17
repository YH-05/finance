"""factors package - Factor implementations for various asset classes.

This package contains factor implementations organized by category:
- macro: Macroeconomic factors (interest rates, inflation, etc.)
- quality: Quality factors (ROIC, etc.)
- value: Value factors (PER, PBR, dividend yield, EV/EBITDA)
"""

from .quality import ROICFactor, ROICTransitionLabeler
from .value import ValueFactor

__all__ = [
    "ROICFactor",
    "ROICTransitionLabeler",
    "ValueFactor",
]
