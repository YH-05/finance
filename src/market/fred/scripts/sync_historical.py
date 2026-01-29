"""CLI script for syncing FRED historical data to local cache.

This script provides command-line interface for managing FRED data cache.
Supports full sync, incremental updates, and status checking.

Examples
--------
Sync all preset series:
    $ uv run python -m market.fred.scripts.sync_historical --all

Sync specific category:
    $ uv run python -m market.fred.scripts.sync_historical --category "Treasury Yields"

Sync single series:
    $ uv run python -m market.fred.scripts.sync_historical --series DGS10

Check sync status:
    $ uv run python -m market.fred.scripts.sync_historical --status

Auto sync (only stale data):
    $ uv run python -m market.fred.scripts.sync_historical --auto

Custom output directory:
    $ uv run python -m market.fred.scripts.sync_historical --all --output-dir /custom/path
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils_core.logging import get_logger

from ..historical_cache import HistoricalCache

logger = get_logger(__name__, module="sync_historical")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Parameters
    ----------
    args : list[str] | None
        Command line arguments. If None, uses sys.argv[1:].

    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Sync FRED historical data to local cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Sync all preset series:
    %(prog)s --all

  Sync specific category:
    %(prog)s --category "Treasury Yields"

  Sync single series:
    %(prog)s --series DGS10

  Check sync status:
    %(prog)s --status

  Auto sync (only stale data, default 24 hours):
    %(prog)s --auto

  Auto sync with custom stale threshold:
    %(prog)s --auto --stale-hours 48

  Custom output directory:
    %(prog)s --all --output-dir /custom/path
""",
    )

    # Sync mode options (mutually exclusive in practice)
    sync_group = parser.add_argument_group("Sync Options")
    sync_group.add_argument(
        "--all",
        action="store_true",
        help="Sync all preset series",
    )
    sync_group.add_argument(
        "--category",
        type=str,
        metavar="CATEGORY",
        help="Sync all series in a specific category",
    )
    sync_group.add_argument(
        "--series",
        type=str,
        metavar="SERIES_ID",
        help="Sync a single series",
    )
    sync_group.add_argument(
        "--auto",
        action="store_true",
        help="Auto sync: only update stale data (default: 24 hours)",
    )

    # Status option
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show sync status for all series",
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--output-dir",
        type=str,
        metavar="PATH",
        help="Custom output directory for cache files",
    )
    config_group.add_argument(
        "--stale-hours",
        type=int,
        default=24,
        metavar="HOURS",
        help="Hours after which data is considered stale (default: 24)",
    )

    return parser.parse_args(args)


