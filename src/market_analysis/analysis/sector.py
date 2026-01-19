"""Sector analysis module.

This module provides functions for analyzing sector performance,
including ETF returns, top/bottom sector rankings, and contributor stocks.

Issue #470: セクター分析モジュールの実装 (sector.py)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd
import yfinance as yf

if TYPE_CHECKING:
    from collections.abc import Mapping

from market_analysis.analysis.returns import calculate_return
from market_analysis.utils.logging_config import get_logger

logger = get_logger(__name__, module="sector")

# =============================================================================
# Constants
# =============================================================================

SECTOR_KEYS: list[str] = [
    "basic-materials",
    "communication-services",
    "consumer-cyclical",
    "consumer-defensive",
    "energy",
    "financial-services",
    "healthcare",
    "industrials",
    "real-estate",
    "technology",
    "utilities",
]

SECTOR_ETF_MAP: dict[str, str] = {
    "basic-materials": "XLB",
    "communication-services": "XLC",
    "consumer-cyclical": "XLY",
    "consumer-defensive": "XLP",
    "energy": "XLE",
    "financial-services": "XLF",
    "healthcare": "XLV",
    "industrials": "XLI",
    "real-estate": "XLRE",
    "technology": "XLK",
    "utilities": "XLU",
}

SECTOR_NAMES: dict[str, str] = {
    "basic-materials": "Basic Materials",
    "communication-services": "Communication Services",
    "consumer-cyclical": "Consumer Discretionary",
    "consumer-defensive": "Consumer Staples",
    "energy": "Energy",
    "financial-services": "Financial Services",
    "healthcare": "Healthcare",
    "industrials": "Industrials",
    "real-estate": "Real Estate",
    "technology": "Information Technology",
    "utilities": "Utilities",
}


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class SectorContributor:
    """Represents a contributing stock within a sector.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    name : str
        Company name
    return_1w : float
        1-week return as decimal
    weight : float
        Weight in sector ETF

    Examples
    --------
    >>> contributor = SectorContributor("NVDA", "NVIDIA", 0.052, 0.15)
    >>> contributor.to_dict()
    {'ticker': 'NVDA', 'name': 'NVIDIA', 'return_1w': 0.052, 'weight': 0.15}
    """

    ticker: str
    name: str
    return_1w: float
    weight: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "name": self.name,
            "return_1w": self.return_1w,
            "weight": self.weight,
        }


@dataclass
class SectorInfo:
    """Represents sector information with performance data.

    Parameters
    ----------
    name : str
        Human-readable sector name
    key : str
        Sector key (e.g., "technology")
    etf : str
        Sector ETF ticker
    return_1w : float
        1-week return as decimal
    top_contributors : list[SectorContributor]
        List of top contributing stocks

    Examples
    --------
    >>> sector = SectorInfo("Information Technology", "technology", "XLK", 0.025, [])
    >>> sector.to_dict()
    {'name': 'Information Technology', 'etf': 'XLK', 'return_1w': 0.025, 'top_contributors': []}
    """

    name: str
    key: str
    etf: str
    return_1w: float
    top_contributors: list[SectorContributor] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "etf": self.etf,
            "return_1w": self.return_1w,
            "top_contributors": [c.to_dict() for c in self.top_contributors],
        }


@dataclass
class SectorAnalysisResult:
    """Result of sector performance analysis.

    Parameters
    ----------
    as_of : datetime
        Timestamp of analysis
    top_sectors : list[SectorInfo]
        Top performing sectors
    bottom_sectors : list[SectorInfo]
        Bottom performing sectors

    Examples
    --------
    >>> result = SectorAnalysisResult(datetime.now(), [], [])
    >>> result.to_dict()
    {'top_sectors': [], 'bottom_sectors': []}
    """

    as_of: datetime
    top_sectors: list[SectorInfo] = field(default_factory=list)
    bottom_sectors: list[SectorInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "top_sectors": [s.to_dict() for s in self.top_sectors],
            "bottom_sectors": [s.to_dict() for s in self.bottom_sectors],
        }


# =============================================================================
# Functions - Stubs for TDD (Red state)
# =============================================================================


def fetch_sector_etf_returns(period: int = 5) -> dict[str, float | None]:
    """Fetch ETF returns for all 11 sectors.

    Parameters
    ----------
    period : int, default=5
        Number of business days for return calculation (5 = 1 week)

    Returns
    -------
    dict[str, float | None]
        Dictionary mapping sector keys to returns (None if data unavailable)

    Examples
    --------
    >>> # returns = fetch_sector_etf_returns()
    >>> # returns["technology"]
    0.025
    """
    logger.debug("Fetching sector ETF returns", period=period)

    results: dict[str, float | None] = {}

    try:
        # Get all ETF tickers
        etf_tickers = list(SECTOR_ETF_MAP.values())
        tickers_str = " ".join(etf_tickers)

        logger.debug(
            "Downloading ETF data",
            tickers=etf_tickers,
            ticker_count=len(etf_tickers),
        )

        # Download all ETF data at once
        df = yf.download(tickers_str, period="1mo", progress=False)

        if df is None or df.empty:
            logger.warning("No data returned from yfinance")
            # Return dict with None values for all sectors
            for sector_key in SECTOR_KEYS:
                results[sector_key] = None
            return results

        # Process each sector
        for sector_key, etf_ticker in SECTOR_ETF_MAP.items():
            try:
                # Extract Close prices for this ETF
                prices: pd.Series
                if isinstance(df.columns, pd.MultiIndex):
                    # Multi-ticker download returns MultiIndex columns
                    if "Close" in df.columns.get_level_values(0):
                        close_data = df["Close"]
                        if etf_ticker in close_data.columns:
                            price_data = close_data[etf_ticker].dropna()
                            if isinstance(price_data, pd.DataFrame):
                                prices = price_data.iloc[:, 0]
                            else:
                                prices = price_data
                        else:
                            logger.debug(
                                "ETF ticker not found in data",
                                sector=sector_key,
                                etf=etf_ticker,
                            )
                            results[sector_key] = None
                            continue
                    else:
                        results[sector_key] = None
                        continue
                # Single ticker download
                elif "Close" in df.columns:
                    close_data = df["Close"].dropna()
                    if isinstance(close_data, pd.DataFrame):
                        prices = close_data.iloc[:, 0]
                    else:
                        prices = close_data
                else:
                    results[sector_key] = None
                    continue

                # Calculate return using returns.calculate_return
                if len(prices) > period:
                    return_value = calculate_return(prices, period)
                    results[sector_key] = return_value
                    logger.debug(
                        "Return calculated",
                        sector=sector_key,
                        etf=etf_ticker,
                        return_value=return_value,
                    )
                else:
                    logger.debug(
                        "Insufficient data for period",
                        sector=sector_key,
                        etf=etf_ticker,
                        data_length=len(prices),
                        period=period,
                    )
                    results[sector_key] = None

            except Exception as e:
                logger.warning(
                    "Failed to calculate return for sector",
                    sector=sector_key,
                    etf=etf_ticker,
                    error=str(e),
                )
                results[sector_key] = None

    except Exception as e:
        logger.error(
            "Failed to fetch sector ETF returns",
            error=str(e),
            exc_info=True,
        )
        # Return dict with None values for all sectors
        for sector_key in SECTOR_KEYS:
            results[sector_key] = None

    logger.info(
        "Sector ETF returns fetched",
        total_sectors=len(results),
        valid_returns=sum(1 for v in results.values() if v is not None),
    )

    return results


def get_top_bottom_sectors(
    returns: Mapping[str, float | None],
    n: int = 3,
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Get top and bottom N sectors by return.

    Parameters
    ----------
    returns : Mapping[str, float | None]
        Mapping of sector keys to returns
    n : int, default=3
        Number of top/bottom sectors to return

    Returns
    -------
    tuple[list[tuple[str, float]], list[tuple[str, float]]]
        Tuple of (top_sectors, bottom_sectors), each as list of (key, return) tuples

    Raises
    ------
    ValueError
        If n is not positive

    Examples
    --------
    >>> returns = {"technology": 0.05, "energy": -0.02}
    >>> # top, bottom = get_top_bottom_sectors(returns, n=1)
    >>> # top
    [("technology", 0.05)]
    """
    if n <= 0:
        msg = f"n must be positive, got {n}"
        raise ValueError(msg)

    logger.debug(
        "Getting top/bottom sectors",
        n=n,
        total_sectors=len(returns),
    )

    # Filter out None values and create sorted list
    valid_returns: list[tuple[str, float]] = [
        (key, value) for key, value in returns.items() if value is not None
    ]

    if not valid_returns:
        logger.debug("No valid returns data")
        return ([], [])

    # Sort by return value in descending order (highest first)
    sorted_returns = sorted(valid_returns, key=lambda x: x[1], reverse=True)

    # Get top N (highest returns)
    top_sectors = sorted_returns[:n]

    # Get bottom N (lowest returns) - from the end of the sorted list
    bottom_sectors = sorted_returns[-n:][::-1]  # Reverse to get worst first

    logger.debug(
        "Top/bottom sectors identified",
        top_count=len(top_sectors),
        bottom_count=len(bottom_sectors),
        top_first=top_sectors[0] if top_sectors else None,
        bottom_first=bottom_sectors[0] if bottom_sectors else None,
    )

    return (top_sectors, bottom_sectors)


