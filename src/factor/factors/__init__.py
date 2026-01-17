"""factors package - Factor implementations for various asset classes.

This package contains factor implementations organized by category:
- macro: Macroeconomic factors (interest rates, inflation, etc.)
- quality: Quality factors (ROIC, etc.)
"""

from .quality import ROICFactor, ROICTransitionLabeler

__all__ = [
    "ROICFactor",
    "ROICTransitionLabeler",
]
