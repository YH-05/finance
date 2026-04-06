"""Command-line interface for the earnings data pipeline.

Provides a ``main()`` function (called by ``__main__.py``) that parses
argparse arguments and delegates to ``EarningsPipeline``.

Usage
-----
::

    python -m market.pipeline [options]

Options
-------
--days-back INT
    Days before today to include in the earnings calendar window.
    Default: 7.
--days-forward INT
    Days after today to include in the earnings calendar window.
    Default: 7.
--phase INT
    Run a single phase only (1–4). Cannot be combined with
    ``--skip-phases``.
--skip-phases INT [INT ...]
    One or more phase numbers to skip.
--av-budget INT
    Alpha Vantage daily API-call budget. Default: 25.
--status
    Print queue statistics and exit without running any phase.
--reset-failed
    Reset failed queue entries back to pending, then exit.
--dry-run
    Print what would be executed without running any phase.

Examples
--------
::

    # Full pipeline with default settings
    python -m market.pipeline

    # Status check (never crashes when DB is empty)
    python -m market.pipeline --status

    # Skip AV and SEC phases
    python -m market.pipeline --skip-phases 2 3

    # Run only Phase 1
    python -m market.pipeline --phase 1

    # Reset failed entries
    python -m market.pipeline --reset-failed

See Also
--------
market.pipeline.pipeline : ``EarningsPipeline``
"""

from __future__ import annotations

import argparse
import json
import sys

from market.pipeline.pipeline import EarningsPipeline
from market.pipeline.queue import CollectionQueue
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m market.pipeline",
        description="Earnings data collection pipeline (4 phases).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m market.pipeline                    # full pipeline\n"
            "  python -m market.pipeline --status           # queue statistics\n"
            "  python -m market.pipeline --phase 1          # phase 1 only\n"
            "  python -m market.pipeline --skip-phases 2 3  # skip AV + SEC\n"
            "  python -m market.pipeline --reset-failed     # reset failed entries\n"
            "  python -m market.pipeline --dry-run          # preview execution\n"
        ),
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        metavar="INT",
        help="Days before today to include in the earnings calendar window. (default: 7)",
    )
    parser.add_argument(
        "--days-forward",
        type=int,
        default=7,
        metavar="INT",
        help="Days after today to include in the earnings calendar window. (default: 7)",
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        metavar="INT",
        help="Run a single phase only (1–4). Cannot be combined with --skip-phases.",
    )
    parser.add_argument(
        "--skip-phases",
        type=int,
        nargs="+",
        metavar="INT",
        help="Phase numbers to skip (e.g. --skip-phases 2 3).",
    )
    parser.add_argument(
        "--av-budget",
        type=int,
        default=None,
        metavar="INT",
        help=(
            "Alpha Vantage daily API-call budget. "
            "When omitted, automatically computed from the number of configured API keys "
            "(key_count * 25). (default: auto)"
        ),
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print queue statistics and exit.",
    )
    parser.add_argument(
        "--reset-failed",
        action="store_true",
        help="Reset failed queue entries to pending, then exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed without running any phase.",
    )

    return parser


# ---------------------------------------------------------------------------
# Helper: validate mutually exclusive options
# ---------------------------------------------------------------------------


def _resolve_skip_phases(
    phase: int | None,
    skip_phases: list[int] | None,
) -> list[int] | None:
    """Resolve the effective ``skip_phases`` list.

    If ``--phase`` is specified, compute the phases to skip by excluding
    the requested phase from [1, 2, 3, 4]. ``--skip-phases`` and ``--phase``
    are mutually exclusive.

    Parameters
    ----------
    phase : int | None
        Single phase to run (all others will be skipped).
    skip_phases : list[int] | None
        Explicit skip list from the CLI.

    Returns
    -------
    list[int] | None
        Resolved skip list, or ``None`` (run all phases).

    Raises
    ------
    SystemExit
        When ``--phase`` and ``--skip-phases`` are both provided.
    """
    if phase is not None and skip_phases:
        print(
            "error: --phase and --skip-phases are mutually exclusive.",
            file=sys.stderr,
        )
        sys.exit(2)

    if phase is not None:
        return [p for p in [1, 2, 3, 4] if p != phase]

    return skip_phases


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the earnings pipeline CLI.

    Parameters
    ----------
    argv : list[str] | None
        Argument list (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code: 0 on success, 1 on error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- --status mode ---
    if args.status:
        try:
            pipeline = EarningsPipeline(
                av_daily_budget=args.av_budget,
            )
            status = pipeline.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return 0
        except Exception as exc:
            logger.error("Status check failed", exc_info=True)
            print(f"error: {exc}", file=sys.stderr)
            return 1

    # --- --reset-failed mode ---
    if args.reset_failed:
        try:
            queue = CollectionQueue()
            reset_count = queue.reset_failed(priority_boost=10)
            print(f"Reset {reset_count} failed entries to pending (priority_boost=10).")
            return 0
        except Exception as exc:
            logger.error("reset-failed failed", exc_info=True)
            print(f"error: {exc}", file=sys.stderr)
            return 1

    # Resolve skip_phases
    skip_phases = _resolve_skip_phases(args.phase, args.skip_phases)

    # --- --dry-run mode ---
    if args.dry_run:
        effective_phases = [p for p in [1, 2, 3, 4] if p not in (skip_phases or [])]
        av_budget_display = args.av_budget if args.av_budget is not None else "auto"
        print("Dry-run mode. Would execute:")
        print(f"  phases:       {effective_phases}")
        print(f"  days_back:    {args.days_back}")
        print(f"  days_forward: {args.days_forward}")
        print(f"  av_budget:    {av_budget_display}")
        return 0

    # --- Normal pipeline run ---
    try:
        pipeline = EarningsPipeline(av_daily_budget=args.av_budget)
        result = pipeline.run(
            days_back=args.days_back,
            days_forward=args.days_forward,
            skip_phases=skip_phases,
        )

        # Print brief summary to stdout
        _print_result_summary(result)
        return 0

    except Exception as exc:
        logger.error("Pipeline run failed", exc_info=True)
        print(f"error: {exc}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Result summary printer
# ---------------------------------------------------------------------------


def _print_result_summary(result: object) -> None:
    """Print a human-readable summary of a ``PipelineResult``."""
    from market.pipeline.models import PipelineResult

    if not isinstance(result, PipelineResult):
        print(f"Result: {result}")
        return

    print(f"Pipeline completed in {result.total_duration_sec:.2f}s")
    for attr, label in [
        ("phase1", "Phase 1 (NASDAQ calendar)"),
        ("phase2", "Phase 2 (Alpha Vantage)"),
        ("phase3", "Phase 3 (SEC EDGAR)"),
        ("phase4", "Phase 4 (Yahoo Finance)"),
    ]:
        phase_result = getattr(result, attr)
        if phase_result is None:
            print(f"  {label}: skipped")
        else:
            print(
                f"  {label}: "
                f"ok={phase_result.success_count} "
                f"fail={phase_result.fail_count} "
                f"skip={phase_result.skip_count} "
                f"({phase_result.duration_sec:.2f}s)"
            )
            for err in phase_result.errors:
                print(f"    [error] {err}")


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = ["main"]
