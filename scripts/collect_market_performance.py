#!/usr/bin/env python3
"""Collect Market Performance Data Script.

市場パフォーマンスデータ、金利、為替、来週の注目材料を収集し、
data/market/ に構造化JSONとして出力する。

Output files:
- indices_us_{YYYYMMDD-HHMM}.json: 米国株価指数
- indices_global_{YYYYMMDD-HHMM}.json: グローバル株価指数
- mag7_{YYYYMMDD-HHMM}.json: MAG7銘柄
- sectors_{YYYYMMDD-HHMM}.json: セクター
- commodities_{YYYYMMDD-HHMM}.json: コモディティ
- interest_rates_{YYYYMMDD-HHMM}.json: 金利データ
- currencies_{YYYYMMDD-HHMM}.json: 為替データ
- upcoming_events_{YYYYMMDD-HHMM}.json: 来週の注目材料
- all_performance_{YYYYMMDD-HHMM}.json: 全統合ファイル

Examples
--------
Basic usage:

    $ uv run python scripts/collect_market_performance.py

Specify output directory:

    $ uv run python scripts/collect_market_performance.py --output data/market

Notes
-----
- PerformanceAnalyzer4Agent: 複数期間（1D, 1W, MTD, YTD等）の騰落率
- InterestRateAnalyzer4Agent: 金利データとイールドカーブ分析
- CurrencyAnalyzer4Agent: 円クロス為替のパフォーマンス
- UpcomingEvents4Agent: 決算発表予定と経済指標発表予定
- 各カテゴリを個別ファイルで出力
- データ鮮度情報（日付ズレ）も含めて出力
- エラー時も他カテゴリの処理を継続
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.reporting.currency_agent import CurrencyAnalyzer4Agent, CurrencyResult
from analyze.reporting.interest_rate_agent import (
    InterestRateAnalyzer4Agent,
    InterestRateResult,
)
from analyze.reporting.performance_agent import (
    PerformanceAnalyzer4Agent,
    PerformanceResult,
)
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


def collect_performance_categories(
    analyzer: PerformanceAnalyzer4Agent,
    output_dir: Path,
    timestamp: str,
) -> tuple[dict[str, dict[str, Any]], int, int]:
    """Collect performance data for standard categories.

    Parameters
    ----------
    analyzer : PerformanceAnalyzer4Agent
        Performance analyzer instance
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming

    Returns
    -------
    tuple[dict[str, dict[str, Any]], int, int]
        (results dict, success count, error count)
    """
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

    return results, success_count, error_count


def collect_interest_rates(
    output_dir: Path,
    timestamp: str,
) -> tuple[dict[str, Any] | None, bool]:
    """Collect interest rate data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming

    Returns
    -------
    tuple[dict[str, Any] | None, bool]
        (result dict or None, success flag)
    """
    try:
        logger.info("Collecting interest rate data", category="interest_rates")

        analyzer = InterestRateAnalyzer4Agent()
        result: InterestRateResult = analyzer.get_interest_rate_data()
        result_dict = result.to_dict()

        # Save individual category file
        file_name = f"interest_rates_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        # Log data freshness warning if there's date gap
        if result.data_freshness.get("has_date_gap"):
            logger.warning(
                "Date gap detected in interest rate data",
                category="interest_rates",
                newest_date=result.data_freshness.get("newest_date"),
                oldest_date=result.data_freshness.get("oldest_date"),
            )

        return result_dict, True

    except Exception as e:
        logger.error(
            "Failed to collect interest rate data",
            category="interest_rates",
            error=str(e),
            exc_info=True,
        )
        return None, False


def collect_currencies(
    output_dir: Path,
    timestamp: str,
) -> tuple[dict[str, Any] | None, bool]:
    """Collect currency data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming

    Returns
    -------
    tuple[dict[str, Any] | None, bool]
        (result dict or None, success flag)
    """
    try:
        logger.info("Collecting currency data", category="currencies")

        analyzer = CurrencyAnalyzer4Agent()
        result: CurrencyResult = analyzer.get_currency_performance()
        result_dict = result.to_dict()

        # Save individual category file
        file_name = f"currencies_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        # Log data freshness warning if there's date gap
        if result.data_freshness.get("has_date_gap"):
            logger.warning(
                "Date gap detected in currency data",
                category="currencies",
                newest_date=result.data_freshness.get("newest_date"),
                oldest_date=result.data_freshness.get("oldest_date"),
            )

        return result_dict, True

    except Exception as e:
        logger.error(
            "Failed to collect currency data",
            category="currencies",
            error=str(e),
            exc_info=True,
        )
        return None, False


def collect_upcoming_events(
    output_dir: Path,
    timestamp: str,
) -> tuple[dict[str, Any] | None, bool]:
    """Collect upcoming events data.

    Parameters
    ----------
    output_dir : Path
        Output directory for JSON files
    timestamp : str
        Timestamp string for file naming

    Returns
    -------
    tuple[dict[str, Any] | None, bool]
        (result dict or None, success flag)
    """
    try:
        logger.info("Collecting upcoming events data", category="upcoming_events")

        agent = UpcomingEvents4Agent()
        result: UpcomingEventsResult = agent.get_upcoming_events()
        result_dict = result.to_dict()

        # Save individual category file
        file_name = f"upcoming_events_{timestamp}.json"
        file_path = output_dir / file_name
        save_json(result_dict, file_path)

        return result_dict, True

    except Exception as e:
        logger.error(
            "Failed to collect upcoming events data",
            category="upcoming_events",
            error=str(e),
            exc_info=True,
        )
        return None, False


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

    results: dict[str, dict[str, Any]] = {}
    success_count = 0
    error_count = 0

    # Collect standard performance categories
    perf_analyzer = PerformanceAnalyzer4Agent()
    perf_results, perf_success, perf_error = collect_performance_categories(
        perf_analyzer, output_dir, timestamp
    )
    results.update(perf_results)
    success_count += perf_success
    error_count += perf_error

    # Collect interest rate data
    interest_rate_result, interest_rate_success = collect_interest_rates(
        output_dir, timestamp
    )
    if interest_rate_success and interest_rate_result:
        results["interest_rates"] = interest_rate_result
        success_count += 1
    else:
        error_count += 1

    # Collect currency data
    currency_result, currency_success = collect_currencies(output_dir, timestamp)
    if currency_success and currency_result:
        results["currencies"] = currency_result
        success_count += 1
    else:
        error_count += 1

    # Collect upcoming events data
    events_result, events_success = collect_upcoming_events(output_dir, timestamp)
    if events_success and events_result:
        results["upcoming_events"] = events_result
        success_count += 1
    else:
        error_count += 1

    # Calculate total categories
    total_categories = 5 + 3  # 5 performance categories + 3 new categories

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
        total_categories=total_categories,
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
            has_gap = data.get("data_freshness", {}).get("has_date_gap", False)
            gap_indicator = " [date gap]" if has_gap else ""

            if category == "interest_rates":
                # Interest rate data structure
                data_count = len(data.get("data", {}))
                yield_curve = data.get("yield_curve", {})
                is_inverted = yield_curve.get("is_inverted", False)
                inverted_indicator = " [inverted]" if is_inverted else ""
                print(
                    f"  {category}: {data_count} series{inverted_indicator}{gap_indicator}"
                )
            elif category == "currencies":
                # Currency data structure
                symbol_count = len(data.get("symbols", {}))
                periods = data.get("periods", [])
                print(
                    f"  {category}: {symbol_count} pairs, periods: {periods}{gap_indicator}"
                )
            elif category == "upcoming_events":
                # Upcoming events data structure
                summary = data.get("summary", {})
                earnings_count = summary.get("earnings_count", 0)
                economic_count = summary.get("economic_release_count", 0)
                period = data.get("period", {})
                period_str = f"{period.get('start', '?')} - {period.get('end', '?')}"
                print(
                    f"  {category}: {earnings_count} earnings, "
                    f"{economic_count} economic ({period_str})"
                )
            else:
                # Standard performance data structure
                symbol_count = len(data.get("symbols", {}))
                periods = data.get("periods", [])
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
