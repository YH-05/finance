"""SQLite storage layer for SEC EDGAR financial statement data.

This module provides the ``SecEdgarStorage`` class that manages the
``se_financial_statements`` SQLite table for persisting SEC EDGAR data.
It uses ``SQLiteClient`` from ``database.db`` for all database operations,
leveraging ``INSERT OR REPLACE`` for idempotent data updates.

Tables managed
--------------
- ``se_financial_statements`` -- SEC EDGAR financial statement records
  (PK: ``symbol``, ``fiscal_date_ending``, ``statement_type``, ``report_type``)

Examples
--------
>>> from pathlib import Path
>>> storage = SecEdgarStorage(db_path=Path(":memory:"))
>>> tables = storage.get_table_names()
>>> "se_financial_statements" in tables
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
    PIPELINE_SEC_EDGAR_DB_PATH_ENV,
    SEC_EDGAR_DB_NAME,
    TABLE_SE_FINANCIAL_STATEMENTS,
)
from market.pipeline.errors import StorageError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Valid table names whitelist (SQL injection prevention)
# ============================================================================

_VALID_TABLE_NAMES: frozenset[str] = frozenset({TABLE_SE_FINANCIAL_STATEMENTS})

# ============================================================================
# Table DDL definitions
# ============================================================================

_TABLE_DDL: dict[str, str] = {
    TABLE_SE_FINANCIAL_STATEMENTS: f"""
        CREATE TABLE IF NOT EXISTS {TABLE_SE_FINANCIAL_STATEMENTS} (
            symbol TEXT NOT NULL,
            fiscal_date_ending TEXT NOT NULL,
            statement_type TEXT NOT NULL,
            report_type TEXT NOT NULL,
            revenue REAL,
            net_income REAL,
            total_assets REAL,
            total_liabilities REAL,
            operating_cashflow REAL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, fiscal_date_ending, statement_type, report_type)
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
    """Resolve the SEC EDGAR SQLite database path.

    Resolution priority:

    1. ``PIPELINE_SEC_EDGAR_DB_PATH`` environment variable (if set and non-empty)
    2. Default path via ``get_db_path("sqlite", SEC_EDGAR_DB_NAME)``

    Returns
    -------
    Path
        Resolved path to the SQLite database file.
    """
    env_path = os.environ.get(PIPELINE_SEC_EDGAR_DB_PATH_ENV, "")
    if env_path:
        return Path(env_path)
    return get_db_path("sqlite", SEC_EDGAR_DB_NAME)


# ============================================================================
# SecEdgarStorage class
# ============================================================================


