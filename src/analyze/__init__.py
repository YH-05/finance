"""Analyze package for financial data analysis.

This package provides analysis tools for financial data including:
- Technical analysis (indicators, patterns, signals)
- Statistical analysis (descriptive statistics, correlation)
- Sector analysis (sector performance, rotation)
- Earnings analysis (earnings calendar, estimates)
- Returns calculation (multi-period returns, MTD, YTD)
- Visualization (charts, heatmaps, price charts)
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
returns
    Multi-period returns calculation (1D, 1W, MTD, 1M, 3M, YTD, etc.)
visualization
    Financial chart creation module (ChartBuilder, HeatmapChart, CandlestickChart, etc.)
"""

from analyze import sector
from analyze.earnings import EarningsCalendar, EarningsData, get_upcoming_earnings
from analyze.returns import (
    RETURN_PERIODS,
    TICKERS_GLOBAL_INDICES,
    TICKERS_MAG7,
    TICKERS_SECTORS,
    TICKERS_US_INDICES,
    calculate_multi_period_returns,
    calculate_return,
    fetch_topix_data,
    generate_returns_report,
)
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
    "RETURN_PERIODS",
    "TICKERS_GLOBAL_INDICES",
    "TICKERS_MAG7",
    "TICKERS_SECTORS",
    "TICKERS_US_INDICES",
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
    "calculate_multi_period_returns",
    "calculate_return",
    "fetch_topix_data",
    "generate_returns_report",
    "get_upcoming_earnings",
    "sector",
]

__version__ = "0.1.0"
