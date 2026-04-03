#!/usr/bin/env python3
"""Smoke test script for edgartools financial statement DataFrame shapes.

This script verifies the actual shape (column names, types, missing value
patterns) of DataFrames returned by edgartools financials before implementing
the Wave 4 SecEdgarCollector.

It also confirms that importlib-based import of the edgartools Company class
works correctly from our src/edgar package environment.

Examples
--------
Basic usage (AAPL, 10-K, limit=1):

    $ uv run python scripts/smoke_test_edgar.py

Custom symbol and filing type:

    $ uv run python scripts/smoke_test_edgar.py --symbol MSFT --filing-type 10-Q --limit 2

Notes
-----
- SEC_EDGAR_IDENTITY environment variable must be set before running.
  Format: "Your Name your@email.com"
- edgartools must be installed: uv add edgartools
- This script is a one-shot inspection tool; it does NOT persist data.
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import sys
from typing import Any

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# importlib helper (mirrors edgar/fetcher.py pattern)
# ---------------------------------------------------------------------------


def _load_company_class() -> Any:
    """Load the edgartools Company class via importlib from site-packages.

    This mirrors the pattern in ``edgar/fetcher.py:_import_edgartools_company()``
    to verify the importlib-based import works correctly in this environment.

    Returns
    -------
    type
        The edgartools Company class

    Raises
    ------
    RuntimeError
        If edgartools is not installed or Company is not found
    """
    site_packages_paths = [p for p in sys.path if "site-packages" in p]
    spec = importlib.machinery.PathFinder.find_spec("edgar", site_packages_paths)

    if spec is None or spec.origin is None:
        msg = "edgartools is not installed. Run: uv add edgartools"
        raise RuntimeError(msg)

    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        msg = "Failed to load edgartools module: loader is None"
        raise RuntimeError(msg)

    spec.loader.exec_module(mod)

    company_cls = getattr(mod, "Company", None)
    if company_cls is None:
        msg = "edgartools module does not export 'Company' class"
        raise RuntimeError(msg)

    logger.info(
        "edgartools Company class loaded via importlib",
        module_origin=spec.origin,
    )
    return company_cls


# ---------------------------------------------------------------------------
# DataFrame inspection helpers
# ---------------------------------------------------------------------------

_SEPARATOR = "-" * 72


def _print_separator(title: str = "") -> None:
    """Print a section separator with optional title."""
    if title:
        print(f"\n{'=' * 72}")
        print(f"  {title}")
        print("=" * 72)
    else:
        print(_SEPARATOR)


def _inspect_dataframe(name: str, df: pd.DataFrame) -> None:
    """Print dtypes, shape, head(), and missing-value summary for a DataFrame.

    Parameters
    ----------
    name : str
        Human-readable name for the statement (e.g., "Income Statement")
    df : pd.DataFrame
        The DataFrame to inspect
    """
    _print_separator(name)
    print(f"Shape   : {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns : {list(df.columns)}")
    print()

    print("--- dtypes ---")
    print(df.dtypes.to_string())
    print()

    print("--- head(5) ---")
    print(df.head(5).to_string())
    print()

    # Missing-value summary
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if null_cols.empty:
        print("--- missing values: none ---")
    else:
        print(f"--- missing values ({len(null_cols)} columns with nulls) ---")
        print(null_cols.to_string())

    print()


def _inspect_cf_standard_concept(cf_df: pd.DataFrame) -> None:
    """Print the count of missing ``standard_concept`` entries in the CF DataFrame.

    Parameters
    ----------
    cf_df : pd.DataFrame
        Cash Flow statement DataFrame
    """
    _print_separator("CF standard_concept missing-value analysis")

    col = "standard_concept"
    if col not in cf_df.columns:
        print(f"  Column '{col}' not present in Cash Flow DataFrame.")
        print(f"  Available columns: {list(cf_df.columns)}")
        return

    total = len(cf_df)
    missing = cf_df[col].isnull().sum()
    present = total - missing

    print(f"  Total rows          : {total}")
    print(f"  standard_concept present : {present}")
    print(f"  standard_concept missing : {missing}")
    if total > 0:
        print(f"  Missing rate        : {missing / total:.1%}")

    if missing > 0:
        print()
        print("  Sample rows where standard_concept is missing:")
        sample_cols = [c for c in cf_df.columns if c != col][:5]
        print(cf_df[cf_df[col].isnull()][[*sample_cols, col]].head(5).to_string())

    print()


# ---------------------------------------------------------------------------
# Core smoke-test logic
# ---------------------------------------------------------------------------


def run_smoke_test(
    symbol: str,
    filing_type: str,
    limit: int,
) -> None:
    """Run the edgartools smoke test for the given symbol and filing type.

    Fetches up to ``limit`` filings, calls ``.obj().financials.to_dataframe()``
    on the first available filing, and prints DataFrame inspection results for
    IS, BS, and CF statements.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g., "AAPL")
    filing_type : str
        SEC form type (e.g., "10-K", "10-Q")
    limit : int
        Maximum number of filings to inspect (each is inspected separately)

    Raises
    ------
    RuntimeError
        If no filings are found or financials cannot be extracted
    """
    _print_separator(f"Smoke Test: {symbol} / {filing_type} / limit={limit}")

    # Step 1: Load Company class via importlib
    company_cls = _load_company_class()
    print(f"[OK] importlib import succeeded: {company_cls}")

    # Step 2: Fetch filings
    print(f"\nFetching {filing_type} filings for {symbol} (limit={limit}) ...")
    company = company_cls(symbol)
    filings_collection = company.get_filings(form=filing_type)
    filings = list(filings_collection.latest(limit))

    if not filings:
        msg = f"No {filing_type} filings found for {symbol}"
        raise RuntimeError(msg)

    print(f"[OK] {len(filings)} filing(s) fetched")

    # Step 3: Inspect each filing
    for idx, filing in enumerate(filings):
        _print_separator(f"Filing {idx + 1}/{len(filings)}")

        accession = getattr(filing, "accession_no", str(filing))
        period = getattr(filing, "period_of_report", "unknown")
        print(f"  Accession : {accession}")
        print(f"  Period    : {period}")

        # Obtain the filing object (may trigger network fetch)
        try:
            filing_obj = filing.obj()
        except Exception as exc:
            logger.warning(
                "Failed to load filing object",
                accession=accession,
                error=str(exc),
            )
            print(f"  [WARN] Could not load filing object: {exc}")
            continue

        financials = getattr(filing_obj, "financials", None)
        if financials is None:
            print("  [WARN] Filing has no 'financials' attribute – skipping")
            continue

        # Income Statement
        try:
            is_df: pd.DataFrame = financials.income_statement.to_dataframe()
            _inspect_dataframe("Income Statement (IS)", is_df)
        except Exception as exc:
            print(f"  [WARN] IS extraction failed: {exc}")

        # Balance Sheet
        try:
            bs_df: pd.DataFrame = financials.balance_sheet.to_dataframe()
            _inspect_dataframe("Balance Sheet (BS)", bs_df)
        except Exception as exc:
            print(f"  [WARN] BS extraction failed: {exc}")

        # Cash Flow Statement
        try:
            cf_df: pd.DataFrame = financials.cash_flow_statement.to_dataframe()
            _inspect_dataframe("Cash Flow Statement (CF)", cf_df)
            _inspect_cf_standard_concept(cf_df)
        except Exception as exc:
            print(f"  [WARN] CF extraction failed: {exc}")

    _print_separator("Smoke test completed successfully")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=(
            "Smoke test for edgartools financial statement DataFrame shapes. "
            "Requires SEC_EDGAR_IDENTITY env var."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run python scripts/smoke_test_edgar.py\n"
            "  uv run python scripts/smoke_test_edgar.py --symbol MSFT --filing-type 10-Q\n"
        ),
    )
    parser.add_argument(
        "--symbol",
        default="AAPL",
        help="Ticker symbol to inspect (default: AAPL)",
    )
    parser.add_argument(
        "--filing-type",
        default="10-K",
        help="SEC form type to fetch (default: 10-K)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Maximum number of filings to inspect (default: 3)",
    )
    return parser


def main() -> None:
    """CLI entry point for the smoke test script."""
    import os

    parser = build_parser()
    args = parser.parse_args()

    # Validate SEC_EDGAR_IDENTITY
    identity = os.environ.get("SEC_EDGAR_IDENTITY", "")
    if not identity.strip():
        print(
            "ERROR: SEC_EDGAR_IDENTITY environment variable is not set.\n"
            "Set it before running:\n"
            '  export SEC_EDGAR_IDENTITY="Your Name your@email.com"',
            file=sys.stderr,
        )
        sys.exit(1)

    # Configure edgartools identity (mirrors edgar/config.py:_configure_edgartools)
    try:
        site_packages_paths = [p for p in sys.path if "site-packages" in p]
        spec = importlib.machinery.PathFinder.find_spec("edgar", site_packages_paths)
        if spec is not None and spec.origin is not None:
            mod = importlib.util.module_from_spec(spec)
            if spec.loader is not None:
                spec.loader.exec_module(mod)
                if hasattr(mod, "set_identity"):
                    mod.set_identity(identity)
                    masked = (identity.split()[0] + " ***") if identity else ""
                    logger.debug("edgartools identity configured", identity=masked)
    except Exception:
        logger.debug("Could not configure edgartools identity", exc_info=True)

    try:
        run_smoke_test(
            symbol=args.symbol,
            filing_type=args.filing_type,
            limit=args.limit,
        )
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
