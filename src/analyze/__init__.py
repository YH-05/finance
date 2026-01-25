"""Analyze package for financial data analysis.

This package provides analysis tools for financial data including:
- Technical analysis (indicators, patterns, signals)
- Fundamental analysis (planned)
- Quantitative analysis (planned)

Submodules
----------
technical
    Technical analysis module (moving averages, RSI, MACD, etc.)
"""

from .technical import (
    BollingerBandsParams,
    BollingerBandsResult,
    EMAParams,
    MACDParams,
    MACDResult,
    ReturnParams,
    RSIParams,
    SMAParams,
    VolatilityParams,
)

__all__ = [
    "BollingerBandsParams",
    "BollingerBandsResult",
    "EMAParams",
    "MACDParams",
    "MACDResult",
    "RSIParams",
    "ReturnParams",
    "SMAParams",
    "VolatilityParams",
]

__version__ = "0.1.0"
