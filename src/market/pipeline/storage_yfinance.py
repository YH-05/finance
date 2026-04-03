"""SQLite storage layer for Yahoo Finance daily price data.

This module provides the ``YFinanceStorage`` class that manages the
``yf_daily_prices`` SQLite table for persisting Yahoo Finance OHLCV data.
It uses ``SQLiteClient`` from ``database.db`` for all database operations,
leveraging ``INSERT OR REPLACE`` for idempotent data updates.

Tables managed
--------------
- ``yf_daily_prices`` -- Yahoo Finance daily OHLCV price records
  (PK: ``symbol``, ``date``)

Examples
--------
>>> from pathlib import Path
>>> storage = YFinanceStorage(db_path=Path(":memory:"))
>>> tables = storage.get_table_names()
>>> "yf_daily_prices" in tables
True

See Also
--------
database.db.sqlite_client.SQLiteClient : Underlying SQLite client.
market.alphavantage.storage : Reference implementation pattern.
market.pipeline.constants : Table name and env var constants.
market.pipeline.models : Storage record dataclasses.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Any

from database.db.connection import get_db_path
from database.db.sqlite_client import SQLiteClient
from market.pipeline.constants import (
    PIPELINE_YFINANCE_DB_PATH_ENV,
    TABLE_YF_DAILY_PRICES,
    YFINANCE_DB_NAME,
)
from market.pipeline.errors import StorageError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Valid table names whitelist (SQL injection prevention)
# ============================================================================

_VALID_TABLE_NAMES: frozenset[str] = frozenset({TABLE_YF_DAILY_PRICES})

# ============================================================================
# Table DDL definitions
# ============================================================================

_TABLE_DDL: dict[str, str] = {
    TABLE_YF_DAILY_PRICES: f"""
        CREATE TABLE IF NOT EXISTS {TABLE_YF_DAILY_PRICES} (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            adjusted_close REAL,
            volume INTEGER NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, date)
        )
    """,
}


# ============================================================================
# Dataclass helpers
# ============================================================================


def _dataclass_to_tuple(obj: object) -> tuple[Any, ...]:
    """Convert a dataclass instance to a tuple of field values."""
    return tuple(getattr(obj, f.name) for f in dataclasses.fields(obj))  # type: ignore[arg-type]


def _build_insert_sql(table_name: str, field_names: tuple[str, ...]) -> str:
    """Build an INSERT OR REPLACE SQL statement."""
    cols = ", ".join(field_names)
    placeholders = ", ".join("?" for _ in field_names)
    return f"INSERT OR REPLACE INTO {table_name} ({cols}) VALUES ({placeholders})"  # nosec B608


# ============================================================================
# DB path resolution
# ============================================================================


def _resolve_db_path() -> Path:
    """Resolve the Yahoo Finance SQLite database path.

    Resolution priority:

    1. ``PIPELINE_YFINANCE_DB_PATH`` environment variable (if set and non-empty)
    2. Default path via ``get_db_path("sqlite", YFINANCE_DB_NAME)``

    Returns
    -------
    Path
        Resolved path to the SQLite database file.
    """
    env_path = os.environ.get(PIPELINE_YFINANCE_DB_PATH_ENV, "")
    if env_path:
        return Path(env_path)
    return get_db_path("sqlite", YFINANCE_DB_NAME)


# ============================================================================
# YFinanceStorage class
# ============================================================================


class YFinanceStorage:
    """SQLite storage layer for Yahoo Finance daily price data.

    Manages the ``yf_daily_prices`` SQLite table. Uses
    ``CREATE TABLE IF NOT EXISTS`` for idempotent DDL and
    ``INSERT OR REPLACE`` for idempotent writes.

    The ``get_latest_date`` method returns the most recent ``date`` for a
    symbol, serving as the starting point for incremental data collection
    in Wave 4.

    Parameters
    ----------
    db_path : Path | None
        Path to the SQLite database file. When ``None``, the path is
        resolved via ``_resolve_db_path()``.

    Raises
    ------
    StorageError
        If the database cannot be initialized (e.g., permission errors).

    Examples
    --------
    >>> from pathlib import Path
    >>> storage = YFinanceStorage(db_path=Path(":memory:"))
    >>> tables = storage.get_table_names()
    >>> "yf_daily_prices" in tables
    True
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize storage and create the daily prices table."""
        path = db_path or _resolve_db_path()
        try:
            self._client = SQLiteClient(path)
        except Exception as exc:
            raise StorageError(
                f"Failed to initialize YFinanceStorage: {exc}",
                context={"db_path": str(path)},
            ) from exc
        logger.debug("YFinanceStorage initialized", db_path=str(path))
        self.ensure_tables()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create the daily prices table if it does not exist.

        Executes ``CREATE TABLE IF NOT EXISTS`` for the
        ``yf_daily_prices`` table. Safe to call multiple times.
        """
        logger.debug("Ensuring Yahoo Finance tables exist")
        try:
            for table_name, ddl in _TABLE_DDL.items():
                self._client.execute(ddl)
                logger.debug("Table ensured", table_name=table_name)
        except Exception as exc:
            raise StorageError(
                f"Failed to ensure Yahoo Finance tables: {exc}",
                context={"operation": "ensure_tables"},
            ) from exc
        logger.info("Yahoo Finance tables ensured", table_count=len(_TABLE_DDL))

    # ------------------------------------------------------------------
    # Introspection / utility
    # ------------------------------------------------------------------

    def get_table_names(self) -> list[str]:
        """Get the list of managed table names.

        Returns
        -------
        list[str]
            Sorted list of table names managed by this storage.
        """
        return sorted(_VALID_TABLE_NAMES)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert(self, records: list[Any]) -> int:
        """Upsert daily price records into ``yf_daily_prices``.

        Uses ``INSERT OR REPLACE`` for idempotent writes. Duplicate
        ``(symbol, date)`` entries are replaced in-place.

        Parameters
        ----------
        records : list[YFDailyPriceRecord]
            Records to upsert. Empty list is a no-op.

        Returns
        -------
        int
            Number of records upserted.

        Raises
        ------
        StorageError
            If the database write fails.

        Examples
        --------
        >>> from market.pipeline.models import YFDailyPriceRecord
        >>> storage = YFinanceStorage(db_path=Path(":memory:"))
        >>> record = YFDailyPriceRecord(
        ...     symbol="AAPL",
        ...     date="2026-04-03",
        ...     open=170.0,
        ...     high=175.0,
        ...     low=169.0,
        ...     close=173.0,
        ...     adjusted_close=173.0,
        ...     volume=50_000_000,
        ...     fetched_at="2026-04-03T20:00:00",
        ... )
        >>> storage.upsert([record])
        1
        """
        if not records:
            return 0
        try:
            field_names = tuple(f.name for f in dataclasses.fields(records[0]))
            sql = _build_insert_sql(TABLE_YF_DAILY_PRICES, field_names)
            data = [_dataclass_to_tuple(r) for r in records]
            self._client.execute_many(sql, data)
        except Exception as exc:
            raise StorageError(
                f"Failed to upsert daily price records: {exc}",
                context={"table": TABLE_YF_DAILY_PRICES, "count": len(records)},
            ) from exc
        logger.info("Daily price records upserted", count=len(records))
        return len(records)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_latest_date(self, symbol: str) -> str | None:
        """Get the most recent trading date for a given symbol.

        This is the primary hook for incremental data collection in Wave 4.
        Callers can use this date as the ``start`` parameter when fetching
        new data from the Yahoo Finance API.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).

        Returns
        -------
        str | None
            Most recent ``date`` in ISO 8601 format (e.g. ``"2026-04-03"``),
            or ``None`` when no data exists for the symbol.

        Raises
        ------
        StorageError
            If the database read fails.

        Examples
        --------
        >>> storage = YFinanceStorage(db_path=Path(":memory:"))
        >>> storage.get_latest_date("AAPL") is None
        True
        """
        try:
            rows = self._client.execute(
                f"SELECT MAX(date) AS latest FROM {TABLE_YF_DAILY_PRICES}"  # nosec B608
                " WHERE symbol = ?",
                (symbol,),
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get latest date for symbol: {exc}",
                context={"symbol": symbol, "table": TABLE_YF_DAILY_PRICES},
            ) from exc
        latest: str | None = rows[0]["latest"] if rows else None
        logger.debug("Latest date retrieved", symbol=symbol, latest=latest)
        return latest

    def get_by_symbol_date_range(
        self,
        symbol: str,
        start: str,
        end: str,
    ) -> list[Any]:
        """Get daily price records for a symbol within a date range.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).
        start : str
            Start date in ISO 8601 format (inclusive), e.g. ``"2026-01-01"``.
        end : str
            End date in ISO 8601 format (inclusive), e.g. ``"2026-04-03"``.

        Returns
        -------
        list[sqlite3.Row]
            Records ordered by ``date`` ascending. Returns an empty list
            if no records match.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT * FROM {TABLE_YF_DAILY_PRICES}"  # nosec B608
                " WHERE symbol = ? AND date BETWEEN ? AND ?"
                " ORDER BY date",
                (symbol, start, end),
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get daily prices by symbol and date range: {exc}",
                context={"symbol": symbol, "start": start, "end": end},
            ) from exc
        logger.debug(
            "Daily price records retrieved by symbol and date range",
            symbol=symbol,
            start=start,
            end=end,
            count=len(rows),
        )
        return list(rows)


# ============================================================================
# Factory function
# ============================================================================


def get_yfinance_storage(
    db_path: Path | None = None,
) -> YFinanceStorage:
    """Create a ``YFinanceStorage`` instance.

    Parameters
    ----------
    db_path : Path | None
        Optional explicit database path. When ``None``, uses the resolved
        default path from ``_resolve_db_path()``.

    Returns
    -------
    YFinanceStorage
        A configured storage instance with the daily prices table ensured.

    Examples
    --------
    >>> from pathlib import Path
    >>> storage = get_yfinance_storage(db_path=Path(":memory:"))
    >>> "yf_daily_prices" in storage.get_table_names()
    True
    """
    return YFinanceStorage(db_path=db_path)


__all__ = [
    "YFinanceStorage",
    "get_yfinance_storage",
]
