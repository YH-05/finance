#!/usr/bin/env python3
"""Weekly Comment Data Collection Script.

This script collects market data for the weekly comment generation,
focusing on a specific Tuesday-to-Tuesday period.

Output files:
- indices.json: Weekly returns for key indices (S&P500, RSP, VUG, VTV)
- mag7.json: Weekly returns for Magnificent 7 stocks
- sectors.json: Top 3 and bottom 3 sectors by weekly return

Examples
--------
Basic usage (auto-calculates period based on today's date):

    $ uv run python scripts/weekly_comment_data.py

Specify output directory:

    $ uv run python scripts/weekly_comment_data.py --output articles/weekly_comment_20260122/data

Specify custom date range:

    $ uv run python scripts/weekly_comment_data.py --start 2026-01-14 --end 2026-01-21

Notes
-----
- Period is calculated as Tuesday-to-Tuesday (previous week's Tuesday to this week's Tuesday)
- Uses yf.download for batch data retrieval
- All returns are calculated as (end_price - start_price) / start_price
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from database.utils.logging_config import get_logger
from market_analysis.utils.date_utils import (
    calculate_weekly_comment_period,
    format_date_japanese,
    format_date_us,
    parse_date,
)

logger = get_logger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Key indices for weekly comment
INDICES_TICKERS: dict[str, str] = {
    "^GSPC": "S&P 500",
    "RSP": "S&P 500 Equal Weight",
    "VUG": "Vanguard Growth ETF",
    "VTV": "Vanguard Value ETF",
}

# Magnificent 7 stocks
MAG7_TICKERS: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet (Google)",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta (Facebook)",
    "TSLA": "Tesla",
}

# Semiconductor index (SOX)
SOX_TICKER = "^SOX"
SOX_NAME = "Philadelphia Semiconductor Index"

# Sector ETFs
SECTOR_ETFS: dict[str, str] = {
    "XLK": "Information Technology",
    "XLF": "Financial Services",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLB": "Basic Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}


# =============================================================================
# Data Collection Functions
# =============================================================================


def calculate_period_return(
    prices: pd.Series,
    start_date: date,
    end_date: date,
) -> float | None:
    """Calculate return for a specific date range.

    Parameters
    ----------
    prices : pd.Series
        Price series with DatetimeIndex
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    float | None
        Calculated return as decimal, or None if insufficient data
    """
    if prices.empty:
        return None

    # Convert dates to datetime for comparison
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    # Find the closest price on or after start_date
    start_prices = prices[prices.index >= start_dt]
    if start_prices.empty:
        logger.debug("No data found on or after start date", start_date=str(start_date))
        return None
    start_price = start_prices.iloc[0]

    # Find the closest price on or before end_date
    end_prices = prices[prices.index <= end_dt]
    if end_prices.empty:
        logger.debug("No data found on or before end date", end_date=str(end_date))
        return None
    end_price = end_prices.iloc[-1]

    if start_price == 0:
        logger.warning("Start price is zero")
        return None

    return float((end_price - start_price) / start_price)


def fetch_weekly_returns(
    tickers: dict[str, str],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Fetch weekly returns for a list of tickers.

    Parameters
    ----------
    tickers : dict[str, str]
        Dictionary mapping ticker symbols to display names
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries with ticker, name, and return data
    """
    logger.debug(
        "Fetching weekly returns",
        ticker_count=len(tickers),
        start_date=str(start_date),
        end_date=str(end_date),
    )

    if not tickers:
        return []

    results: list[dict[str, Any]] = []
    ticker_list = list(tickers.keys())

    try:
        # Fetch data with some buffer before start_date
        fetch_start = start_date - timedelta(days=7)
        fetch_end = end_date + timedelta(days=3)

        logger.debug(
            "Downloading data",
            tickers=ticker_list,
            fetch_start=str(fetch_start),
            fetch_end=str(fetch_end),
        )

        df = yf.download(
            ticker_list,
            start=fetch_start.isoformat(),
            end=fetch_end.isoformat(),
            progress=False,
        )

        if df is None or df.empty:
            logger.warning("No data returned from yfinance")
            return []

        # Process each ticker
        for ticker, name in tickers.items():
            try:
                # Extract Close prices for this ticker
                prices: pd.Series
                if isinstance(df.columns, pd.MultiIndex):
                    if "Close" in df.columns.get_level_values(0):
                        close_df = df["Close"]
                        if ticker in close_df.columns:
                            price_data = close_df[ticker].dropna()
                            if isinstance(price_data, pd.DataFrame):
                                prices = price_data.iloc[:, 0]
                            else:
                                prices = price_data
                        else:
                            logger.debug("Ticker not found in data", ticker=ticker)
                            continue
                    else:
                        continue
                elif "Close" in df.columns:
                    close_data = df["Close"].dropna()
                    if isinstance(close_data, pd.DataFrame):
                        prices = close_data.iloc[:, 0]
                    else:
                        prices = close_data
                else:
                    continue

                if prices.empty:
                    logger.debug("Empty price data", ticker=ticker)
                    continue

                # Calculate weekly return
                weekly_return = calculate_period_return(prices, start_date, end_date)

                # Get latest close price
                end_dt = pd.Timestamp(end_date)
                end_prices = prices[prices.index <= end_dt]
                latest_close = (
                    float(end_prices.iloc[-1]) if not end_prices.empty else None
                )

                result = {
                    "ticker": ticker,
                    "name": name,
                    "weekly_return": weekly_return,
                    "latest_close": latest_close,
                }
                results.append(result)

                logger.debug(
                    "Return calculated",
                    ticker=ticker,
                    weekly_return=weekly_return,
                )

            except Exception as e:
                logger.warning(
                    "Failed to process ticker",
                    ticker=ticker,
                    error=str(e),
                )
                continue

    except Exception as e:
        logger.error(
            "Batch download failed",
            error=str(e),
            exc_info=True,
        )
        return []

    logger.info(
        "Weekly returns fetched",
        processed_count=len(results),
        total_tickers=len(tickers),
    )

    return results


