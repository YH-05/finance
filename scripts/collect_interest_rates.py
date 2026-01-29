#!/usr/bin/env python3
"""Collect Interest Rate Data Script.

InterestRateAnalyzer4Agent を使用して金利データを収集し、
data/market/ に構造化JSONとして出力する。

Output files:
- interest_rates_{YYYYMMDD-HHMM}.json: 金利データ

Examples
--------
Basic usage:

    $ uv run python scripts/collect_interest_rates.py

Specify output directory:

    $ uv run python scripts/collect_interest_rates.py --output data/market

Notes
-----
- InterestRateAnalyzer4Agent を使用して金利変化とイールドカーブ分析を取得
- 対象シリーズ: DGS2, DGS10, DGS30, FEDFUNDS, T10Y2Y
- データ鮮度情報（日付ズレ）も含めて出力
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.reporting.interest_rate_agent import (
    InterestRateAnalyzer4Agent,
    InterestRateResult,
)
from database.utils import get_logger

logger = get_logger(__name__)


def generate_timestamp() -> str:
    """Generate timestamp string in YYYYMMDD-HHMM format.

    Returns
    -------
    str
        Timestamp string (e.g., "20260129-1030")
    """
    return datetime.now().strftime("%Y%m%d-%H%M")


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


def collect_interest_rates(
    output_dir: Path,
    timestamp: str,
) -> InterestRateResult | None:
    """Collect interest rate data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming (YYYYMMDD-HHMM)

    Returns
    -------
    InterestRateResult | None
        Interest rate analysis result, or None if collection failed
    """
    logger.info(
        "Starting interest rate data collection",
        output_dir=str(output_dir),
        timestamp=timestamp,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = InterestRateAnalyzer4Agent()

    try:
        logger.info("Collecting interest rate data")

        result: InterestRateResult = analyzer.get_interest_rate_data()
        result_dict = result.to_dict()

        # Save interest rate data file
        file_name = f"interest_rates_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        # Log data freshness warning if there's date gap
        if result.data_freshness.get("has_date_gap"):
            logger.warning(
                "Date gap detected in data",
                newest_date=result.data_freshness.get("newest_date"),
                oldest_date=result.data_freshness.get("oldest_date"),
            )

        logger.info(
            "Interest rate data collection completed",
            series_count=len(result.data),
            is_inverted=result.yield_curve.get("is_inverted", False),
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to collect interest rate data",
            error=str(e),
            exc_info=True,
        )
        return None


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect interest rate data using InterestRateAnalyzer4Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default output to data/market/
  uv run python scripts/collect_interest_rates.py

  # Specify output directory
  uv run python scripts/collect_interest_rates.py --output data/market

  # Output to temporary directory
  uv run python scripts/collect_interest_rates.py --output .tmp/interest_rate_data
        """,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/market",
        help="Output directory for JSON files (default: data/market)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    logger.info("Interest rate data collection started")

    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    timestamp = generate_timestamp()

    try:
        result = collect_interest_rates(output_dir, timestamp)

        if result is None:
            logger.error("No interest rate data was collected")
            return 1

        # Print summary
        print(f"\n{'=' * 60}")
        print("Interest Rate Data Collection Complete")
        print(f"{'=' * 60}")
        print(f"Timestamp: {timestamp}")
        print(f"Output: {output_dir}")
        print("\nFile created:")
        print(f"  * interest_rates_{timestamp}.json")

        # Print data summary
        print("\nData Summary:")
        print(f"  Group: {result.group}")
        print(f"  Periods: {result.periods}")
        print(f"  Series count: {len(result.data)}")

        # Print series details
        print("\n  Series:")
        for series_id, series_data in result.data.items():
            latest = series_data.get("latest")
            if latest is not None:
                print(f"    {series_id}: {latest:.4f}%")
            else:
                print(f"    {series_id}: N/A")

        # Print yield curve analysis
        yield_curve = result.yield_curve
        print("\n  Yield Curve Analysis:")
        spread = yield_curve.get("spread_10y_2y")
        if spread is not None:
            print(f"    10Y-2Y Spread: {spread:.4f}%")
        print(f"    Slope Status: {yield_curve.get('slope_status', 'unknown')}")
        print(f"    Is Inverted: {yield_curve.get('is_inverted', False)}")

        # Print data freshness
        freshness = result.data_freshness
        has_gap = freshness.get("has_date_gap", False)
        gap_indicator = " (date gap detected)" if has_gap else ""
        print(f"\n  Data Freshness{gap_indicator}:")
        print(f"    Newest Date: {freshness.get('newest_date', 'N/A')}")
        print(f"    Oldest Date: {freshness.get('oldest_date', 'N/A')}")

        print(f"{'=' * 60}\n")

        return 0

    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
