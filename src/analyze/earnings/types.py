"""Type definitions for earnings analysis module.

This module provides data classes for earnings calendar analysis including:
- EarningsData: Represents a single earnings event with estimates
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class EarningsData:
    """Data class representing a single earnings event.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g., "AAPL", "NVDA")
    name : str
        Company name (e.g., "Apple Inc.", "NVIDIA Corporation")
    earnings_date : datetime
        Expected earnings announcement date (timezone-aware recommended)
    eps_estimate : float | None, default=None
        Estimated earnings per share (if available)
    revenue_estimate : float | None, default=None
        Estimated revenue in dollars (if available)

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> data = EarningsData(
    ...     ticker="NVDA",
    ...     name="NVIDIA Corporation",
    ...     earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
    ...     eps_estimate=0.85,
    ...     revenue_estimate=38_500_000_000,
    ... )
    >>> data.ticker
    'NVDA'
    >>> data.to_dict()
    {'ticker': 'NVDA', 'name': 'NVIDIA Corporation', ...}

    Notes
    -----
    This class is designed for compatibility with the original
    ``market_analysis.analysis.earnings.EarningsData`` class.
    The ``to_dict()`` method formats dates as ISO 8601 strings
    for JSON serialization.
    """

    ticker: str
    name: str
    earnings_date: datetime
    eps_estimate: float | None = None
    revenue_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the earnings data with the following keys:
            - ticker: Stock ticker symbol
            - name: Company name
            - earnings_date: Date formatted as "YYYY-MM-DD"
            - eps_estimate: EPS estimate or None
            - revenue_estimate: Revenue estimate or None

        Examples
        --------
        >>> from datetime import datetime, timezone
        >>> data = EarningsData(
        ...     ticker="AAPL",
        ...     name="Apple Inc.",
        ...     earnings_date=datetime(2026, 1, 30, tzinfo=timezone.utc),
        ...     eps_estimate=2.15,
        ... )
        >>> result = data.to_dict()
        >>> result["ticker"]
        'AAPL'
        >>> result["earnings_date"]
        '2026-01-30'
        """
        return {
            "ticker": self.ticker,
            "name": self.name,
            "earnings_date": self.earnings_date.strftime("%Y-%m-%d"),
            "eps_estimate": self.eps_estimate,
            "revenue_estimate": self.revenue_estimate,
        }


__all__ = [
    "EarningsData",
]