def collect_indices_data(start_date: date, end_date: date) -> dict[str, Any]:
    """Collect indices data for weekly comment.

    Parameters
    ----------
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    dict[str, Any]
        Indices data with structure:
        {
            "as_of": "2026-01-21",
            "period": {"start": "2026-01-14", "end": "2026-01-21"},
            "indices": [...]
        }
    """
    logger.info("Collecting indices data")

    indices = fetch_weekly_returns(INDICES_TICKERS, start_date, end_date)

    return {
        "as_of": end_date.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "indices": indices,
    }


def collect_mag7_data(start_date: date, end_date: date) -> dict[str, Any]:
    """Collect MAG7 data for weekly comment.

    Parameters
    ----------
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    dict[str, Any]
        MAG7 data with structure:
        {
            "as_of": "2026-01-21",
            "period": {"start": "2026-01-14", "end": "2026-01-21"},
            "mag7": [...],
            "sox": {...}
        }
    """
    logger.info("Collecting MAG7 data")

    # Fetch MAG7 returns
    mag7 = fetch_weekly_returns(MAG7_TICKERS, start_date, end_date)

    # Sort by weekly return (descending)
    mag7_sorted = sorted(
        mag7,
        key=lambda x: x.get("weekly_return") or -999,
        reverse=True,
    )

    # Fetch SOX index
    sox_data = fetch_weekly_returns({SOX_TICKER: SOX_NAME}, start_date, end_date)
    sox = sox_data[0] if sox_data else None

    return {
        "as_of": end_date.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "mag7": mag7_sorted,
        "sox": sox,
    }


def collect_sectors_data(start_date: date, end_date: date) -> dict[str, Any]:
    """Collect sector data for weekly comment.

    Parameters
    ----------
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    dict[str, Any]
        Sector data with structure:
        {
            "as_of": "2026-01-21",
            "period": {"start": "2026-01-14", "end": "2026-01-21"},
            "top_sectors": [...],
            "bottom_sectors": [...],
            "all_sectors": [...]
        }
    """
    logger.info("Collecting sector data")

    sectors = fetch_weekly_returns(SECTOR_ETFS, start_date, end_date)

    # Sort by weekly return
    sectors_sorted = sorted(
        sectors,
        key=lambda x: x.get("weekly_return") or -999,
        reverse=True,
    )

    # Top 3 and bottom 3
    top_sectors = sectors_sorted[:3]
    bottom_sectors = sectors_sorted[-3:][::-1]  # Reverse to show worst first

    return {
        "as_of": end_date.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "top_sectors": top_sectors,
        "bottom_sectors": bottom_sectors,
        "all_sectors": sectors_sorted,
    }


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """Save data to JSON file.

    Parameters
    ----------
    data : dict[str, Any]
        Data to save
    file_path : Path
        Output file path
    """
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Data saved", file=str(file_path))


