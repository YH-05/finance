#!/usr/bin/env python3
"""Collect Currency Rates Data Script.

CurrencyAnalyzer4Agent を使用して為替データを収集し、
data/market/ に構造化JSONとして出力する。

Output files:
- currency_{subgroup}_{YYYYMMDD-HHMM}.json: 為替パフォーマンスデータ

Examples
--------
Basic usage:

    $ uv run python scripts/collect_currency_rates.py

Specify output directory:

    $ uv run python scripts/collect_currency_rates.py --output data/market

Specify subgroup:

    $ uv run python scripts/collect_currency_rates.py --subgroup usd_crosses

Notes
-----
- CurrencyAnalyzer4Agent を使用して複数期間（1D, 1W, 1M）の騰落率を取得
- 各通貨ペアの対円レートを収集
- データ鮮度情報（日付ズレ）も含めて出力
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.reporting.currency_agent import (
    CurrencyAnalyzer4Agent,
    CurrencyResult,
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


def collect_currency_rates(
    output_dir: Path,
    timestamp: str,
    subgroup: str,
) -> dict[str, Any] | None:
    """Collect currency rates data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming (YYYYMMDD-HHMM)
    subgroup : str
        Currency subgroup (e.g., "jpy_crosses")

    Returns
    -------
    dict[str, Any] | None
        Currency performance data or None if collection failed
    """
    logger.info(
        "Starting currency rates collection",
        output_dir=str(output_dir),
        timestamp=timestamp,
        subgroup=subgroup,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        analyzer = CurrencyAnalyzer4Agent()
        result: CurrencyResult = analyzer.get_currency_performance()
        result_dict = result.to_dict()

        # Save currency data file
        file_name = f"currency_{subgroup}_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        # Log data freshness warning if there's date gap
        if result.data_freshness.get("has_date_gap"):
            logger.warning(
                "Date gap detected in currency data",
                newest_date=result.data_freshness.get("newest_date"),
                oldest_date=result.data_freshness.get("oldest_date"),
            )

        logger.info(
            "Currency rates collection completed",
            symbol_count=len(result_dict.get("symbols", {})),
            periods=result_dict.get("periods", []),
        )

        return result_dict

    except Exception as e:
        logger.error(
            "Failed to collect currency rates",
            error=str(e),
            exc_info=True,
        )
        return None


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect currency rates data using CurrencyAnalyzer4Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default output to data/market/
  uv run python scripts/collect_currency_rates.py

  # Specify output directory
  uv run python scripts/collect_currency_rates.py --output data/market

  # Specify subgroup
  uv run python scripts/collect_currency_rates.py --subgroup usd_crosses

  # Output to temporary directory with custom subgroup
  uv run python scripts/collect_currency_rates.py --output .tmp/currency --subgroup eur_crosses
        """,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/market",
        help="Output directory for JSON files (default: data/market)",
    )

    parser.add_argument(
        "--subgroup",
        type=str,
        default="jpy_crosses",
        help="Currency subgroup (default: jpy_crosses)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    logger.info("Currency rates data collection started")

    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    timestamp = generate_timestamp()
    subgroup = args.subgroup

    result = collect_currency_rates(output_dir, timestamp, subgroup)

    if not result:
        logger.error("No currency data was collected")
        return 1

    # Print summary
    print(f"\n{'=' * 60}")
    print("Currency Rates Data Collection Complete")
    print(f"{'=' * 60}")
    print(f"Timestamp: {timestamp}")
    print(f"Output: {output_dir}")
    print(f"Subgroup: {subgroup}")
    print("\nFile created:")
    print(f"  - currency_{subgroup}_{timestamp}.json")

    # Print summary of data
    print("\nData Summary:")
    symbol_count = len(result.get("symbols", {}))
    periods = result.get("periods", [])
    has_gap = result.get("data_freshness", {}).get("has_date_gap", False)
    gap_indicator = " (date gap detected)" if has_gap else ""

    print(f"  Symbols: {symbol_count}")
    print(f"  Periods: {periods}")
    print(f"  Base Currency: {result.get('base_currency', 'N/A')}")
    print(
        f"  Data Freshness: {result.get('data_freshness', {}).get('newest_date', 'N/A')}{gap_indicator}"
    )

    # Print strongest/weakest currency
    summary = result.get("summary", {})
    if summary:
        strongest = summary.get("strongest_currency", {})
        weakest = summary.get("weakest_currency", {})
        if strongest:
            print(
                f"\n  Strongest: {strongest.get('symbol')} ({strongest.get('period')}: {strongest.get('return_pct')}%)"
            )
        if weakest:
            print(
                f"  Weakest: {weakest.get('symbol')} ({weakest.get('period')}: {weakest.get('return_pct')}%)"
            )

    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
