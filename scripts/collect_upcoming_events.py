#!/usr/bin/env python3
"""Collect Upcoming Events Script.

UpcomingEvents4Agent を使用して来週の注目材料（決算・経済指標）を収集し、
data/market/ に構造化JSONとして出力する。

Output files:
- upcoming_events_{YYYYMMDD-HHMM}.json: 来週の注目材料

Examples
--------
Basic usage:

    $ uv run python scripts/collect_upcoming_events.py

Specify output directory:

    $ uv run python scripts/collect_upcoming_events.py --output data/market

Specify date range:

    $ uv run python scripts/collect_upcoming_events.py --start-date 2026-02-01 --end-date 2026-02-07

Notes
-----
- UpcomingEvents4Agent を使用して決算発表日と経済指標発表予定を取得
- 決算予定と経済指標発表予定の両方を含む
- データは単一のJSONファイルとして出力
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analyze.reporting.upcoming_events_agent import (
    UpcomingEvents4Agent,
    UpcomingEventsResult,
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


def parse_date(date_str: str) -> date:
    """Parse date string to date object.

    Parameters
    ----------
    date_str : str
        Date string in YYYY-MM-DD format

    Returns
    -------
    date
        Parsed date object

    Raises
    ------
    ValueError
        If date string is not in YYYY-MM-DD format
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD format."
        ) from e


def collect_upcoming_events(
    output_dir: Path,
    timestamp: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> UpcomingEventsResult | None:
    """Collect upcoming events data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming (YYYYMMDD-HHMM)
    start_date : date | None, default=None
        Start date for the period (default: tomorrow)
    end_date : date | None, default=None
        End date for the period (default: 1 week from start)

    Returns
    -------
    UpcomingEventsResult | None
        Upcoming events result, or None if collection failed
    """
    logger.info(
        "Starting upcoming events collection",
        output_dir=str(output_dir),
        timestamp=timestamp,
        start_date=str(start_date) if start_date else "default",
        end_date=str(end_date) if end_date else "default",
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate days_ahead based on date range
    if start_date and end_date:
        # Calculate days from tomorrow to end_date
        tomorrow = date.today() + timedelta(days=1)
        days_ahead = (end_date - tomorrow).days + 1
        if days_ahead < 1:
            logger.warning(
                "End date is before or on tomorrow, using default 7 days",
                end_date=str(end_date),
                tomorrow=str(tomorrow),
            )
            days_ahead = 7
    else:
        days_ahead = 7

    try:
        agent = UpcomingEvents4Agent()
        result: UpcomingEventsResult = agent.get_upcoming_events(days_ahead=days_ahead)

        # Override period if custom dates were provided
        if start_date and end_date:
            result.period["start"] = start_date.strftime("%Y-%m-%d")
            result.period["end"] = end_date.strftime("%Y-%m-%d")

        result_dict = result.to_dict()

        # Add metadata
        result_dict["timestamp"] = timestamp

        # Save to file
        file_name = f"upcoming_events_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        logger.info(
            "Upcoming events collection completed",
            earnings_count=result.summary.get("earnings_count", 0),
            economic_release_count=result.summary.get("economic_release_count", 0),
            high_importance_count=result.summary.get("high_importance_count", 0),
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to collect upcoming events",
            error=str(e),
            exc_info=True,
        )
        return None


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect upcoming events using UpcomingEvents4Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default output to data/market/
  uv run python scripts/collect_upcoming_events.py

  # Specify output directory
  uv run python scripts/collect_upcoming_events.py --output data/market

  # Specify date range
  uv run python scripts/collect_upcoming_events.py --start-date 2026-02-01 --end-date 2026-02-07

  # Output to temporary directory
  uv run python scripts/collect_upcoming_events.py --output .tmp/events
        """,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/market",
        help="Output directory for JSON files (default: data/market)",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date in YYYY-MM-DD format (default: tomorrow)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date in YYYY-MM-DD format (default: 1 week from start)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    logger.info("Upcoming events data collection started")

    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    timestamp = generate_timestamp()

    # Parse dates if provided
    start_date: date | None = None
    end_date: date | None = None

    try:
        if args.start_date:
            start_date = parse_date(args.start_date)
        if args.end_date:
            end_date = parse_date(args.end_date)

        # Validate date range
        if start_date and end_date and start_date > end_date:
            logger.error(
                "Invalid date range: start_date must be before end_date",
                start_date=str(start_date),
                end_date=str(end_date),
            )
            print(
                f"Error: start-date ({start_date}) must be before end-date ({end_date})"
            )
            return 1

    except ValueError as e:
        logger.error("Date parsing error", error=str(e))
        print(f"Error: {e}")
        return 1

    try:
        result = collect_upcoming_events(output_dir, timestamp, start_date, end_date)

        if result is None:
            logger.error("No upcoming events data was collected")
            print("Error: Failed to collect upcoming events data")
            return 1

        # Print summary
        print(f"\n{'=' * 60}")
        print("Upcoming Events Data Collection Complete")
        print(f"{'=' * 60}")
        print(f"Timestamp: {timestamp}")
        print(f"Output: {output_dir}")
        print(f"Period: {result.period['start']} to {result.period['end']}")
        print("\nFile created:")
        print(f"  - upcoming_events_{timestamp}.json")

        # Print summary of data
        print("\nData Summary:")
        print(f"  Earnings: {result.summary.get('earnings_count', 0)} companies")
        print(
            f"  Economic Releases: {result.summary.get('economic_release_count', 0)} events"
        )
        print(
            f"  High Importance: {result.summary.get('high_importance_count', 0)} events"
        )

        busiest_date = result.summary.get("busiest_date")
        if busiest_date:
            print(f"  Busiest Date: {busiest_date}")

        # List upcoming earnings
        if result.earnings:
            print("\nUpcoming Earnings:")
            for earning in result.earnings[:10]:  # Show first 10
                symbol = earning.get("symbol", "N/A")
                name = earning.get("name", "N/A")
                earnings_date = earning.get("earnings_date", "N/A")
                print(f"  - {symbol} ({name}): {earnings_date}")
            if len(result.earnings) > 10:
                print(f"  ... and {len(result.earnings) - 10} more")

        # List high importance economic releases
        high_importance = [
            r for r in result.economic_releases if r.get("importance") == "high"
        ]
        if high_importance:
            print("\nHigh Importance Economic Releases:")
            for release in high_importance:
                name_ja = release.get("name_ja", release.get("name", "N/A"))
                release_date = release.get("release_date", "N/A")
                print(f"  - {name_ja}: {release_date}")

        print(f"{'=' * 60}\n")

        return 0

    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        print(f"Error: Unexpected error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
