"""Multi-period returns calculation module.

This module provides functions for calculating returns over multiple periods
including dynamic periods like MTD (Month-to-Date) and YTD (Year-to-Date).

Issue #469: 多期間騰落率計算モジュールの実装
Migrated from market_analysis.analysis.returns (Issue #956)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from analyze.config.loader import get_return_periods, get_symbols
from utils_core.logging import get_logger

logger = get_logger(__name__, module="returns")

# =============================================================================
# Constants (loaded from config/symbols.yaml)
# =============================================================================

RETURN_PERIODS: dict[str, int | str] = get_return_periods()
TICKERS_GLOBAL_INDICES: list[str] = get_symbols("indices", "global")
TICKERS_US_INDICES: list[str] = get_symbols("indices", "us")
TICKERS_MAG7: list[str] = get_symbols("mag7")
TICKERS_SECTORS: list[str] = get_symbols("sectors")


# =============================================================================
# Functions
# =============================================================================


def calculate_return(prices: pd.Series, period: int | str) -> float | None:
    """Calculate return for a single period.

    Parameters
    ----------
    prices : pd.Series
        Price series with DatetimeIndex
    period : int | str
        Number of business days or "mtd"/"ytd" for dynamic periods

    Returns
    -------
    float | None
        Calculated return as decimal (e.g., 0.05 for 5%), or None if insufficient data

    Raises
    ------
    ValueError
        If period is a non-positive integer

    Examples
    --------
    >>> prices = pd.Series([100.0, 101.0, 102.0], index=pd.date_range("2024-01-01", periods=3))
    >>> calculate_return(prices, period=1)
    0.00990099009900991
    """
    logger.debug("Calculating return", period=period, data_length=len(prices))

    # Handle empty series
    if prices.empty:
        logger.debug("Empty price series, returning None")
        return None

    # Drop NaN values for calculation
    clean_prices = prices.dropna()
    if clean_prices.empty:
        logger.debug("All NaN values in price series, returning None")
        return None

    # Handle integer period validation
    if isinstance(period, int):
        if period <= 0:
            msg = f"period must be positive, got {period}"
            logger.error("Invalid period", period=period, error=msg)
            raise ValueError(msg)

        # Check if we have enough data
        if len(clean_prices) <= period:
            logger.debug(
                "Insufficient data for period",
                period=period,
                data_length=len(clean_prices),
            )
            return None

        # Calculate return: (current - past) / past
        current_price = clean_prices.iloc[-1]
        past_price = clean_prices.iloc[-(period + 1)]

        if past_price == 0:
            logger.warning("Past price is zero, cannot calculate return")
            return None

        result = (current_price - past_price) / past_price
        logger.debug("Return calculated", period=period, result=result)
        return float(result)

    # Handle string period (mtd/ytd)
    # At this point, period must be a string since we checked for int above
    period_lower = period.lower()

    if period_lower == "mtd":
        return _calculate_mtd_return(clean_prices)
    elif period_lower == "ytd":
        return _calculate_ytd_return(clean_prices)
    else:
        msg = f"Unknown period type: {period}. Expected 'mtd' or 'ytd'"
        logger.error("Unknown period type", period=period)
        raise ValueError(msg)


def _calculate_mtd_return(prices: pd.Series) -> float | None:
    """Calculate month-to-date return.

    Parameters
    ----------
    prices : pd.Series
        Price series with DatetimeIndex

    Returns
    -------
    float | None
        MTD return or None if insufficient data
    """
    if prices.empty:
        return None

    # Get the current date's month
    current_date = prices.index[-1]
    current_month = current_date.month
    current_year = current_date.year

    # Find the first price of the current month
    month_start_mask = (prices.index.month == current_month) & (
        prices.index.year == current_year
    )
    month_prices = prices[month_start_mask]

    if month_prices.empty or len(month_prices) < 1:
        logger.debug("No data for current month")
        return None

    month_start_price = month_prices.iloc[0]
    current_price = prices.iloc[-1]

    if month_start_price == 0:
        logger.warning("Month start price is zero")
        return None

    result = (current_price - month_start_price) / month_start_price
    logger.debug("MTD return calculated", result=result)
    return float(result)


def _calculate_ytd_return(prices: pd.Series) -> float | None:
    """Calculate year-to-date return.

    Parameters
    ----------
    prices : pd.Series
        Price series with DatetimeIndex

    Returns
    -------
    float | None
        YTD return or None if insufficient data
    """
    if prices.empty:
        return None

    # Get the current date's year
    current_date = prices.index[-1]
    current_year = current_date.year

    # Find the first price of the current year
    year_start_mask = prices.index.year == current_year
    year_prices = prices[year_start_mask]

    if year_prices.empty or len(year_prices) < 1:
        logger.debug("No data for current year")
        return None

    year_start_price = year_prices.iloc[0]
    current_price = prices.iloc[-1]

    if year_start_price == 0:
        logger.warning("Year start price is zero")
        return None

    result = (current_price - year_start_price) / year_start_price
    logger.debug("YTD return calculated", result=result)
    return float(result)


def calculate_multi_period_returns(prices: pd.Series) -> dict[str, float | None]:
    """Calculate returns for all periods in RETURN_PERIODS.

    Parameters
    ----------
    prices : pd.Series
        Price series with DatetimeIndex

    Returns
    -------
    dict[str, float | None]
        Dictionary mapping period names to returns (None if insufficient data)

    Examples
    --------
    >>> prices = pd.Series([100.0, 101.0, 102.0], index=pd.date_range("2024-01-01", periods=3))
    >>> result = calculate_multi_period_returns(prices)
    >>> "1D" in result
    True
    """
    logger.debug("Calculating multi-period returns", data_length=len(prices))

    results: dict[str, float | None] = {}

    for period_name, period_value in RETURN_PERIODS.items():
        try:
            result = calculate_return(prices, period_value)
            results[period_name] = result
            logger.debug(
                "Period return calculated",
                period_name=period_name,
                result=result,
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to calculate period return",
                period_name=period_name,
                error=str(e),
            )
            results[period_name] = None

    logger.info(
        "Multi-period returns calculated",
        total_periods=len(results),
        valid_results=sum(1 for v in results.values() if v is not None),
    )
    return results


def fetch_topix_data(
    start: str | datetime | None = None,
    end: str | datetime | None = None,
) -> pd.DataFrame | None:
    """Fetch TOPIX data with fallback to 1306.T ETF.

    Attempts to fetch ^TOPX first, falling back to 1306.T if unavailable.

    Parameters
    ----------
    start : str | datetime | None
        Start date for data fetch
    end : str | datetime | None
        End date for data fetch

    Returns
    -------
    pd.DataFrame | None
        OHLCV DataFrame or None if both sources fail

    Examples
    --------
    >>> # This would fetch actual data from yfinance
    >>> # df = fetch_topix_data(start="2024-01-01", end="2024-12-31")
    """
    logger.debug("Fetching TOPIX data", start=start, end=end)

    # Try ^TOPX first
    try:
        logger.debug("Attempting to fetch ^TOPX")
        df = yf.download("^TOPX", start=start, end=end, progress=False)

        if df is not None and not df.empty:
            logger.info("Successfully fetched ^TOPX data", rows=len(df))
            return df

        logger.debug("^TOPX returned empty data")
    except Exception as e:
        logger.warning("Failed to fetch ^TOPX", error=str(e))

    # Fallback to 1306.T (TOPIX ETF)
    try:
        logger.debug("Attempting to fetch 1306.T (fallback)")
        df = yf.download("1306.T", start=start, end=end, progress=False)

        if df is not None and not df.empty:
            logger.info("Successfully fetched 1306.T data (fallback)", rows=len(df))
            return df

        logger.debug("1306.T returned empty data")
    except Exception as e:
        logger.warning("Failed to fetch 1306.T", error=str(e))

    logger.error("Failed to fetch TOPIX data from both sources")
    return None


def generate_returns_report(as_of: datetime | None = None) -> dict[str, Any]:
    """Generate comprehensive returns report.

    Parameters
    ----------
    as_of : datetime | None
        Reference datetime for the report. Defaults to current time.

    Returns
    -------
    dict[str, Any]
        Report with structure:
        {
            "as_of": "2026-01-19T16:00:00",
            "indices": [...],
            "mag7": [...],
            "sectors": [...],
            "global_indices": [...]
        }

    Examples
    --------
    >>> # report = generate_returns_report()
    >>> # "indices" in report
    True
    """
    logger.info("Generating returns report")

    # Set as_of time
    report_time = as_of if as_of else datetime.now()
    as_of_str = report_time.isoformat()

    logger.debug("Report as_of time", as_of=as_of_str)

    # Calculate returns for each category
    indices_data = _fetch_and_calculate_returns(TICKERS_US_INDICES, "indices")
    mag7_data = _fetch_and_calculate_returns(TICKERS_MAG7, "mag7")
    sectors_data = _fetch_and_calculate_returns(TICKERS_SECTORS, "sectors")
    global_indices_data = _fetch_and_calculate_returns(
        TICKERS_GLOBAL_INDICES, "global_indices"
    )

    report = {
        "as_of": as_of_str,
        "indices": indices_data,
        "mag7": mag7_data,
        "sectors": sectors_data,
        "global_indices": global_indices_data,
    }

    logger.info(
        "Returns report generated",
        indices_count=len(indices_data),
        mag7_count=len(mag7_data),
        sectors_count=len(sectors_data),
        global_indices_count=len(global_indices_data),
    )

    return report


def _fetch_and_calculate_returns(
    tickers: list[str],
    category: str,
) -> list[dict[str, Any]]:
    """Fetch price data and calculate returns for a list of tickers.

    Uses batch download with yf.download for efficiency.

    Parameters
    ----------
    tickers : list[str]
        List of ticker symbols
    category : str
        Category name for logging

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries containing ticker and returns data
    """
    logger.debug(
        "Fetching and calculating returns (batch)",
        category=category,
        ticker_count=len(tickers),
    )

    if not tickers:
        return []

    results: list[dict[str, Any]] = []

    try:
        # Batch download all tickers at once
        logger.debug("Batch downloading data", tickers=tickers, category=category)
        df = yf.download(tickers, period="6y", progress=False)

        if df is None or df.empty:
            logger.warning("No data returned for batch download", category=category)
            return []

        # Process each ticker
        for ticker in tickers:
            try:
                # Extract Close prices for this ticker
                prices: pd.Series
                if isinstance(df.columns, pd.MultiIndex):
                    # Multi-ticker download returns MultiIndex columns
                    if "Close" in df.columns.get_level_values(0):
                        close_df = df["Close"]
                        if ticker in close_df.columns:
                            ticker_data = close_df[ticker].dropna()
                            if isinstance(ticker_data, pd.DataFrame):
                                prices = ticker_data.iloc[:, 0]
                            else:
                                prices = ticker_data
                        else:
                            logger.debug(
                                "Ticker not found in batch data",
                                ticker=ticker,
                                category=category,
                            )
                            continue
                    else:
                        logger.debug(
                            "No Close column in MultiIndex",
                            ticker=ticker,
                            category=category,
                        )
                        continue
                # Single ticker case (when only 1 ticker in list)
                elif "Close" in df.columns:
                    close_data = df["Close"]
                    if isinstance(close_data, pd.DataFrame):
                        prices = close_data.iloc[:, 0].dropna()
                    else:
                        prices = close_data.dropna()
                else:
                    logger.warning("No Close column found", ticker=ticker)
                    continue

                if prices.empty:
                    logger.debug("Empty price data after dropna", ticker=ticker)
                    continue

                # Calculate multi-period returns
                returns = calculate_multi_period_returns(prices)

                result = {
                    "ticker": ticker,
                    **returns,
                }
                results.append(result)

                logger.debug(
                    "Returns calculated for ticker",
                    ticker=ticker,
                    valid_periods=sum(1 for v in returns.values() if v is not None),
                )

            except Exception as e:
                logger.warning(
                    "Failed to process ticker",
                    ticker=ticker,
                    category=category,
                    error=str(e),
                )
                continue

    except Exception as e:
        logger.error(
            "Batch download failed",
            category=category,
            error=str(e),
            exc_info=True,
        )
        return []

    logger.debug(
        "Category returns calculation completed",
        category=category,
        processed_count=len(results),
        total_tickers=len(tickers),
    )

    return results
