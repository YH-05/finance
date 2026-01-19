"""Earnings calendar module for fetching upcoming earnings dates.

This module provides functionality to:
- Fetch earnings dates from Yahoo Finance using yfinance
- Filter earnings within a specified time range
- Extract EPS and revenue estimates when available
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="earnings")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class EarningsData:
    """Data class representing a single earnings event.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    name : str
        Company name
    earnings_date : datetime
        Expected earnings announcement date
    eps_estimate : float | None
        Estimated earnings per share (if available)
    revenue_estimate : float | None
        Estimated revenue (if available)

    Examples
    --------
    >>> data = EarningsData(
    ...     ticker="NVDA",
    ...     name="NVIDIA Corporation",
    ...     earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
    ...     eps_estimate=0.85,
    ...     revenue_estimate=38_500_000_000,
    ... )
    >>> data.to_dict()
    {'ticker': 'NVDA', 'name': 'NVIDIA Corporation', ...}
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
            Dictionary representation of the earnings data
        """
        return {
            "ticker": self.ticker,
            "name": self.name,
            "earnings_date": self.earnings_date.strftime("%Y-%m-%d"),
            "eps_estimate": self.eps_estimate,
            "revenue_estimate": self.revenue_estimate,
        }


# =============================================================================
# Earnings Calendar Class
# =============================================================================


@dataclass
class EarningsCalendar:
    """Fetches and filters upcoming earnings dates.

    Provides functionality to retrieve earnings dates for major stocks
    and filter them based on a time range.

    Attributes
    ----------
    default_symbols : list[str]
        Default list of symbols to check (Mag7 + sector representatives)

    Examples
    --------
    >>> calendar = EarningsCalendar()
    >>> results = calendar.get_upcoming_earnings(days_ahead=14)
    >>> for r in results:
    ...     print(f"{r.ticker}: {r.earnings_date}")
    """

    default_symbols: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize default symbols if not provided."""
        if not self.default_symbols:
            self.default_symbols = self._get_default_symbols()
        logger.debug(
            "EarningsCalendar initialized",
            symbol_count=len(self.default_symbols),
        )

    @staticmethod
    def _get_default_symbols() -> list[str]:
        """Get default list of symbols (Mag7 + sector representatives).

        Returns
        -------
        list[str]
            List of ticker symbols
        """
        # Magnificent 7
        mag7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

        # Sector representatives
        sector_reps = [
            # Financials
            "JPM",
            "BAC",
            "GS",
            # Healthcare
            "JNJ",
            "UNH",
            "PFE",
            # Consumer Discretionary
            "HD",
            "NKE",
            "MCD",
            # Consumer Staples
            "PG",
            "KO",
            "WMT",
            # Industrials
            "CAT",
            "BA",
            "UPS",
            # Energy
            "XOM",
            "CVX",
            # Utilities
            "NEE",
            "DUK",
            # Materials
            "LIN",
            "APD",
            # Real Estate
            "AMT",
            "PLD",
            # Communication Services (beyond META/GOOGL)
            "DIS",
            "NFLX",
        ]

        return mag7 + sector_reps

    def get_earnings_for_symbol(
        self,
        symbol: str,
        limit: int = 100,
    ) -> EarningsData | None:
        """Get the next upcoming earnings date for a symbol.

        Parameters
        ----------
        symbol : str
            Stock ticker symbol
        limit : int, default=100
            Maximum number of earnings dates to fetch

        Returns
        -------
        EarningsData | None
            Earnings data if available, None otherwise
        """
        import yfinance as yf

        logger.debug("Fetching earnings for symbol", symbol=symbol, limit=limit)

        try:
            ticker = yf.Ticker(symbol)
            earnings_df = ticker.get_earnings_dates(limit=limit)

            if earnings_df is None or earnings_df.empty:
                logger.debug("No earnings data available", symbol=symbol)
                return None

            # Get ticker info for company name
            info = ticker.info
            company_name = info.get("shortName", symbol)

            # Find the next upcoming earnings date
            now = datetime.now(tz=timezone.utc)

            # Iterate through dates to find the next future earnings
            for idx in earnings_df.index:
                # Convert to pandas Timestamp for consistent handling
                ts = pd.Timestamp(str(idx))
                if bool(pd.isna(ts)):
                    continue
                if ts.tzinfo is None:
                    dt = ts.tz_localize(timezone.utc).to_pydatetime()
                else:
                    dt = ts.to_pydatetime()

                # Type guard: ensure dt is datetime, not NaTType
                if not isinstance(dt, datetime):
                    continue

                if dt > now:
                    row = earnings_df.loc[idx]
                    return self._create_earnings_data(symbol, company_name, dt, row)

            logger.debug("No future earnings dates found", symbol=symbol)
            return None

        except Exception as e:
            logger.warning(
                "Failed to fetch earnings",
                symbol=symbol,
                error=str(e),
            )
            return None

    def _create_earnings_data(
        self,
        symbol: str,
        company_name: str,
        earnings_date: datetime,
        row: pd.Series,
    ) -> EarningsData:
        """Create EarningsData from a DataFrame row.

        Parameters
        ----------
        symbol : str
            Stock ticker symbol
        company_name : str
            Company name
        earnings_date : datetime
            Earnings date
        row : pd.Series
            Row from earnings DataFrame

        Returns
        -------
        EarningsData
            Populated earnings data object
        """
        # Extract estimates (may be NaN)
        eps_estimate = None
        revenue_estimate = None

        if "EPS Estimate" in row.index:
            val = row["EPS Estimate"]
            if bool(pd.notna(val)):
                eps_estimate = float(val)

        if "Revenue Estimate" in row.index:
            val = row["Revenue Estimate"]
            if bool(pd.notna(val)):
                revenue_estimate = float(val)

        return EarningsData(
            ticker=symbol,
            name=company_name,
            earnings_date=earnings_date,
            eps_estimate=eps_estimate,
            revenue_estimate=revenue_estimate,
        )

    def get_upcoming_earnings(
        self,
        symbols: list[str] | None = None,
        days_ahead: int = 14,
    ) -> list[EarningsData]:
        """Get upcoming earnings within the specified time range.

        Parameters
        ----------
        symbols : list[str] | None, default=None
            List of symbols to check. If None, uses default_symbols.
        days_ahead : int, default=14
            Number of days ahead to look for earnings

        Returns
        -------
        list[EarningsData]
            List of upcoming earnings, sorted by date
        """
        if symbols is None:
            symbols = self.default_symbols

        logger.info(
            "Fetching upcoming earnings",
            symbol_count=len(symbols),
            days_ahead=days_ahead,
        )

        now = datetime.now(tz=timezone.utc)
        cutoff_date = now + timedelta(days=days_ahead)

        results: list[EarningsData] = []

        for symbol in symbols:
            earnings = self.get_earnings_for_symbol(symbol)
            if earnings is None:
                continue

            # Filter by date range
            if now < earnings.earnings_date <= cutoff_date:
                results.append(earnings)
                logger.debug(
                    "Found upcoming earnings",
                    symbol=symbol,
                    earnings_date=earnings.earnings_date.isoformat(),
                )

        # Sort by earnings date
        results.sort(key=lambda x: x.earnings_date)

        logger.info(
            "Upcoming earnings fetch completed",
            total_found=len(results),
            symbols_checked=len(symbols),
        )

        return results

    def to_json_output(
        self,
        earnings_list: list[EarningsData],
    ) -> dict[str, Any]:
        """Convert earnings list to JSON output format.

        Parameters
        ----------
        earnings_list : list[EarningsData]
            List of earnings data

        Returns
        -------
        dict[str, Any]
            JSON-serializable output
        """
        return {
            "upcoming_earnings": [e.to_dict() for e in earnings_list],
        }


