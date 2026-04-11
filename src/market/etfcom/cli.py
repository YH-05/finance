"""Command-line interface for the ETF.com data collection pipeline.

Provides a ``main()`` function (called by ``__main__.py``) that parses
argparse arguments and delegates to ``ETFComCollector``.

Usage
-----
::

    python -m market.etfcom [options]

Options
-------
--frequency {daily,weekly,monthly,all}
    Collection frequency to run. Default: all.
--tickers TICKER [TICKER ...]
    Space-separated list of ETF ticker symbols (e.g. SPY QQQ IWM).
    Comma-separated input is also accepted (e.g. SPY,QQQ,IWM).
    Mutually exclusive with ``--tickers-file``.
--tickers-file PATH
    Path to a JSON file containing a list of ticker symbols.
    Mutually exclusive with ``--tickers``.
--dry-run
    Print what would be executed without running any collection.

Examples
--------
::

    # Collect all frequencies for SPY and QQQ
    python -m market.etfcom --frequency all --tickers SPY QQQ

    # Daily collection using comma-separated tickers
    python -m market.etfcom --frequency daily --tickers SPY,QQQ

    # Weekly collection using a tickers file
    python -m market.etfcom --frequency weekly --tickers-file data/config/etfcom_tickers.json

    # Preview what would run (no HTTP calls)
    python -m market.etfcom --dry-run --frequency monthly --tickers SPY

See Also
--------
market.etfcom.collector : ``ETFComCollector``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.etfcom.models import CollectionSummary

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Default tickers config path
# ---------------------------------------------------------------------------

_DEFAULT_TICKERS_FILE = Path("data/config/etfcom_tickers.json")

# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the ETF.com collection CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m market.etfcom",
        description="ETF.com data collection pipeline (daily / weekly / monthly).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m market.etfcom --frequency daily --tickers SPY QQQ\n"
            "  python -m market.etfcom --frequency daily --tickers SPY,QQQ\n"
            "  python -m market.etfcom --frequency weekly --tickers-file data/config/etfcom_tickers.json\n"
            "  python -m market.etfcom --frequency all --tickers SPY\n"
            "  python -m market.etfcom --dry-run --frequency monthly --tickers SPY\n"
        ),
    )

    parser.add_argument(
        "--frequency",
        choices=["daily", "weekly", "monthly", "all"],
        default="all",
        metavar="FREQ",
        help=("Collection frequency: daily | weekly | monthly | all. (default: all)"),
    )

    ticker_group = parser.add_mutually_exclusive_group()
    ticker_group.add_argument(
        "--tickers",
        nargs="+",
        metavar="TICKER",
        help=(
            "ETF ticker symbols to collect (space-separated or comma-separated). "
            "Example: SPY QQQ  or  SPY,QQQ,IWM"
        ),
    )
    ticker_group.add_argument(
        "--tickers-file",
        type=Path,
        metavar="PATH",
        help=(
            "Path to a JSON file containing a list of ticker symbols. "
            f"Default file when neither flag is specified: {_DEFAULT_TICKERS_FILE}"
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed without making any HTTP requests.",
    )

    return parser


# ---------------------------------------------------------------------------
# Helper: resolve tickers
# ---------------------------------------------------------------------------


def _resolve_tickers(
    tickers_arg: list[str] | None,
    tickers_file: Path | None,
) -> list[str]:
    """Resolve the effective list of ETF ticker symbols.

    Priority order:
    1. ``--tickers`` (inline, comma/space-separated)
    2. ``--tickers-file`` (JSON file path)
    3. Default file ``data/config/etfcom_tickers.json`` (if it exists)

    Parameters
    ----------
    tickers_arg : list[str] | None
        Ticker list from ``--tickers`` (may contain comma-joined values).
    tickers_file : Path | None
        Path to a JSON tickers file from ``--tickers-file``.

    Returns
    -------
    list[str]
        Resolved, deduplicated list of uppercase ticker symbols.

    Raises
    ------
    SystemExit
        When the specified or default tickers file cannot be parsed, or when
        no tickers can be resolved at all.
    """
    if tickers_arg is not None:
        # Accept both "SPY QQQ" and "SPY,QQQ,IWM" (and mixed)
        raw = [t.strip() for item in tickers_arg for t in item.split(",") if t.strip()]
        if not raw:
            print("error: --tickers provided but no symbols found.", file=sys.stderr)
            sys.exit(2)
        return list(dict.fromkeys(t.upper() for t in raw))

    effective_file = tickers_file if tickers_file is not None else _DEFAULT_TICKERS_FILE

    if not effective_file.exists():
        if tickers_file is not None:
            # User explicitly specified a file that doesn't exist — hard error
            print(
                f"error: tickers file not found: {effective_file}",
                file=sys.stderr,
            )
            sys.exit(2)
        # Default file missing — inform and exit
        print(
            f"error: no tickers provided and default config file not found: {effective_file}\n"
            "  Use --tickers SPY QQQ  or  --tickers-file <path>",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        with effective_file.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(
            f"error: failed to parse tickers file {effective_file}: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)

    if isinstance(data, list):
        raw = [str(t).strip() for t in data if str(t).strip()]
    elif isinstance(data, dict):
        # Accept {"tickers": ["SPY", ...]} or {"SPY": ..., "QQQ": ...} (key-based)
        if "tickers" in data and isinstance(data["tickers"], list):
            raw = [str(t).strip() for t in data["tickers"] if str(t).strip()]
        else:
            raw = [str(k).strip() for k in data if str(k).strip()]
    else:
        print(
            f"error: tickers file {effective_file} must contain a JSON array or object.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not raw:
        print(f"error: tickers file {effective_file} is empty.", file=sys.stderr)
        sys.exit(2)

    return list(dict.fromkeys(t.upper() for t in raw))


# ---------------------------------------------------------------------------
# Result summary printer
# ---------------------------------------------------------------------------


def _print_summary(summary: CollectionSummary, frequency: str) -> None:
    """Print a human-readable collection summary to stdout.

    Parameters
    ----------
    summary : CollectionSummary
        Aggregated collection result.
    frequency : str
        The frequency label that was run (e.g. ``"daily"``).
    """
    status = "FAILED" if summary.has_failures else "OK"
    print(
        f"[{frequency.upper()}] {status} — "
        f"tickers={summary.total_tickers} "
        f"ok={summary.successful} "
        f"fail={summary.failed} "
        f"rows={summary.total_rows}"
    )
    if summary.has_failures:
        for result in summary.results:
            if not result.success:
                print(
                    f"  [FAIL] {result.ticker}/{result.table}: {result.error_message}"
                )


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ETF.com collection CLI.

    Parameters
    ----------
    argv : list[str] | None
        Argument list (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code: 0 on success, 1 when any collection fails.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    tickers = _resolve_tickers(args.tickers, args.tickers_file)

    # --- --dry-run mode ---
    if args.dry_run:
        print("Dry-run mode. Would execute:")
        print(f"  frequency: {args.frequency}")
        print(f"  tickers:   {tickers}")
        return 0

    logger.info(
        "ETFCom CLI started",
        frequency=args.frequency,
        ticker_count=len(tickers),
    )

    from market.etfcom.collector import ETFComCollector

    collector = ETFComCollector()
    has_failure = False

    try:
        if args.frequency == "daily":
            summary = collector.collect_daily(tickers)
            _print_summary(summary, "daily")
            has_failure = summary.has_failures

        elif args.frequency == "weekly":
            summary = collector.collect_weekly(tickers)
            _print_summary(summary, "weekly")
            has_failure = summary.has_failures

        elif args.frequency == "monthly":
            summary = collector.collect_monthly(tickers)
            _print_summary(summary, "monthly")
            has_failure = summary.has_failures

        else:  # "all"
            summary = collector.collect_all(tickers)
            _print_summary(summary, "all")
            has_failure = summary.has_failures

    except Exception as exc:
        # AIDEV-NOTE: Individual collect_* errors are already caught inside
        # ETFComCollector and stored as CollectionResult(success=False).
        # This outer except catches unexpected infrastructure failures
        # (e.g. storage init error) so the process never crashes unhandled.
        logger.error("ETFCom CLI encountered unexpected error", exc_info=True)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if has_failure:
        logger.warning(
            "ETFCom CLI completed with partial failures",
            frequency=args.frequency,
        )
        return 1

    logger.info("ETFCom CLI completed successfully", frequency=args.frequency)
    return 0


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = ["main"]