def run_sync(args: argparse.Namespace) -> int:
    """Execute the sync operation based on arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command line arguments

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    # Determine base path
    base_path = Path(args.output_dir) if args.output_dir else None

    # Create cache instance
    cache = HistoricalCache(base_path=base_path)

    # Handle --status
    if args.status:
        return _show_status(cache)

    # Handle --auto
    if args.auto:
        return _auto_sync(cache, args.stale_hours)

    # Handle --all
    if args.all:
        return _sync_all(cache)

    # Handle --category
    if args.category:
        return _sync_category(cache, args.category)

    # Handle --series
    if args.series:
        return _sync_series(cache, args.series)

    # No option specified
    print(
        "Error: Please specify one of --all, --category, --series, --status, or --auto.",
        file=sys.stderr,
    )
    return 1


def _show_status(cache: HistoricalCache) -> int:
    """Show sync status for all series.

    Parameters
    ----------
    cache : HistoricalCache
        Cache instance

    Returns
    -------
    int
        Exit code
    """
    status = cache.get_status()

    cached_count = sum(1 for s in status.values() if s.get("cached", False))
    total_count = len(status)

    print("\nFRED Historical Data Cache Status")
    print("=" * 60)
    print(f"Cached: {cached_count}/{total_count} series\n")

    # Group by cached status
    cached_series = {k: v for k, v in status.items() if v.get("cached", False)}
    not_cached = {k: v for k, v in status.items() if not v.get("cached", False)}

    if cached_series:
        print("Cached Series:")
        print("-" * 60)
        for series_id, info in sorted(cached_series.items()):
            data_points = info.get("data_points", 0)
            date_range = info.get("date_range", [None, None])
            range_str = (
                f"{date_range[0]} to {date_range[1]}"
                if date_range[0] and date_range[1]
                else "Unknown"
            )
            print(f"  {series_id:15} | {data_points:6} points | {range_str}")
        print()

    if not_cached:
        print("Not Cached:")
        print("-" * 60)
        for series_id in sorted(not_cached.keys()):
            print(f"  {series_id}")
        print()

    return 0


def _auto_sync(cache: HistoricalCache, stale_hours: int) -> int:
    """Auto sync only stale data.

    Parameters
    ----------
    cache : HistoricalCache
        Cache instance
    stale_hours : int
        Hours after which data is considered stale

    Returns
    -------
    int
        Exit code
    """
    logger.info("Starting auto sync", stale_hours=stale_hours)

    status = cache.get_status()
    now = datetime.now(timezone.utc)
    series_to_sync: list[str] = []

    for series_id, info in status.items():
        if not info.get("cached", False):
            # Not cached, needs sync
            series_to_sync.append(series_id)
            continue

        last_fetched_str = info.get("last_fetched")
        if not last_fetched_str:
            series_to_sync.append(series_id)
            continue

        try:
            last_fetched = datetime.fromisoformat(last_fetched_str)
            hours_since = (now - last_fetched).total_seconds() / 3600
            if hours_since > stale_hours:
                series_to_sync.append(series_id)
        except (ValueError, TypeError):
            series_to_sync.append(series_id)

    if not series_to_sync:
        print("All series are up to date.")
        return 0

    print(f"Syncing {len(series_to_sync)} stale series...")

    success_count = 0
    fail_count = 0

    for series_id in series_to_sync:
        result = cache.sync_series(series_id)
        if result.get("success", False):
            success_count += 1
            print(f"  [OK] {series_id}: {result.get('data_points', 0)} points")
        else:
            fail_count += 1
            print(f"  [FAIL] {series_id}: {result.get('error', 'Unknown error')}")

    print(f"\nAuto sync completed: {success_count} succeeded, {fail_count} failed")

    return 0 if fail_count == 0 else 1


def _sync_all(cache: HistoricalCache) -> int:
    """Sync all preset series.

    Parameters
    ----------
    cache : HistoricalCache
        Cache instance

    Returns
    -------
    int
        Exit code
    """
    logger.info("Syncing all preset series")

    results = cache.sync_all_presets()

    success_count = sum(1 for r in results if r.get("success", False))
    fail_count = len(results) - success_count

    print(f"\nSync completed: {success_count}/{len(results)} series successful")

    if fail_count > 0:
        print("\nFailed series:")
        for result in results:
            if not result.get("success", False):
                print(
                    f"  {result['series_id']}: {result.get('error', 'Unknown error')}"
                )

    return 0 if fail_count == 0 else 1


def _sync_category(cache: HistoricalCache, category: str) -> int:
    """Sync all series in a category.

    Parameters
    ----------
    cache : HistoricalCache
        Cache instance
    category : str
        Category name

    Returns
    -------
    int
        Exit code
    """
    logger.info("Syncing category", category=category)

    try:
        results = cache.sync_category(category)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    success_count = sum(1 for r in results if r.get("success", False))
    fail_count = len(results) - success_count

    print(
        f"\nCategory '{category}' sync completed: {success_count}/{len(results)} successful"
    )

    if fail_count > 0:
        print("\nFailed series:")
        for result in results:
            if not result.get("success", False):
                print(
                    f"  {result['series_id']}: {result.get('error', 'Unknown error')}"
                )

    return 0 if fail_count == 0 else 1


def _sync_series(cache: HistoricalCache, series_id: str) -> int:
    """Sync a single series.

    Parameters
    ----------
    cache : HistoricalCache
        Cache instance
    series_id : str
        FRED series ID

    Returns
    -------
    int
        Exit code
    """
    logger.info("Syncing single series", series_id=series_id)

    try:
        result = cache.sync_series(series_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if result.get("success", False):
        print(f"Series '{series_id}' synced successfully:")
        print(f"  Data points: {result.get('data_points', 0)}")
        print(f"  New points: {result.get('new_points', 0)}")
        return 0
    else:
        print(f"Failed to sync '{series_id}': {result.get('error', 'Unknown error')}")
        return 1


def main() -> int:
    """Main entry point.

    Returns
    -------
    int
        Exit code
    """
    args = parse_args()
    return run_sync(args)


if __name__ == "__main__":
    sys.exit(main())
