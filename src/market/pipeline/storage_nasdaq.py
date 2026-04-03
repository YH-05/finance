"""SQLite storage layer for NASDAQ earnings calendar data.

This module provides the ``NasdaqCalendarStorage`` class that manages the
``nc_earnings_calendar`` SQLite table for persisting NASDAQ API data.
It uses ``SQLiteClient`` from ``database.db`` for all database operations,
leveraging ``INSERT OR REPLACE`` for idempotent data updates.

Tables managed
--------------
- ``nc_earnings_calendar`` -- NASDAQ earnings calendar records
  (PK: ``symbol``, ``report_date``)

Examples
--------
>>> from pathlib import Path
>>> storage = NasdaqCalendarStorage(db_path=Path(":memory:"))
>>> tables = storage.get_table_names()
>>> "nc_earnings_calendar" in tables
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
    NASDAQ_CALENDAR_DB_NAME,
    PIPELINE_NASDAQ_DB_PATH_ENV,
    TABLE_NC_EARNINGS_CALENDAR,
)
from market.pipeline.errors import StorageError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Valid table names whitelist (SQL injection prevention)
# ============================================================================

_VALID_TABLE_NAMES: frozenset[str] = frozenset({TABLE_NC_EARNINGS_CALENDAR})

# ============================================================================
# Table DDL definitions
# ============================================================================

_TABLE_DDL: dict[str, str] = {
    TABLE_NC_EARNINGS_CALENDAR: f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NC_EARNINGS_CALENDAR} (
            symbol TEXT NOT NULL,
            report_date TEXT NOT NULL,
            eps_estimate REAL,
            report_time TEXT,
            fiscal_quarter_ending TEXT,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, report_date)
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
    """Resolve the NASDAQ calendar SQLite database path.

    Resolution priority:

    1. ``PIPELINE_NASDAQ_DB_PATH`` environment variable (if set and non-empty)
    2. Default path via ``get_db_path("sqlite", NASDAQ_CALENDAR_DB_NAME)``

    Returns
    -------
    Path
        Resolved path to the SQLite database file.
    """
    env_path = os.environ.get(PIPELINE_NASDAQ_DB_PATH_ENV, "")
    if env_path:
        return Path(env_path)
    return get_db_path("sqlite", NASDAQ_CALENDAR_DB_NAME)


# ============================================================================
# NasdaqCalendarStorage class
# ============================================================================


class NasdaqCalendarStorage:
    """SQLite storage layer for NASDAQ earnings calendar data.

    Manages the ``nc_earnings_calendar`` SQLite table. Uses
    ``CREATE TABLE IF NOT EXISTS`` for idempotent DDL and
    ``INSERT OR REPLACE`` for idempotent writes.

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
    >>> storage = NasdaqCalendarStorage(db_path=Path(":memory:"))
    >>> tables = storage.get_table_names()
    >>> "nc_earnings_calendar" in tables
    True
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize storage and create the earnings calendar table."""
        path = db_path or _resolve_db_path()
        try:
            self._client = SQLiteClient(path)
        except Exception as exc:
            raise StorageError(
                f"Failed to initialize NasdaqCalendarStorage: {exc}",
                context={"db_path": str(path)},
            ) from exc
        logger.debug("NasdaqCalendarStorage initialized", db_path=str(path))
        self.ensure_tables()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create the earnings calendar table if it does not exist.

        Executes ``CREATE TABLE IF NOT EXISTS`` for the
        ``nc_earnings_calendar`` table. Safe to call multiple times.
        """
        logger.debug("Ensuring NASDAQ calendar tables exist")
        try:
            for table_name, ddl in _TABLE_DDL.items():
                self._client.execute(ddl)
                logger.debug("Table ensured", table_name=table_name)
        except Exception as exc:
            raise StorageError(
                f"Failed to ensure NASDAQ calendar tables: {exc}",
                context={"operation": "ensure_tables"},
            ) from exc
        logger.info("NASDAQ calendar tables ensured", table_count=len(_TABLE_DDL))

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
        """Upsert earnings calendar records into ``nc_earnings_calendar``.

        Uses ``INSERT OR REPLACE`` for idempotent writes. Duplicate
        ``(symbol, report_date)`` entries are replaced in-place.

        Parameters
        ----------
        records : list[EarningsCalendarRecord]
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
        >>> from market.pipeline.models import EarningsCalendarRecord
        >>> storage = NasdaqCalendarStorage(db_path=Path(":memory:"))
        >>> record = EarningsCalendarRecord(
        ...     symbol="AAPL",
        ...     report_date="2026-04-30",
        ...     fetched_at="2026-04-03T10:00:00",
        ... )
        >>> storage.upsert([record])
        1
        """
        if not records:
            return 0
        try:
            field_names = tuple(f.name for f in dataclasses.fields(records[0]))
            sql = _build_insert_sql(TABLE_NC_EARNINGS_CALENDAR, field_names)
            data = [_dataclass_to_tuple(r) for r in records]
            self._client.execute_many(sql, data)
        except Exception as exc:
            raise StorageError(
                f"Failed to upsert earnings calendar records: {exc}",
                context={"table": TABLE_NC_EARNINGS_CALENDAR, "count": len(records)},
            ) from exc
        logger.info(
            "Earnings calendar records upserted",
            count=len(records),
        )
        return len(records)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_date_range(self, start: str, end: str) -> list[Any]:
        """Get earnings calendar records within a date range.

        Parameters
        ----------
        start : str
            Start date in ISO 8601 format (inclusive), e.g. ``"2026-04-01"``.
        end : str
            End date in ISO 8601 format (inclusive), e.g. ``"2026-04-30"``.

        Returns
        -------
        list[sqlite3.Row]
            Records with ``report_date`` between ``start`` and ``end``.
            Returns an empty list if no records match.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT * FROM {TABLE_NC_EARNINGS_CALENDAR}"  # nosec B608
                " WHERE report_date BETWEEN ? AND ?"
                " ORDER BY report_date, symbol",
                (start, end),
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to query earnings calendar by date range: {exc}",
                context={"start": start, "end": end},
            ) from exc
        logger.debug(
            "Earnings calendar records retrieved by date range",
            start=start,
            end=end,
            count=len(rows),
        )
        return list(rows)

    def get_latest_fetched_date(self) -> str | None:
        """Get the most recent ``fetched_at`` timestamp across all records.

        Useful for determining how stale the local data is.

        Returns
        -------
        str | None
            ISO 8601 timestamp of the most recent ``fetched_at``,
            or ``None`` when the table is empty.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT MAX(fetched_at) AS latest FROM {TABLE_NC_EARNINGS_CALENDAR}"  # nosec B608
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get latest fetched date: {exc}",
                context={"table": TABLE_NC_EARNINGS_CALENDAR},
            ) from exc
        latest: str | None = rows[0]["latest"] if rows else None
        logger.debug("Latest fetched date retrieved", latest=latest)
        return latest


# ============================================================================
# Factory function
# ============================================================================


def get_nasdaq_calendar_storage(
    db_path: Path | None = None,
) -> NasdaqCalendarStorage:
    """Create a ``NasdaqCalendarStorage`` instance.

    Parameters
    ----------
    db_path : Path | None
        Optional explicit database path. When ``None``, uses the resolved
        default path from ``_resolve_db_path()``.

    Returns
    -------
    NasdaqCalendarStorage
        A configured storage instance with the earnings calendar table ensured.

    Examples
    --------
    >>> from pathlib import Path
    >>> storage = get_nasdaq_calendar_storage(db_path=Path(":memory:"))
    >>> "nc_earnings_calendar" in storage.get_table_names()
    True
    """
    return NasdaqCalendarStorage(db_path=db_path)


__all__ = [
    "NasdaqCalendarStorage",
    "get_nasdaq_calendar_storage",
]