def fetch_top_companies(sector_key: str) -> list[dict[str, Any]] | None:
    """Fetch top companies for a sector using yf.Sector.

    Parameters
    ----------
    sector_key : str
        Sector key (e.g., "technology")

    Returns
    -------
    list[dict[str, Any]] | None
        List of company dictionaries with symbol, name, weight
        Returns None if fetch fails

    Examples
    --------
    >>> # companies = fetch_top_companies("technology")
    >>> # companies[0]
    {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'weight': 0.15}
    """
    logger.debug("Fetching top companies", sector_key=sector_key)

    try:
        # Create yf.Sector object
        sector = yf.Sector(sector_key)

        # Get top_companies DataFrame
        top_companies_df = sector.top_companies

        if top_companies_df is None or top_companies_df.empty:
            logger.debug("No top companies data returned", sector_key=sector_key)
            return None

        # Reset index to include symbol as a column
        # yf.Sector.top_companies has symbol as index
        df_reset = top_companies_df.reset_index()

        # Normalize column names (symbol from index, weight from 'market weight')
        if "symbol" not in df_reset.columns and "index" in df_reset.columns:
            df_reset = df_reset.rename(columns={"index": "symbol"})
        if "weight" not in df_reset.columns and "market weight" in df_reset.columns:
            df_reset = df_reset.rename(columns={"market weight": "weight"})

        # Convert DataFrame to list of dictionaries
        companies: list[dict[str, Any]] = df_reset.to_dict(orient="records")

        logger.info(
            "Top companies fetched",
            sector_key=sector_key,
            company_count=len(companies),
        )

        return companies

    except Exception as e:
        logger.warning(
            "Failed to fetch top companies",
            sector_key=sector_key,
            error=str(e),
        )
        return None


