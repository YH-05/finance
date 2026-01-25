"""Earnings analysis module.

This module provides types and utilities for earnings calendar analysis,
including fetching upcoming earnings dates and filtering by time range.

Classes
-------
EarningsData
    Data class representing a single earnings event
EarningsCalendar
    Fetches and filters upcoming earnings dates

Functions
---------
get_upcoming_earnings
    Convenience function to get upcoming earnings in JSON format

Examples
--------
>>> from analyze.earnings import EarningsData, EarningsCalendar
>>> from datetime import datetime, timezone
>>> data = EarningsData(
...     ticker="NVDA",
...     name="NVIDIA Corporation",
...     earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
...     eps_estimate=0.85,
... )
>>> data.to_dict()
{'ticker': 'NVDA', 'name': 'NVIDIA Corporation', ...}

>>> calendar = EarningsCalendar()
>>> results = calendar.get_upcoming_earnings(days_ahead=14)
"""

from analyze.earnings.earnings import EarningsCalendar, get_upcoming_earnings
from analyze.earnings.types import EarningsData

__all__ = [
    "EarningsCalendar",
    "EarningsData",
    "get_upcoming_earnings",
]
