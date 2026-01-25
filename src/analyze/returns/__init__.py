"""Returns calculation module.

This module provides functions for calculating returns over multiple periods
including dynamic periods like MTD (Month-to-Date) and YTD (Year-to-Date).
"""

from analyze.returns.returns import (
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

__all__ = [
    "RETURN_PERIODS",
    "TICKERS_GLOBAL_INDICES",
    "TICKERS_MAG7",
    "TICKERS_SECTORS",
    "TICKERS_US_INDICES",
    "calculate_multi_period_returns",
    "calculate_return",
    "fetch_topix_data",
    "generate_returns_report",
]