def analyze_sector_performance(
    as_of: datetime | None = None,
    n_sectors: int = 3,
) -> SectorAnalysisResult:
    """Analyze sector performance and identify top/bottom sectors with contributors.

    This is the main function that orchestrates the sector analysis workflow:
    1. Fetch ETF returns for all sectors
    2. Rank sectors by return
    3. Get top companies for each ranked sector
    4. Calculate contributor stock returns

    Parameters
    ----------
    as_of : datetime | None
        Reference datetime for the analysis. Defaults to current time.
    n_sectors : int, default=3
        Number of top/bottom sectors to include

    Returns
    -------
    SectorAnalysisResult
        Analysis result with top and bottom sectors

    Examples
    --------
    >>> # result = analyze_sector_performance()
    >>> # result.top_sectors[0].name
    'Information Technology'
    """
    logger.info("Starting sector performance analysis", n_sectors=n_sectors)

    # Set as_of time
    report_time = as_of if as_of else datetime.now()

    # Step 1: Fetch ETF returns for all sectors
    logger.debug("Step 1: Fetching ETF returns for all sectors")
    etf_returns = fetch_sector_etf_returns()

    # Step 2: Rank sectors by return
    logger.debug("Step 2: Ranking sectors by return")
    top_sectors_raw, bottom_sectors_raw = get_top_bottom_sectors(
        etf_returns, n=n_sectors
    )

    # Step 3 & 4: Build SectorInfo objects with top companies and their returns
    top_sectors = _build_sector_info_list(top_sectors_raw)
    bottom_sectors = _build_sector_info_list(bottom_sectors_raw)

    result = SectorAnalysisResult(
        as_of=report_time,
        top_sectors=top_sectors,
        bottom_sectors=bottom_sectors,
    )

    logger.info(
        "Sector performance analysis completed",
        top_sectors_count=len(result.top_sectors),
        bottom_sectors_count=len(result.bottom_sectors),
    )

    return result