class SecEdgarStorage:
    """SQLite storage layer for SEC EDGAR financial statement data.

    Manages the ``se_financial_statements`` SQLite table. Uses
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
    >>> storage = SecEdgarStorage(db_path=Path(":memory:"))
    >>> tables = storage.get_table_names()
    >>> "se_financial_statements" in tables
    True
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize storage and create the financial statements table."""
        path = db_path or _resolve_db_path()
        try:
            self._client = SQLiteClient(path)
        except Exception as exc:
            raise StorageError(
                f"Failed to initialize SecEdgarStorage: {exc}",
                context={"db_path": str(path)},
            ) from exc
        logger.debug("SecEdgarStorage initialized", db_path=str(path))
        self.ensure_tables()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """Create the financial statements table if it does not exist.

        Executes ``CREATE TABLE IF NOT EXISTS`` for
        ``se_financial_statements``. Safe to call multiple times.
        """
        logger.debug("Ensuring SEC EDGAR tables exist")
        try:
            for table_name, ddl in _TABLE_DDL.items():
                self._client.execute(ddl)
                logger.debug("Table ensured", table_name=table_name)
        except Exception as exc:
            raise StorageError(
                f"Failed to ensure SEC EDGAR tables: {exc}",
                context={"operation": "ensure_tables"},
            ) from exc
        logger.info("SEC EDGAR tables ensured", table_count=len(_TABLE_DDL))

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
        """Upsert financial statement records into ``se_financial_statements``.

        Uses ``INSERT OR REPLACE`` for idempotent writes. Duplicate
        ``(symbol, fiscal_date_ending, statement_type, report_type)``
        entries are replaced in-place.

        Parameters
        ----------
        records : list[FinancialStatementRecord]
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
        >>> from market.pipeline.models import FinancialStatementRecord
        >>> storage = SecEdgarStorage(db_path=Path(":memory:"))
        >>> record = FinancialStatementRecord(
        ...     symbol="AAPL",
        ...     fiscal_date_ending="2025-09-30",
        ...     statement_type="income",
        ...     report_type="annual",
        ...     fetched_at="2026-04-03T10:00:00",
        ... )
        >>> storage.upsert([record])
        1
        """
        if not records:
            return 0
        try:
            field_names = tuple(f.name for f in dataclasses.fields(records[0]))
            sql = _build_insert_sql(TABLE_SE_FINANCIAL_STATEMENTS, field_names)
            data = [_dataclass_to_tuple(r) for r in records]
            self._client.execute_many(sql, data)
        except Exception as exc:
            raise StorageError(
                f"Failed to upsert financial statement records: {exc}",
                context={"table": TABLE_SE_FINANCIAL_STATEMENTS, "count": len(records)},
            ) from exc
        logger.info("Financial statement records upserted", count=len(records))
        return len(records)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_symbols_with_data(self) -> list[str]:
        """Get the list of unique ticker symbols that have data.

        Returns
        -------
        list[str]
            Sorted list of distinct symbols in ``se_financial_statements``.
            Returns an empty list if the table is empty.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT DISTINCT symbol FROM {TABLE_SE_FINANCIAL_STATEMENTS}"  # nosec B608
                " ORDER BY symbol"
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get symbols with data: {exc}",
                context={"table": TABLE_SE_FINANCIAL_STATEMENTS},
            ) from exc
        symbols = [row["symbol"] for row in rows]
        logger.debug("Symbols with data retrieved", count=len(symbols))
        return symbols

    def get_by_symbol(self, symbol: str) -> list[Any]:
        """Get all financial statement records for a given symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol to filter by (e.g. ``"AAPL"``).

        Returns
        -------
        list[sqlite3.Row]
            All records for the symbol, ordered by ``fiscal_date_ending``
            then ``statement_type``. Returns an empty list if not found.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT * FROM {TABLE_SE_FINANCIAL_STATEMENTS}"  # nosec B608
                " WHERE symbol = ?"
                " ORDER BY fiscal_date_ending, statement_type",
                (symbol,),
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get financial statements by symbol: {exc}",
                context={"symbol": symbol},
            ) from exc
        logger.debug(
            "Financial statement records retrieved by symbol",
            symbol=symbol,
            count=len(rows),
        )
        return list(rows)

    def get_latest_filing_date(self, symbol: str, filing_type: str) -> str | None:
        """Get the most recent ``fiscal_date_ending`` for a symbol and filing type.

        Useful as the starting point for incremental data collection.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).
        filing_type : str
            Filing period type: ``"annual"`` or ``"quarterly"``.

        Returns
        -------
        str | None
            Most recent ``fiscal_date_ending`` in ISO 8601 format,
            or ``None`` when no data exists for the given symbol and filing type.

        Raises
        ------
        StorageError
            If the database read fails.
        """
        try:
            rows = self._client.execute(
                f"SELECT MAX(fiscal_date_ending) AS latest"  # nosec B608
                f" FROM {TABLE_SE_FINANCIAL_STATEMENTS}"
                " WHERE symbol = ? AND report_type = ?",
                (symbol, filing_type),
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to get latest filing date: {exc}",
                context={"symbol": symbol, "filing_type": filing_type},
            ) from exc
        latest: str | None = rows[0]["latest"] if rows else None
        logger.debug(
            "Latest filing date retrieved",
            symbol=symbol,
            filing_type=filing_type,
            latest=latest,
        )
        return latest


# ============================================================================
# Factory function
# ============================================================================


def get_sec_edgar_storage(
    db_path: Path | None = None,
) -> SecEdgarStorage:
    """Create a ``SecEdgarStorage`` instance.

    Parameters
    ----------
    db_path : Path | None
        Optional explicit database path. When ``None``, uses the resolved
        default path from ``_resolve_db_path()``.

    Returns
    -------
    SecEdgarStorage
        A configured storage instance with the financial statements table ensured.

    Examples
    --------
    >>> from pathlib import Path
    >>> storage = get_sec_edgar_storage(db_path=Path(":memory:"))
    >>> "se_financial_statements" in storage.get_table_names()
    True
    """
    return SecEdgarStorage(db_path=db_path)


__all__ = [
    "SecEdgarStorage",
    "get_sec_edgar_storage",
]
