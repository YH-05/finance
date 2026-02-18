"""Run transcript parsing for monthly files with optional date-range filtering.

Executes TranscriptParser.parse_all_months() against S&P Capital IQ
monthly transcript exports, producing per-ticker structured JSON files
for the CA Strategy pipeline.

By default, parses 2015-01 to 2015-09 (the PoC target range).
Use ``--start-month`` / ``--end-month`` to adjust the range.

Usage
-----
Default (2015-01 to 2015-09)::

    uv run python -m dev.ca_strategy.run_parse_transcripts \
        --source-dir /path/to/data/Transcript

All months in the source directory::

    uv run python -m dev.ca_strategy.run_parse_transcripts \
        --source-dir /path/to/data/Transcript --all-months

Custom range::

    uv run python -m dev.ca_strategy.run_parse_transcripts \
        --source-dir /path/to/data/Transcript \
        --start-month 2015-01 --end-month 2015-09
"""

from __future__ import annotations

import argparse
import json
import re as _re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

from dev.ca_strategy.transcript_parser import ParseResult, TranscriptParser
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Default paths and date range
# ---------------------------------------------------------------------------
DEFAULT_SOURCE_DIR = Path("data/Transcript")
DEFAULT_OUTPUT_DIR = Path("research/ca_strategy_poc/transcripts")
DEFAULT_TICKER_MAPPING = Path("research/ca_strategy_poc/config/ticker_mapping.json")
DEFAULT_START_MONTH = "2015-01"
DEFAULT_END_MONTH = "2015-09"


_MONTH_FORMAT = _re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _validate_month(value: str) -> str:
    """Validate YYYY-MM month format."""
    if not _MONTH_FORMAT.match(value):
        msg = f"Invalid month format: {value!r}. Expected YYYY-MM (e.g. 2015-01)"
        raise argparse.ArgumentTypeError(msg)
    return value


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser for transcript parsing runner.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Parse S&P Capital IQ transcript JSONs into per-ticker files.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"Directory containing list_transcript_YYYY-MM.json files (default: {DEFAULT_SOURCE_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for parsed transcripts (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--ticker-mapping",
        type=Path,
        default=DEFAULT_TICKER_MAPPING,
        help=f"Path to ticker_mapping.json (default: {DEFAULT_TICKER_MAPPING})",
    )
    parser.add_argument(
        "--start-month",
        type=_validate_month,
        default=DEFAULT_START_MONTH,
        help=f"Start month in YYYY-MM format (default: {DEFAULT_START_MONTH})",
    )
    parser.add_argument(
        "--end-month",
        type=_validate_month,
        default=DEFAULT_END_MONTH,
        help=f"End month in YYYY-MM format (default: {DEFAULT_END_MONTH})",
    )
    parser.add_argument(
        "--all-months",
        action="store_true",
        help="Parse all months in the source directory (ignore start/end month)",
    )
    return parser


