"""Analyze package for financial data analysis.

This package provides analysis tools for financial data including:
- Technical analysis (indicators, patterns, signals)
- Sector analysis (sector performance, rotation)
- Fundamental analysis (planned)
- Quantitative analysis (planned)

Submodules
----------
technical
    Technical analysis module (moving averages, RSI, MACD, etc.)
sector
    Sector analysis module (sector performance, ETF tracking)
"""

from analyze import sector
from analyze.technical import (
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
    # Technical analysis
    "BollingerBandsParams",
    "BollingerBandsResult",
    "EMAParams",
    "MACDParams",
    "MACDResult",
    "RSIParams",
    "ReturnParams",
    "SMAParams",
    "VolatilityParams",
    # Sector analysis
    "sector",
]

__version__ = "0.1.0"
