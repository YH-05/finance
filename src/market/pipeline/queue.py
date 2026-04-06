"""SQLite queue layer for NASDAQ earnings calendar collection tasks.

This module provides the ``CollectionQueue`` class that manages the
``nc_collection_queue`` SQLite table. It shares the same database file as
``NasdaqCalendarStorage`` (``nasdaq_calendar.db``) but operates as an
independent class.

Each row in ``nc_collection_queue`` represents one ``(symbol, earnings_date,
source)`` combination. The composite primary key ensures idempotent
``enqueue()`` calls.

Tables managed
--------------
- ``nc_collection_queue`` -- collection task queue for NASDAQ earnings data

Status lifecycle
----------------
::

    pending → completed
    pending → failed  → (reset_failed) → pending
    pending → skipped

Examples
--------
>>> from pathlib import Path
>>> q = CollectionQueue(db_path=Path(":memory:"))
>>> q.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
2
>>> entries = q.get_pending("nasdaq")
>>> entries[0].symbol
'AAPL'

See Also
--------
market.pipeline.storage_nasdaq.NasdaqCalendarStorage : Shares the same DB.
market.pipeline.models : ``QueueEntry`` dataclass.
market.pipeline.constants : Table name and env var constants.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from database.db.connection import get_db_path
from database.db.sqlite_client import SQLiteClient
from market.pipeline.constants import (
    NASDAQ_CALENDAR_DB_NAME,
    PIPELINE_NASDAQ_DB_PATH_ENV,
    TABLE_NC_COLLECTION_QUEUE,
)
from market.pipeline.errors import QueueError
from market.pipeline.models import QueueEntry
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Table DDL
# ============================================================================

_TABLE_DDL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NC_COLLECTION_QUEUE} (
        symbol          TEXT    NOT NULL,
        earnings_date   TEXT    NOT NULL,
        source          TEXT    NOT NULL,
        status          TEXT    NOT NULL DEFAULT 'pending',
        priority        INTEGER NOT NULL DEFAULT 0,
        attempts        INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT    NOT NULL,
        updated_at      TEXT,
        error_message   TEXT,
        PRIMARY KEY (symbol, earnings_date, source)
    )
"""

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
# CollectionQueue
# ============================================================================


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _row_to_queue_entry(row: object) -> QueueEntry:
    """Convert a sqlite3.Row to a QueueEntry dataclass."""
    return QueueEntry(
        symbol=row["symbol"],  # type: ignore[index]
        earnings_date=row["earnings_date"],  # type: ignore[index]
        source=row["source"],  # type: ignore[index]
        status=row["status"],  # type: ignore[index]
        priority=row["priority"],  # type: ignore[index]
        attempts=row["attempts"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        updated_at=row["updated_at"],  # type: ignore[index]
        error_message=row["error_message"],  # type: ignore[index]
    )


class CollectionQueue:
    """SQLite queue for NASDAQ earnings calendar collection tasks.

    Manages the ``nc_collection_queue`` table inside the shared
    ``nasdaq_calendar.db`` file. All write operations are idempotent.

    Parameters
    ----------
    db_path : Path | None
        Path to the SQLite database file. When ``None``, the path is
        resolved via the ``PIPELINE_NASDAQ_DB_PATH`` env var or the default
        ``get_db_path("sqlite", "nasdaq_calendar")`` path.

    Raises
    ------
    QueueError
        If the database cannot be initialized (e.g., permission errors).

    Examples
    --------
    >>> from pathlib import Path
    >>> q = CollectionQueue(db_path=Path(":memory:"))
    >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])
    1
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the queue and create the ``nc_collection_queue`` table."""
        path = db_path or _resolve_db_path()
        try:
            self._client = SQLiteClient(path)
        except Exception as exc:
            raise QueueError(
                f"Failed to initialize CollectionQueue: {exc}",
                context={"db_path": str(path)},
            ) from exc
        logger.debug("CollectionQueue initialized", db_path=str(path))
        self.ensure_tables()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create the collection queue table if it does not exist.

        Safe to call multiple times (idempotent DDL via
        ``CREATE TABLE IF NOT EXISTS``).

        Raises
        ------
        QueueError
            If the DDL execution fails.
        """
        logger.debug("Ensuring collection queue table exists")
        try:
            self._client.execute(_TABLE_DDL)
        except Exception as exc:
            raise QueueError(
                f"Failed to ensure collection queue table: {exc}",
                context={"table": TABLE_NC_COLLECTION_QUEUE},
            ) from exc
        logger.debug("Collection queue table ensured", table=TABLE_NC_COLLECTION_QUEUE)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def enqueue(
        self,
        symbol: str,
        earnings_date: str,
        sources: list[str],
        priority: int = 0,
    ) -> int:
        """Add pending queue entries for each source (idempotent).

        For each ``source`` in ``sources``, inserts a ``pending`` row
        with the given ``(symbol, earnings_date, source)`` composite key.
        If a row already exists with the same key, it is left unchanged
        (``INSERT OR IGNORE`` semantics).

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).
        earnings_date : str
            Expected earnings date in ISO 8601 format (e.g. ``"2026-04-30"``).
        sources : list[str]
            Data source identifiers (e.g. ``["nasdaq", "yfinance"]``).
            Empty list is a no-op that returns ``0``.
        priority : int
            Collection priority. Higher values are processed first.
            Default is ``0``.

        Returns
        -------
        int
            Number of entries actually inserted (0 when all already exist).

        Raises
        ------
        QueueError
            If the database write fails.

        Examples
        --------
        >>> q = CollectionQueue(db_path=Path(":memory:"))
        >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        2
        >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])  # already exists
        0
        """
        if not sources:
            return 0

        now = _now_iso()
        sql = (
            f"INSERT OR IGNORE INTO {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " (symbol, earnings_date, source, status, priority, attempts, created_at)"
            " VALUES (?, ?, ?, 'pending', ?, 0, ?)"
        )
        rows: list[tuple[str, str, str, int, str]] = [
            (symbol, earnings_date, source, priority, now) for source in sources
        ]
        try:
            self._client.execute_many(sql, rows)
        except Exception as exc:
            raise QueueError(
                f"Failed to enqueue entries: {exc}",
                context={
                    "symbol": symbol,
                    "earnings_date": earnings_date,
                    "sources": sources,
                },
            ) from exc

        # Determine how many rows were inserted by checking existence
        inserted = self._count_existing(symbol, earnings_date, sources)
        logger.info(
            "Queue entries enqueued",
            symbol=symbol,
            earnings_date=earnings_date,
            sources=sources,
            priority=priority,
        )
        return inserted

    def _count_existing(
        self, symbol: str, earnings_date: str, sources: list[str]
    ) -> int:
        """Count existing entries for the given (symbol, earnings_date, sources)."""
        placeholders = ",".join("?" for _ in sources)
        sql = (
            f"SELECT COUNT(*) AS cnt FROM {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            f" WHERE symbol=? AND earnings_date=? AND source IN ({placeholders})"
        )
        params: tuple[str, ...] = (symbol, earnings_date, *sources)
        rows = self._client.execute(sql, params)
        return int(rows[0]["cnt"]) if rows else 0

    def mark_completed(self, symbol: str, earnings_date: str, source: str) -> None:
        """Mark a queue entry as completed.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        earnings_date : str
            Earnings date in ISO 8601 format.
        source : str
            Data source identifier.

        Raises
        ------
        QueueError
            If the database update fails.
        """
        self._update_status(symbol, earnings_date, source, "completed")

    def mark_failed(
        self,
        symbol: str,
        earnings_date: str,
        source: str,
        error_message: str,
    ) -> None:
        """Mark a queue entry as failed and increment the attempt counter.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        earnings_date : str
            Earnings date in ISO 8601 format.
        source : str
            Data source identifier.
        error_message : str
            Human-readable description of the failure.

        Raises
        ------
        QueueError
            If the database update fails.
        """
        now = _now_iso()
        sql = (
            f"UPDATE {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " SET status='failed', attempts=attempts+1,"
            "     error_message=?, updated_at=?"
            " WHERE symbol=? AND earnings_date=? AND source=?"
        )
        try:
            self._client.execute(
                sql, (error_message, now, symbol, earnings_date, source)
            )
        except Exception as exc:
            raise QueueError(
                f"Failed to mark entry as failed: {exc}",
                context={
                    "symbol": symbol,
                    "earnings_date": earnings_date,
                    "source": source,
                },
            ) from exc
        logger.debug(
            "Queue entry marked failed",
            symbol=symbol,
            earnings_date=earnings_date,
            source=source,
            error_message=error_message,
        )

    def mark_skipped(self, symbol: str, earnings_date: str, source: str) -> None:
        """Mark a queue entry as skipped.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        earnings_date : str
            Earnings date in ISO 8601 format.
        source : str
            Data source identifier.

        Raises
        ------
        QueueError
            If the database update fails.
        """
        self._update_status(symbol, earnings_date, source, "skipped")

    def reset_failed(self, max_attempts: int = 3, priority_boost: int = 0) -> int:
        """Reset failed entries with fewer than ``max_attempts`` back to pending.

        Only entries where ``attempts < max_attempts`` are reset; entries
        that have exhausted all retries are left untouched.

        Parameters
        ----------
        max_attempts : int
            Maximum number of attempts allowed. Entries with
            ``attempts >= max_attempts`` are **not** reset.
            Default is ``3``.
        priority_boost : int
            Amount to add to the ``priority`` column of each reset entry.
            Use a positive value to ensure previously-failed entries are
            processed before newly-enqueued ones on the next run.
            Default is ``0`` (no change to priority, preserving existing
            behaviour).

        Returns
        -------
        int
            Number of entries reset to ``pending``.

        Raises
        ------
        QueueError
            If the database update fails.

        Examples
        --------
        >>> q = CollectionQueue(db_path=Path(":memory:"))
        >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        1
        >>> q.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        >>> q.reset_failed(max_attempts=3)
        1
        >>> q.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        >>> q.reset_failed(max_attempts=3, priority_boost=10)
        1
        """
        now = _now_iso()
        sql = (
            f"UPDATE {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " SET status='pending', priority=priority+?, error_message=NULL, updated_at=?"
            " WHERE status='failed' AND attempts < ?"
        )
        try:
            self._client.execute(sql, (priority_boost, now, max_attempts))
        except Exception as exc:
            raise QueueError(
                f"Failed to reset failed entries: {exc}",
                context={
                    "max_attempts": max_attempts,
                    "priority_boost": priority_boost,
                },
            ) from exc

        # Count how many pending entries now exist (approximation via re-query)
        count_sql = (
            f"SELECT COUNT(*) AS cnt FROM {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " WHERE status='pending' AND updated_at=?"
        )
        rows = self._client.execute(count_sql, (now,))
        reset_count = int(rows[0]["cnt"]) if rows else 0
        logger.info(
            "Failed queue entries reset to pending",
            reset_count=reset_count,
            max_attempts=max_attempts,
            priority_boost=priority_boost,
        )
        return reset_count

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_pending(self, source: str, limit: int = 100) -> list[QueueEntry]:
        """Get pending queue entries for the given source.

        Returns entries ordered by ``priority DESC, created_at ASC``.

        Parameters
        ----------
        source : str
            Data source identifier to filter by.
        limit : int
            Maximum number of entries to return. Default is ``100``.

        Returns
        -------
        list[QueueEntry]
            Pending entries for ``source``, ordered by priority (high first)
            then creation time (oldest first).

        Raises
        ------
        QueueError
            If the database read fails.

        Examples
        --------
        >>> q = CollectionQueue(db_path=Path(":memory:"))
        >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        1
        >>> entries = q.get_pending("nasdaq")
        >>> entries[0].status
        'pending'
        """
        sql = (
            f"SELECT * FROM {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " WHERE source=? AND status='pending'"
            " ORDER BY priority DESC, created_at ASC"
            " LIMIT ?"
        )
        try:
            rows = self._client.execute(sql, (source, limit))
        except Exception as exc:
            raise QueueError(
                f"Failed to get pending entries: {exc}",
                context={"source": source, "limit": limit},
            ) from exc
        entries = [_row_to_queue_entry(row) for row in rows]
        logger.debug(
            "Pending queue entries retrieved",
            source=source,
            count=len(entries),
        )
        return entries

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Get a count of entries by source and status.

        Returns
        -------
        dict[str, dict[str, int]]
            Nested dict of the form ``{source: {status: count}}``.
            Returns an empty dict when the table is empty.

        Raises
        ------
        QueueError
            If the database read fails.

        Examples
        --------
        >>> q = CollectionQueue(db_path=Path(":memory:"))
        >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        1
        >>> q.get_stats()
        {'nasdaq': {'pending': 1}}
        """
        sql = (
            f"SELECT source, status, COUNT(*) AS cnt"  # nosec B608
            f" FROM {TABLE_NC_COLLECTION_QUEUE}"
            " GROUP BY source, status"
        )
        try:
            rows = self._client.execute(sql)
        except Exception as exc:
            raise QueueError(
                f"Failed to get queue stats: {exc}",
                context={"table": TABLE_NC_COLLECTION_QUEUE},
            ) from exc

        stats: dict[str, dict[str, int]] = {}
        for row in rows:
            src = row["source"]
            status = row["status"]
            cnt = int(row["cnt"])
            if src not in stats:
                stats[src] = {}
            stats[src][status] = cnt

        logger.debug("Queue stats retrieved", source_count=len(stats))
        return stats

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_status(
        self, symbol: str, earnings_date: str, source: str, new_status: str
    ) -> None:
        """Update the status of a single queue entry."""
        now = _now_iso()
        sql = (
            f"UPDATE {TABLE_NC_COLLECTION_QUEUE}"  # nosec B608
            " SET status=?, updated_at=?"
            " WHERE symbol=? AND earnings_date=? AND source=?"
        )
        try:
            self._client.execute(sql, (new_status, now, symbol, earnings_date, source))
        except Exception as exc:
            raise QueueError(
                f"Failed to update queue entry status to '{new_status}': {exc}",
                context={
                    "symbol": symbol,
                    "earnings_date": earnings_date,
                    "source": source,
                },
            ) from exc
        logger.debug(
            "Queue entry status updated",
            symbol=symbol,
            earnings_date=earnings_date,
            source=source,
            new_status=new_status,
        )


# ============================================================================
# Factory function
# ============================================================================


def get_collection_queue(db_path: Path | None = None) -> CollectionQueue:
    """Create a ``CollectionQueue`` instance.

    Parameters
    ----------
    db_path : Path | None
        Optional explicit database path. When ``None``, uses the resolved
        default path.

    Returns
    -------
    CollectionQueue
        A configured queue instance with the table ensured.

    Examples
    --------
    >>> from pathlib import Path
    >>> q = get_collection_queue(db_path=Path(":memory:"))
    >>> q.enqueue("AAPL", "2026-04-30", ["nasdaq"])
    1
    """
    return CollectionQueue(db_path=db_path)


__all__ = [
    "CollectionQueue",
    "get_collection_queue",
]
