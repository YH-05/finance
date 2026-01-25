"""Date utility functions for market analysis.

This module provides date-related utilities for calculating trading periods,
market dates, and report generation dates.

Functions
---------
calculate_weekly_comment_period
    Calculate the Tuesday-to-Tuesday period for weekly comment generation.
get_previous_tuesday
    Get the most recent Tuesday on or before the given date.
get_last_tuesday
    Get the Tuesday of the previous week.
format_date_japanese
    Format a date in Japanese style.

Examples
--------
>>> from market_analysis.utils.date_utils import calculate_weekly_comment_period
>>> period = calculate_weekly_comment_period()
>>> "start" in period and "end" in period
True
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Literal

from database.utils.logging_config import get_logger

logger = get_logger(__name__)

# Tuesday is weekday 1 (Monday=0, Tuesday=1, ..., Sunday=6)
TUESDAY = 1
WEDNESDAY = 2


def get_previous_tuesday(reference_date: date) -> date:
    """Get the most recent Tuesday on or before the given date.

    Parameters
    ----------
    reference_date : date
        The reference date to find the previous Tuesday from.

    Returns
    -------
    date
        The most recent Tuesday on or before the reference date.
        If reference_date is a Tuesday, returns reference_date itself.

    Examples
    --------
    >>> from datetime import date
    >>> # Wednesday Jan 22, 2026 -> Tuesday Jan 21, 2026
    >>> get_previous_tuesday(date(2026, 1, 22))
    datetime.date(2026, 1, 21)
    >>> # Tuesday Jan 21, 2026 -> Tuesday Jan 21, 2026
    >>> get_previous_tuesday(date(2026, 1, 21))
    datetime.date(2026, 1, 21)
    """
    days_since_tuesday = (reference_date.weekday() - TUESDAY) % 7
    return reference_date - timedelta(days=days_since_tuesday)


def get_last_tuesday(reference_date: date) -> date:
    """Get the Tuesday of the previous week.

    Parameters
    ----------
    reference_date : date
        The reference date.

    Returns
    -------
    date
        The Tuesday of the week before the reference date's week.

    Examples
    --------
    >>> from datetime import date
    >>> # Wednesday Jan 22, 2026 -> Tuesday Jan 14, 2026
    >>> get_last_tuesday(date(2026, 1, 22))
    datetime.date(2026, 1, 14)
    """
    current_tuesday = get_previous_tuesday(reference_date)
    return current_tuesday - timedelta(days=7)


def calculate_weekly_comment_period(
    reference_date: date | None = None,
) -> dict[str, date]:
    """Calculate the Tuesday-to-Tuesday period for weekly comment generation.

    The weekly comment covers the period from the Tuesday of the previous week
    to the Tuesday of the current week (inclusive).

    If called on a Wednesday (the typical report generation day), it will
    calculate the period from the previous Tuesday to yesterday's Tuesday.

    Parameters
    ----------
    reference_date : date, optional
        The reference date for calculation. If None, uses today's date.
        Typically this would be a Wednesday (report generation day).

    Returns
    -------
    dict[str, date]
        Dictionary containing:
        - 'start': Start date of the period (Tuesday of previous week)
        - 'end': End date of the period (Tuesday of current week)
        - 'reference': The reference date used for calculation
        - 'report_date': The suggested report date (day after end date)

    Examples
    --------
    >>> from datetime import date
    >>> # On Wednesday Jan 22, 2026
    >>> period = calculate_weekly_comment_period(date(2026, 1, 22))
    >>> period['start']
    datetime.date(2026, 1, 14)
    >>> period['end']
    datetime.date(2026, 1, 21)
    >>> period['report_date']
    datetime.date(2026, 1, 22)
    """
    if reference_date is None:
        reference_date = date.today()

    logger.debug(
        "Calculating weekly comment period", reference_date=str(reference_date)
    )

    # Get this week's Tuesday (the end of the period)
    end_date = get_previous_tuesday(reference_date)

    # Get last week's Tuesday (the start of the period)
    start_date = end_date - timedelta(days=7)

    # Report date is typically the day after the end date (Wednesday)
    report_date = end_date + timedelta(days=1)

    period = {
        "start": start_date,
        "end": end_date,
        "reference": reference_date,
        "report_date": report_date,
    }

    logger.info(
        "Weekly comment period calculated",
        start=str(start_date),
        end=str(end_date),
        report_date=str(report_date),
    )

    return period


def format_date_japanese(
    d: date, style: Literal["full", "short", "weekday"] = "full"
) -> str:
    """Format a date in Japanese style.

    Parameters
    ----------
    d : date
        The date to format.
    style : {"full", "short", "weekday"}, default="full"
        The format style:
        - "full": "2026年1月22日(水)"
        - "short": "1/22(水)"
        - "weekday": "水"

    Returns
    -------
    str
        The formatted date string.

    Examples
    --------
    >>> from datetime import date
    >>> format_date_japanese(date(2026, 1, 22), "full")
    '2026年1月22日(水)'
    >>> format_date_japanese(date(2026, 1, 22), "short")
    '1/22(水)'
    >>> format_date_japanese(date(2026, 1, 22), "weekday")
    '水'
    """
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = weekday_names[d.weekday()]

    if style == "full":
        return f"{d.year}年{d.month}月{d.day}日({weekday})"
    elif style == "short":
        return f"{d.month}/{d.day}({weekday})"
    else:  # style == "weekday"
        return weekday


def format_date_us(d: date, style: Literal["full", "short", "mdy"] = "full") -> str:
    """Format a date in US style.

    Parameters
    ----------
    d : date
        The date to format.
    style : {"full", "short", "mdy"}, default="full"
        The format style:
        - "full": "January 22, 2026"
        - "short": "1/22"
        - "mdy": "01/22/2026"

    Returns
    -------
    str
        The formatted date string.

    Examples
    --------
    >>> from datetime import date
    >>> format_date_us(date(2026, 1, 22), "full")
    'January 22, 2026'
    >>> format_date_us(date(2026, 1, 22), "short")
    '1/22'
    >>> format_date_us(date(2026, 1, 22), "mdy")
    '01/22/2026'
    """
    if style == "full":
        return d.strftime("%B %d, %Y")
    elif style == "short":
        return f"{d.month}/{d.day}"
    else:  # style == "mdy"
        return d.strftime("%m/%d/%Y")


def get_trading_days_in_period(start: date, end: date) -> list[date]:
    """Get all trading days (weekdays) in a given period.

    Parameters
    ----------
    start : date
        Start date of the period (inclusive).
    end : date
        End date of the period (inclusive).

    Returns
    -------
    list[date]
        List of weekday dates in the period.

    Notes
    -----
    This function returns weekdays only. It does not account for market
    holidays. For accurate trading day calculation, consider using a
    market calendar library.

    Examples
    --------
    >>> from datetime import date
    >>> days = get_trading_days_in_period(date(2026, 1, 19), date(2026, 1, 23))
    >>> len(days)  # Mon, Tue, Wed, Thu, Fri
    5
    """
    trading_days = []
    current = start
    while current <= end:
        # Monday = 0, ..., Friday = 4
        if current.weekday() < 5:
            trading_days.append(current)
        current += timedelta(days=1)
    return trading_days


def parse_date(date_str: str) -> date:
    """Parse a date string in various formats.

    Parameters
    ----------
    date_str : str
        Date string to parse. Supported formats:
        - YYYY-MM-DD (e.g., "2026-01-22")
        - YYYYMMDD (e.g., "20260122")
        - MM/DD/YYYY (e.g., "01/22/2026")

    Returns
    -------
    date
        Parsed date object.

    Raises
    ------
    ValueError
        If the date string cannot be parsed.

    Examples
    --------
    >>> parse_date("2026-01-22")
    datetime.date(2026, 1, 22)
    >>> parse_date("20260122")
    datetime.date(2026, 1, 22)
    >>> parse_date("01/22/2026")
    datetime.date(2026, 1, 22)
    """
    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    msg = f"Unable to parse date '{date_str}'. Supported formats: YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY"
    raise ValueError(msg)