def save_all_data(
    output_dir: Path, start_date: date, end_date: date
) -> dict[str, bool]:
    """Collect and save all weekly comment data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    start_date : date
        Start date of the period
    end_date : date
        End date of the period

    Returns
    -------
    dict[str, bool]
        Dictionary mapping file names to success status
    """
    logger.info(
        "Starting weekly comment data collection",
        output_dir=str(output_dir),
        start_date=str(start_date),
        end_date=str(end_date),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, bool] = {}

    # Collect indices data
    try:
        indices_data = collect_indices_data(start_date, end_date)
        save_json(indices_data, output_dir / "indices.json")
        results["indices.json"] = True
    except Exception as e:
        logger.error("Failed to collect indices data", error=str(e), exc_info=True)
        results["indices.json"] = False

    # Collect MAG7 data
    try:
        mag7_data = collect_mag7_data(start_date, end_date)
        save_json(mag7_data, output_dir / "mag7.json")
        results["mag7.json"] = True
    except Exception as e:
        logger.error("Failed to collect MAG7 data", error=str(e), exc_info=True)
        results["mag7.json"] = False

    # Collect sectors data
    try:
        sectors_data = collect_sectors_data(start_date, end_date)
        save_json(sectors_data, output_dir / "sectors.json")
        results["sectors.json"] = True
    except Exception as e:
        logger.error("Failed to collect sector data", error=str(e), exc_info=True)
        results["sectors.json"] = False

    # Save period metadata
    try:
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "start_jp": format_date_japanese(start_date, "short"),
                "end_jp": format_date_japanese(end_date, "short"),
                "start_us": format_date_us(start_date, "short"),
                "end_us": format_date_us(end_date, "short"),
            },
        }
        save_json(metadata, output_dir / "metadata.json")
        results["metadata.json"] = True
    except Exception as e:
        logger.error("Failed to save metadata", error=str(e), exc_info=True)
        results["metadata.json"] = False

    logger.info(
        "Weekly comment data collection completed",
        success_count=sum(results.values()),
        total_count=len(results),
    )

    return results


# =============================================================================
# CLI
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect market data for weekly comment generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-calculate period based on today's date
  uv run python scripts/weekly_comment_data.py

  # Specify output directory
  uv run python scripts/weekly_comment_data.py --output articles/weekly_comment_20260122/data

  # Specify custom date range
  uv run python scripts/weekly_comment_data.py --start 2026-01-14 --end 2026-01-21
        """,
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    default_output = f".tmp/weekly-comment-{timestamp}"

    parser.add_argument(
        "--output",
        type=str,
        default=default_output,
        help=f"Output directory for JSON files (default: {default_output})",
    )

    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD). If not specified, calculates from reference date.",
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD). If not specified, calculates from reference date.",
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Reference date for period calculation (YYYY-MM-DD). Defaults to today.",
    )

    return parser


def main() -> int:
    """Main entry point."""
    logger.info("Weekly comment data collection started")

    parser = create_parser()
    args = parser.parse_args()

    # Determine period
    if args.start and args.end:
        # Explicit start/end dates
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
        logger.info(
            "Using explicit date range",
            start=str(start_date),
            end=str(end_date),
        )
    else:
        # Calculate period from reference date
        reference_date = parse_date(args.date) if args.date else date.today()
        period = calculate_weekly_comment_period(reference_date)
        start_date = period["start"]
        end_date = period["end"]
        logger.info(
            "Calculated period from reference date",
            reference=str(reference_date),
            start=str(start_date),
            end=str(end_date),
        )

    output_dir = Path(args.output)

    try:
        results = save_all_data(output_dir, start_date, end_date)

        # Check if at least one file was created successfully
        if not any(results.values()):
            logger.error("No data files were created")
            return 1

        # Print summary
        print(f"\n{'=' * 60}")
        print("Weekly Comment Data Collection Complete")
        print(f"{'=' * 60}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Output: {output_dir}")
        print("\nFiles created:")
        for filename, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {filename}")
        print(f"{'=' * 60}\n")

        return 0

    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