# =============================================================================
# Convenience Function
# =============================================================================


def get_upcoming_earnings(
    symbols: list[str] | None = None,
    days_ahead: int = 14,
) -> dict[str, Any]:
    """Get upcoming earnings for the specified symbols.

    This is a convenience function that creates an EarningsCalendar
    and returns the results in JSON format.

    Parameters
    ----------
    symbols : list[str] | None, default=None
        List of symbols to check. If None, uses default symbols.
    days_ahead : int, default=14
        Number of days ahead to look for earnings

    Returns
    -------
    dict[str, Any]
        JSON-serializable output with upcoming earnings

    Examples
    --------
    >>> result = get_upcoming_earnings(symbols=["NVDA", "AAPL"])
    >>> print(result["upcoming_earnings"])
    [{'ticker': 'NVDA', 'name': 'NVIDIA Corporation', ...}]
    """
    logger.info(
        "Getting upcoming earnings",
        symbols=symbols,
        days_ahead=days_ahead,
    )

    calendar = EarningsCalendar()
    earnings = calendar.get_upcoming_earnings(
        symbols=symbols,
        days_ahead=days_ahead,
    )

    return calendar.to_json_output(earnings)


__all__ = [
    "EarningsCalendar",
    "EarningsData",
    "get_upcoming_earnings",
]
