#!/usr/bin/env python3
"""Collect Market Performance Data Script.

PerformanceAnalyzer4Agent を使用して市場パフォーマンスデータを収集し、
data/market/ に構造化JSONとして出力する。

Output files:
- {category}_{YYYYMMDD-HHMM}.json: カテゴリ別パフォーマンスデータ
- all_performance_{YYYYMMDD-HHMM}.json: 統合ファイル

Examples
--------
Basic usage:

    $ uv run python scripts/collect_market_performance.py

Specify output directory:

    $ uv run python scripts/collect_market_performance.py --output data/market

Notes
-----
- PerformanceAnalyzer4Agent を使用して複数期間（1D, 1W, MTD, YTD等）の騰落率を取得
- 各カテゴリ（indices_us, mag7, sectors等）を個別ファイルで出力
- データ鮮度情報（日付ズレ）も含めて出力
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.reporting.performance_agent import (
    PerformanceAnalyzer4Agent,
    PerformanceResult,
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


def collect_all_performance(
    output_dir: Path,
    timestamp: str,
) -> dict[str, dict[str, Any]]:
    """Collect all market performance data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming (YYYYMMDD-HHMM)

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary mapping category names to performance data
    """
    logger.info(
        "Starting market performance collection",
        output_dir=str(output_dir),
        timestamp=timestamp,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = PerformanceAnalyzer4Agent()
    results: dict[str, dict[str, Any]] = {}
    success_count = 0
    error_count = 0

    # Define categories to collect
    categories: dict[str, tuple[str, str | None]] = {
        "indices_us": ("indices", "us"),
        "indices_global": ("indices", "global"),
        "mag7": ("mag7", None),
        "sectors": ("sectors", None),
        "commodities": ("commodities", None),
    }

    for category_name, (group, subgroup) in categories.items():
        try:
            logger.info(
                "Collecting performance data",
                category=category_name,
                group=group,
                subgroup=subgroup,
            )

            result: PerformanceResult = analyzer.get_group_performance(group, subgroup)
            result_dict = result.to_dict()

            # Save individual category file
            file_name = f"{category_name}_{timestamp}.json"
            file_path = output_dir / file_name
            save_json(result_dict, file_path)

            results[category_name] = result_dict
            success_count += 1

            # Log data freshness warning if there's date gap
            if result.data_freshness.get("has_date_gap"):
                logger.warning(
                    "Date gap detected in data",
                    category=category_name,
                    newest_date=result.data_freshness.get("newest_date"),
                    oldest_date=result.data_freshness.get("oldest_date"),
                )

        except Exception as e:
            logger.error(
                "Failed to collect performance data",
                category=category_name,
                error=str(e),
                exc_info=True,
            )
            error_count += 1
            continue

    # Save all data in one file
    if results:
        all_data = {
            "generated_at": datetime.now().isoformat(),
            "timestamp": timestamp,
            "categories": list(results.keys()),
            "data": results,
        }
        all_file_name = f"all_performance_{timestamp}.json"
        save_json(all_data, output_dir / all_file_name)

    logger.info(
        "Market performance collection completed",
        success_count=success_count,
        error_count=error_count,
        total_categories=len(categories),
    )

    return results


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect market performance data using PerformanceAnalyzer4Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default output to data/market/
  uv run python scripts/collect_market_performance.py

  # Specify output directory
  uv run python scripts/collect_market_performance.py --output data/market

  # Output to temporary directory
  uv run python scripts/collect_market_performance.py --output .tmp/market_data
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
    logger.info("Market performance data collection started")

    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    timestamp = generate_timestamp()

    try:
        results = collect_all_performance(output_dir, timestamp)

        if not results:
            logger.error("No performance data was collected")
            return 1

        # Print summary
        print(f"\n{'=' * 60}")
        print("Market Performance Data Collection Complete")
        print(f"{'=' * 60}")
        print(f"Timestamp: {timestamp}")
        print(f"Output: {output_dir}")
        print("\nFiles created:")
        for category in results:
            print(f"  ✓ {category}_{timestamp}.json")
        print(f"  ✓ all_performance_{timestamp}.json")

        # Print summary of each category
        print("\nData Summary:")
        for category, data in results.items():
            symbol_count = len(data.get("symbols", {}))
            periods = data.get("periods", [])
            has_gap = data.get("data_freshness", {}).get("has_date_gap", False)
            gap_indicator = " ⚠️ date gap" if has_gap else ""
            print(
                f"  {category}: {symbol_count} symbols, periods: {periods}{gap_indicator}"
            )

        print(f"{'=' * 60}\n")

        return 0

    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
