"""Universe diff detection for the NSE owner-company screening pipeline.

This module compares a previously confirmed NIFTY 750 universe snapshot
against a newly fetched index constituent DataFrame (e.g. from
``IndicesCollector.fetch_index("NIFTY TOTAL MKT")``) and detects which
symbols were newly added, removed, or unchanged. This supports the
incremental universe update workflow that runs after each NSE index
reconstitution (effective end of March / September).

See Also
--------
market.nse.collectors.indices.IndicesCollector : Source of the current
    universe DataFrame via ``fetch_index()``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class UniverseDiff:
    """Result of comparing two universe snapshots.

    Parameters
    ----------
    added : list[str]
        Symbols present in the current universe but not in the previous
        one, sorted alphabetically.
    removed : list[str]
        Symbols present in the previous universe but not in the current
        one, sorted alphabetically.
    unchanged : list[str]
        Symbols present in both universes, sorted alphabetically.

    Examples
    --------
    >>> diff = UniverseDiff(added=["WIPRO"], removed=["RELIANCE"], unchanged=["INFY"])
    >>> diff.added
    ['WIPRO']
    """

    added: list[str]
    removed: list[str]
    unchanged: list[str]


def _normalize_symbols(df: pd.DataFrame) -> set[str]:
    """Extract the ``symbol`` column and normalize values into a set.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a ``symbol`` column.

    Returns
    -------
    set[str]
        Normalized symbols (stripped of whitespace, upper-cased).

    Raises
    ------
    KeyError
        If ``df`` does not have a ``symbol`` column.
    """
    if "symbol" not in df.columns:
        msg = "DataFrame is missing required 'symbol' column"
        raise KeyError(msg)

    return set(df["symbol"].astype(str).str.strip().str.upper())


def diff_universe(previous: pd.DataFrame, current: pd.DataFrame) -> UniverseDiff:
    """Compare two universe snapshots and detect added/removed/unchanged symbols.

    Parameters
    ----------
    previous : pd.DataFrame
        Previously confirmed universe snapshot with a ``symbol`` column
        (e.g. ``nifty750_universe.csv``).
    current : pd.DataFrame
        Newly fetched index constituent DataFrame with a ``symbol`` column
        (e.g. from ``IndicesCollector.fetch_index("NIFTY TOTAL MKT")``).

    Returns
    -------
    UniverseDiff
        Added / removed / unchanged symbol lists, each sorted
        alphabetically. Symbols are normalized (stripped, upper-cased)
        before comparison.

    Raises
    ------
    KeyError
        If ``previous`` or ``current`` is missing the ``symbol`` column.

    Examples
    --------
    >>> import pandas as pd
    >>> previous = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
    >>> current = pd.DataFrame({"symbol": ["INFY", "WIPRO"]})
    >>> diff = diff_universe(previous, current)
    >>> diff.added
    ['WIPRO']
    >>> diff.removed
    ['RELIANCE']
    >>> diff.unchanged
    ['INFY']
    """
    logger.debug(
        "Diffing universe",
        previous_count=len(previous),
        current_count=len(current),
    )

    previous_symbols = _normalize_symbols(previous)
    current_symbols = _normalize_symbols(current)

    added = sorted(current_symbols - previous_symbols)
    removed = sorted(previous_symbols - current_symbols)
    unchanged = sorted(previous_symbols & current_symbols)

    result = UniverseDiff(added=added, removed=removed, unchanged=unchanged)

    logger.info(
        "Universe diff computed",
        added_count=len(added),
        removed_count=len(removed),
        unchanged_count=len(unchanged),
    )

    return result


__all__ = ["UniverseDiff", "diff_universe"]
