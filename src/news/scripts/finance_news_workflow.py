#!/usr/bin/env python
"""Finance news collection workflow CLI.

This module provides the CLI entry point for the news collection workflow,
orchestrating the complete pipeline: Collector -> Extractor -> Summarizer -> Publisher.

Usage
-----
Run with default configuration:

    python -m news.scripts.finance_news_workflow

Run in dry-run mode (skip Issue creation):

    python -m news.scripts.finance_news_workflow --dry-run

Filter by status:

    python -m news.scripts.finance_news_workflow --status index,stock

Limit articles:

    python -m news.scripts.finance_news_workflow --max-articles 10

Enable verbose logging:

    python -m news.scripts.finance_news_workflow --verbose

Use a specific config file:

    python -m news.scripts.finance_news_workflow --config data/config/news-collection-config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from news.config.workflow import load_config
from news.orchestrator import NewsWorkflowOrchestrator
from news.utils.logging_config import get_logger, set_log_level

if TYPE_CHECKING:
    from news.models import WorkflowResult

logger = get_logger(__name__, module="scripts.finance_news_workflow")

# Default configuration file path
DEFAULT_CONFIG_PATH = Path("data/config/news-collection-config.yaml")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the workflow script.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser with all supported options.

    Examples
    --------
    >>> parser = create_parser()
    >>> args = parser.parse_args(["--dry-run", "--status", "index"])
    >>> args.dry_run
    True
    >>> args.status
    'index'
    """
    parser = argparse.ArgumentParser(
        prog="finance-news-workflow",
        description="Run the finance news collection workflow pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s                                Run with default config
  %(prog)s --dry-run                      Run without creating Issues
  %(prog)s --status index,stock           Filter by status
  %(prog)s --max-articles 10              Limit to 10 articles
  %(prog)s --config config.yaml           Use specific config file
""",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file (default: data/config/news-collection-config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run workflow without creating GitHub Issues",
    )

    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Comma-separated list of statuses to filter by (e.g., 'index,stock')",
    )

    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Maximum number of articles to process",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG level) logging output",
    )

    return parser


def parse_statuses(status_str: str | None) -> list[str] | None:
    """Parse comma-separated status string into a list.

    Parameters
    ----------
    status_str : str | None
        Comma-separated status string, or None.

    Returns
    -------
    list[str] | None
        List of status strings, or None if input was None.

    Examples
    --------
    >>> parse_statuses("index,stock")
    ['index', 'stock']
    >>> parse_statuses("index")
    ['index']
    >>> parse_statuses(None) is None
    True
    """
    if status_str is None:
        return None
    return [s.strip() for s in status_str.split(",")]


def print_result_summary(result: WorkflowResult) -> None:
    """Print workflow result summary to stdout.

    Parameters
    ----------
    result : WorkflowResult
        The workflow execution result to print.

    Examples
    --------
    >>> print_result_summary(result)
    === Workflow Result ===
    Collected: 10
    ...
    """
    print("\n=== Workflow Result ===")
    print(f"Collected: {result.total_collected}")
    print(f"Extracted: {result.total_extracted}")
    print(f"Summarized: {result.total_summarized}")
    print(f"Published: {result.total_published}")
    print(f"Duplicates: {result.total_duplicates}")
    print(f"Elapsed: {result.elapsed_seconds:.1f}s")


async def run_workflow(
    config_path: Path,
    dry_run: bool = False,
    statuses: list[str] | None = None,
    max_articles: int | None = None,
) -> int:
    """Run the workflow asynchronously.

    Parameters
    ----------
    config_path : Path
        Path to the configuration file.
    dry_run : bool, optional
        If True, skip actual Issue creation. Default is False.
    statuses : list[str] | None, optional
        Filter articles by status. None means no filtering.
    max_articles : int | None, optional
        Maximum number of articles to process. None means no limit.

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.
    """
    logger.info(
        "Starting finance news workflow",
        config_path=str(config_path),
        dry_run=dry_run,
        statuses=statuses,
        max_articles=max_articles,
    )

    try:
        config = load_config(config_path)
        orchestrator = NewsWorkflowOrchestrator(config)

        result = await orchestrator.run(
            statuses=statuses,
            max_articles=max_articles,
            dry_run=dry_run,
        )

        print_result_summary(result)

        logger.info(
            "Workflow completed successfully",
            total_collected=result.total_collected,
            total_published=result.total_published,
            elapsed_seconds=result.elapsed_seconds,
        )

        return 0

    except FileNotFoundError as e:
        logger.error("Configuration file not found", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(
            "Workflow failed with exception",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the finance news workflow script.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command line arguments. If None, uses sys.argv[1:].

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.

    Examples
    --------
    >>> exit_code = main(["--dry-run"])
    >>> exit_code
    0

    >>> exit_code = main(["--config", "config.yaml", "--status", "index"])
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Set log level to DEBUG if verbose mode is enabled
    if args.verbose:
        set_log_level("DEBUG")

    logger.info(
        "Finance news workflow script started",
        config=args.config,
        dry_run=args.dry_run,
        status=args.status,
        max_articles=args.max_articles,
        verbose=args.verbose,
    )

    # Determine config path
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH

    # Parse statuses
    statuses = parse_statuses(args.status)

    # Run the workflow
    return asyncio.run(
        run_workflow(
            config_path=config_path,
            dry_run=args.dry_run,
            statuses=statuses,
            max_articles=args.max_articles,
        )
    )


if __name__ == "__main__":
    sys.exit(main())


# Export all public symbols
__all__ = [
    "DEFAULT_CONFIG_PATH",
    "create_parser",
    "main",
    "parse_statuses",
    "print_result_summary",
    "run_workflow",
]