def _build_sector_info_list(
    sectors_raw: list[tuple[str, float]],
) -> list[SectorInfo]:
    """Build list of SectorInfo objects with top contributors.

    Parameters
    ----------
    sectors_raw : list[tuple[str, float]]
        List of (sector_key, return) tuples

    Returns
    -------
    list[SectorInfo]
        List of SectorInfo objects with populated top_contributors
    """
    sector_infos: list[SectorInfo] = []

    for sector_key, return_value in sectors_raw:
        logger.debug(
            "Building sector info",
            sector_key=sector_key,
            return_value=return_value,
        )

        # Get sector metadata
        sector_name = SECTOR_NAMES.get(sector_key, sector_key)
        etf_ticker = SECTOR_ETF_MAP.get(sector_key, "")

        # Fetch top companies for this sector
        companies = fetch_top_companies(sector_key)
        contributors = _build_contributors(companies) if companies else []

        sector_info = SectorInfo(
            name=sector_name,
            key=sector_key,
            etf=etf_ticker,
            return_1w=return_value,
            top_contributors=contributors,
        )
        sector_infos.append(sector_info)

    return sector_infos


def _build_contributors(
    companies: list[dict[str, Any]],
    max_contributors: int = 5,
    period: int = 5,
) -> list[SectorContributor]:
    """Build list of SectorContributor objects from company data.

    Uses batch download with yf.download for efficiency.

    Parameters
    ----------
    companies : list[dict[str, Any]]
        List of company dictionaries from yf.Sector.top_companies
    max_contributors : int, default=5
        Maximum number of contributors to include
    period : int, default=5
        Number of business days for return calculation (5 = 1 week)

    Returns
    -------
    list[SectorContributor]
        List of SectorContributor objects with stock returns
    """
    if not companies:
        return []

    # Step 1: Extract symbols from companies
    target_companies = companies[:max_contributors]
    symbols = [
        company.get("symbol") or company.get("ticker", "")
        for company in target_companies
    ]
    symbols = [s for s in symbols if s]  # Remove empty strings

    if not symbols:
        return []

    # Step 2: Batch download all stock data at once
    stock_returns: dict[str, float | None] = {}
    try:
        logger.debug(
            "Batch downloading stock data for contributors",
            symbols=symbols,
            symbol_count=len(symbols),
        )

        df = yf.download(symbols, period="1mo", progress=False)

        if df is not None and not df.empty:
            # Step 3: Calculate returns for each symbol
            for symbol in symbols:
                try:
                    prices: pd.Series
                    if isinstance(df.columns, pd.MultiIndex):
                        # Multi-ticker download returns MultiIndex columns
                        if "Close" in df.columns.get_level_values(0):
                            close_df = df["Close"]
                            if symbol in close_df.columns:
                                symbol_data = close_df[symbol].dropna()
                                if isinstance(symbol_data, pd.DataFrame):
                                    prices = symbol_data.iloc[:, 0]
                                else:
                                    prices = symbol_data
                            else:
                                logger.debug(
                                    "Symbol not found in batch data",
                                    symbol=symbol,
                                )
                                stock_returns[symbol] = None
                                continue
                        else:
                            stock_returns[symbol] = None
                            continue
                    # Single ticker case
                    elif "Close" in df.columns:
                        close_data = df["Close"]
                        if isinstance(close_data, pd.DataFrame):
                            prices = close_data.iloc[:, 0].dropna()
                        else:
                            prices = close_data.dropna()
                    else:
                        stock_returns[symbol] = None
                        continue

                    if len(prices) > period:
                        stock_returns[symbol] = calculate_return(prices, period)
                    else:
                        stock_returns[symbol] = None

                except Exception as e:
                    logger.debug(
                        "Failed to calculate return for symbol",
                        symbol=symbol,
                        error=str(e),
                    )
                    stock_returns[symbol] = None
        else:
            # Mark all as None if batch download failed
            for symbol in symbols:
                stock_returns[symbol] = None

    except Exception as e:
        logger.warning(
            "Batch download failed for contributors",
            symbols=symbols,
            error=str(e),
        )
        for symbol in symbols:
            stock_returns[symbol] = None

    # Step 4: Build SectorContributor objects
    contributors: list[SectorContributor] = []
    for company in target_companies:
        symbol = company.get("symbol") or company.get("ticker", "")
        if not symbol:
            continue

        name = company.get("name", "")
        weight = company.get("weight", 0.0)
        stock_return = stock_returns.get(symbol)

        contributor = SectorContributor(
            ticker=str(symbol),
            name=str(name),
            return_1w=stock_return if stock_return is not None else 0.0,
            weight=float(weight) if weight else 0.0,
        )
        contributors.append(contributor)

    logger.debug(
        "Contributors built",
        count=len(contributors),
        with_returns=sum(1 for c in contributors if c.return_1w != 0.0),
    )

    return contributors
