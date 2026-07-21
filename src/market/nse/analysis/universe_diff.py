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


def find_post_cutoff_listings(
    stocks: pd.DataFrame, cutoff: str | pd.Timestamp
) -> list[str]:
    """基準日より後に上場した銘柄を検出する.

    NSE の指数構成 API は point-in-time 取得に対応しておらず、基準日より後に
    取得した構成データを使うと、基準日時点で未上場の銘柄が universe に混入する。
    本関数はその混入分を検出し、universe から除外できるようにする。

    Parameters
    ----------
    stocks : pd.DataFrame
        ``symbol`` と ``listing_date`` 列を持つ銘柄マスタ。``listing_date`` は
        NSE の EQUITY_L.csv 形式（``DD-MMM-YYYY``、例 ``03-JUL-2026``）を想定する。
    cutoff : str | pd.Timestamp
        基準日。この日より後に上場した銘柄が検出対象となる。基準日当日の
        上場は「基準日時点で上場済み」として検出対象に含めない。

    Returns
    -------
    list[str]
        基準日より後に上場した symbol のリスト（昇順）。``listing_date`` が
        欠損または解釈不能な銘柄は、誤除外を避けるため検出対象に含めない。

    Raises
    ------
    KeyError
        ``stocks`` が ``symbol`` または ``listing_date`` 列を持たない場合。

    Examples
    --------
    >>> import pandas as pd
    >>> stocks = pd.DataFrame(
    ...     {
    ...         "symbol": ["AGL", "RELIANCE"],
    ...         "listing_date": ["03-JUL-2026", "29-NOV-1995"],
    ...     }
    ... )
    >>> find_post_cutoff_listings(stocks, "2026-06-30")
    ['AGL']
    """
    missing = {"symbol", "listing_date"} - set(stocks.columns)
    if missing:
        msg = f"DataFrame is missing required column(s): {sorted(missing)}"
        raise KeyError(msg)

    cutoff_ts = pd.Timestamp(cutoff)
    # NSE の EQUITY_L.csv は DD-MMM-YYYY 形式。文字列のままでは日付比較が
    # 成立しないため必ず Timestamp に変換する。解釈できない値は NaT となり、
    # 比較結果が False になるので保守的に「除外しない」挙動となる。
    listed_at = pd.to_datetime(
        stocks["listing_date"], format="%d-%b-%Y", errors="coerce"
    )
    post_cutoff = stocks.loc[listed_at > cutoff_ts, "symbol"]

    result = sorted(post_cutoff.astype(str).str.strip().str.upper())

    logger.info(
        "Post-cutoff listings detected",
        cutoff=str(cutoff_ts.date()),
        total_count=len(stocks),
        post_cutoff_count=len(result),
    )

    return result


__all__ = ["UniverseDiff", "diff_universe", "find_post_cutoff_listings"]
