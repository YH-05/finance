"""Analyze package for financial data analysis.

This package provides analysis tools for financial data including:
- Technical analysis (indicators, patterns, signals)
- Statistical analysis (descriptive statistics, correlation)
- Sector analysis (sector performance, rotation)
- Earnings analysis (earnings calendar, estimates)
- Fundamental analysis (planned)
- Quantitative analysis (planned)

Submodules
----------
technical
    Technical analysis module (moving averages, RSI, MACD, etc.)
statistics
    Statistical analysis module (descriptive statistics, correlation)
sector
    Sector analysis module (sector performance, ETF tracking)
earnings
    Earnings calendar and earnings data analysis
"""

from analyze import sector
from analyze.earnings import EarningsCalendar, EarningsData, get_upcoming_earnings
from analyze.statistics.types import (
    CorrelationMethod,
    CorrelationResult,
    DescriptiveStats,
)
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
    "BollingerBandsParams",
    "BollingerBandsResult",
    "CorrelationMethod",
    "CorrelationResult",
    "DescriptiveStats",
    "EMAParams",
    "EarningsCalendar",
    "EarningsData",
    "MACDParams",
    "MACDResult",
    "RSIParams",
    "ReturnParams",
    "SMAParams",
    "VolatilityParams",
    "get_upcoming_earnings",
    "sector",
]

__version__ = "0.1.0"
