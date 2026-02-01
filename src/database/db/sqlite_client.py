"""SQLite client with connection management."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


class SQLiteClient:
    """SQLite database client with context manager support.

    Parameters
    ----------
    db_path : Path
        Path to SQLite database file

    Examples
    --------
    >>> from database.db import SQLiteClient, get_db_path
    >>> client = SQLiteClient(get_db_path("sqlite", "market"))
    >>> with client.connection() as conn:
    ...     cursor = conn.execute("SELECT 1")
    ...     result = cursor.fetchone()
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("SQLiteClient initialized", db_path=str(db_path))

    @property
    def path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Get database connection as context manager.

        Yields
        ------
        sqlite3.Connection
            Database connection with Row factory

        Raises
        ------
        sqlite3.Error
            If database operation fails
        """
        logger.debug("Opening SQLite connection", db_path=str(self._db_path))
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
            logger.debug("SQLite transaction committed")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("SQLite transaction failed", error=str(e))
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """Execute SQL and return results.

        Parameters
        ----------
        sql : str
            SQL query to execute
        params : tuple[Any, ...], default=()
            Query parameters

        Returns
        -------
        list[sqlite3.Row]
            Query results
        """
        with self.connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def execute_many(self, sql: str, params_list: list[tuple[Any, ...]]) -> int:
        """Execute SQL with multiple parameter sets.

        Parameters
        ----------
        sql : str
            SQL query to execute
        params_list : list[tuple[Any, ...]]
            List of parameter tuples

        Returns
        -------
        int
            Number of rows affected
        """
        with self.connection() as conn:
            cursor = conn.executemany(sql, params_list)
            return cursor.rowcount

    def execute_script(self, script: str) -> None:
        """Execute SQL script.

        Parameters
        ----------
        script : str
            SQL script to execute
        """
        with self.connection() as conn:
            conn.executescript(script)

    def get_tables(self) -> list[str]:
        """Get list of table names in the database.

        Returns
        -------
        list[str]
            List of table names, sorted alphabetically

        Examples
        --------
        >>> from database.db import SQLiteClient, get_db_path
        >>> client = SQLiteClient(get_db_path("sqlite", "market"))
        >>> tables = client.get_tables()
        >>> print(tables)
        ['daily_prices', 'stocks']
        """
        results = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row["name"] for row in results]