def _filter_source_files(
    source_dir: Path,
    start_month: str,
    end_month: str,
) -> Path:
    """Create a temporary directory with symlinks to files in the date range.

    Parameters
    ----------
    source_dir : Path
        Original source directory containing all monthly files.
    start_month : str
        Start month in YYYY-MM format (inclusive).
    end_month : str
        End month in YYYY-MM format (inclusive).

    Returns
    -------
    Path
        Path to temporary directory containing only the filtered files.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="transcript_parse_"))
    included_count = 0
    excluded_count = 0

    for filepath in sorted(source_dir.glob("list_transcript_*.json")):
        # Extract YYYY-MM from filename
        stem = filepath.stem  # list_transcript_2015-01
        month_str = stem.replace("list_transcript_", "")  # 2015-01

        if start_month <= month_str <= end_month:
            # Create symlink in temp directory
            link_path = temp_dir / filepath.name
            link_path.symlink_to(filepath.resolve())
            included_count += 1
        else:
            excluded_count += 1

    logger.info(
        "Source files filtered by date range",
        start_month=start_month,
        end_month=end_month,
        included=included_count,
        excluded=excluded_count,
    )

    return temp_dir


def _print_summary(
    result: ParseResult,
    output_dir: Path,
    ticker_mapping_path: Path,
) -> None:
    """Print parsing summary with per-ticker and truncation statistics.

    Parameters
    ----------
    result : ParseResult
        Result from TranscriptParser.parse_all_months().
    output_dir : Path
        Output directory to scan for generated files.
    ticker_mapping_path : Path
        Path to ticker_mapping.json for unknown ticker reporting.
    """
    # Collect per-ticker stats from output directory
    ticker_dirs = sorted(d for d in output_dir.iterdir() if d.is_dir())
    ticker_file_counts: dict[str, int] = {}
    truncation_counts: Counter[str] = Counter()
    total_truncated = 0

    for ticker_dir in ticker_dirs:
        files = list(ticker_dir.glob("*_earnings_call.json"))
        ticker_file_counts[ticker_dir.name] = len(files)

        # Check truncation metadata in each file
        for filepath in files:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                if data.get("metadata", {}).get("is_truncated", False):
                    truncation_counts[ticker_dir.name] += 1
                    total_truncated += 1
            except (json.JSONDecodeError, OSError):
                pass

    logger.info(
        "=== Transcript Parsing Summary ===",
        total_records=result.total_count,
        success=result.success_count,
        errors=result.error_count,
        unique_tickers=len(ticker_file_counts),
        total_files_generated=sum(ticker_file_counts.values()),
        truncated_transcripts=total_truncated,
    )

    # Per-ticker breakdown
    for ticker, count in sorted(ticker_file_counts.items()):
        trunc_count = truncation_counts.get(ticker, 0)
        trunc_label = f" (truncated: {trunc_count})" if trunc_count > 0 else ""
        logger.info(
            f"  {ticker}: {count} file(s){trunc_label}",
        )

    # Report errors
    if result.errors:
        logger.warning("=== Parsing Errors ===")
        for error_msg in result.errors:
            logger.warning(f"  {error_msg}")

    # Report ticker mapping status
    if ticker_mapping_path.exists():
        mapping = json.loads(ticker_mapping_path.read_text(encoding="utf-8"))
        logger.info(
            "Ticker mapping entries",
            count=len(mapping),
            path=str(ticker_mapping_path),
        )


def _detect_unknown_tickers(
    output_dir: Path,
    ticker_mapping_path: Path,
) -> list[str]:
    """Detect tickers that start with digits and are not in ticker_mapping.

    Parameters
    ----------
    output_dir : Path
        Output directory containing per-ticker subdirectories.
    ticker_mapping_path : Path
        Path to ticker_mapping.json.

    Returns
    -------
    list[str]
        List of unknown digit-starting ticker names found in output.
    """
    # Load current mapping
    if ticker_mapping_path.exists():
        mapping: dict[str, dict[str, str]] = json.loads(
            ticker_mapping_path.read_text(encoding="utf-8")
        )
    else:
        mapping = {}

    # Scan output directories for digit-starting tickers
    unknown: list[str] = []
    if output_dir.exists():
        for ticker_dir in output_dir.iterdir():
            if ticker_dir.is_dir():
                name = ticker_dir.name
                if name and name[0].isdigit() and name not in mapping:
                    unknown.append(name)

    return sorted(unknown)


def main() -> int:
    """Execute transcript parsing and print summary.

    Returns
    -------
    int
        Exit code (0 for success, 1 for errors).
    """
    args = _build_parser().parse_args()
    source_dir: Path = args.source_dir
    output_dir: Path = args.output_dir
    ticker_mapping_path: Path = args.ticker_mapping
    all_months: bool = args.all_months
    start_month: str = args.start_month
    end_month: str = args.end_month

    # Validate source directory
    if not source_dir.exists():
        logger.error(
            "Source directory not found",
            source_dir=str(source_dir),
        )
        return 1

    # Determine effective source directory (with optional filtering)
    effective_source_dir = source_dir
    temp_dir: Path | None = None

    if not all_months:
        temp_dir = _filter_source_files(source_dir, start_month, end_month)
        effective_source_dir = temp_dir

    try:
        # Log configuration
        logger.info(
            "Transcript parsing configuration",
            source_dir=str(source_dir),
            effective_source_dir=str(effective_source_dir),
            output_dir=str(output_dir),
            ticker_mapping=str(ticker_mapping_path),
            date_range=f"{start_month} to {end_month}" if not all_months else "all",
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run parser
        parser = TranscriptParser(
            source_dir=effective_source_dir,
            output_dir=output_dir,
            ticker_mapping_path=ticker_mapping_path,
        )
        result = parser.parse_all_months()

        # Print summary
        _print_summary(result, output_dir, ticker_mapping_path)

        # Detect unknown tickers
        unknown_tickers = _detect_unknown_tickers(output_dir, ticker_mapping_path)
        if unknown_tickers:
            logger.warning(
                "Unknown digit-starting tickers detected (not in ticker_mapping.json)",
                tickers=unknown_tickers,
                count=len(unknown_tickers),
            )
            logger.info(
                "Consider adding these to ticker_mapping.json with proper ticker names"
            )

        if result.error_count > 0:
            logger.warning(
                "Parsing completed with errors",
                error_count=result.error_count,
            )
            return 1

        logger.info("Parsing completed successfully")
        return 0

    finally:
        # Clean up temporary directory
        if temp_dir is not None and temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug("Temporary directory cleaned up", temp_dir=str(temp_dir))


if __name__ == "__main__":
    sys.exit(main())
