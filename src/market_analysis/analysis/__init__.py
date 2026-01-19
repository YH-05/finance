"""Analysis module for market data technical indicators and statistics."""

from .analyzer import Analyzer
from .correlation import CorrelationAnalyzer
from .indicators import IndicatorCalculator
from .returns import (
    RETURN_PERIODS,
    TICKERS_GLOBAL_INDICES,
    calculate_multi_period_returns,
    calculate_return,
    fetch_topix_data,
    generate_returns_report,
)

__all__ = [
    "RETURN_PERIODS",
    "TICKERS_GLOBAL_INDICES",
    "Analyzer",
    "CorrelationAnalyzer",
    "IndicatorCalculator",
    "calculate_multi_period_returns",
    "calculate_return",
    "fetch_topix_data",
    "generate_returns_report",
]
