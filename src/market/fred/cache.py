"""SQLite-based caching for FRED data.

This module provides a persistent cache implementation using SQLite
for storing fetched FRED data with TTL (time-to-live) support.
"""

import hashlib
import json
import pickle  # nosec B403
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Generator

import pandas as pd

from finance.utils.logging_config import get_logger

from .types import CacheConfig

logger = get_logger(__name__)


# Default cache configuration (in-memory by default for backwards compatibility)
DEFAULT_CACHE_CONFIG = CacheConfig(
    enabled=True,
    ttl_seconds=3600,  # 1 hour
    max_entries=1000,
    db_path=None,  # In-memory by default
)


def generate_cache_key(
    symbol: str,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    interval: str = "1d",
    source: str = "fred",
) -> str:
    """Generate a unique cache key for FRED data.

    Parameters
    ----------
    symbol : str
        Series ID (e.g., GDP, CPIAUCSL)
    start_date : datetime | str | None
        Start date
    end_date : datetime | str | None
        End date
    interval : str
        Data interval
    source : str
        Data source

    Returns
    -------
    str
        A unique cache key (SHA-256 hash)

    Examples
    --------
    >>> key = generate_cache_key("GDP", "2024-01-01", "2024-12-31")
    >>> len(key)
    64
    """
    key_str = ":".join(
        [
            symbol.upper(),
            str(start_date) if start_date else "none",
            str(end_date) if end_date else "none",
            interval,
            source,
        ]
    )
    return hashlib.sha256(key_str.encode()).hexdigest()


class CacheError(Exception):
    """Exception raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        key: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.key = key
        self.cause = cause


class SQLiteCache:
    """SQLite-based cache for FRED data.

    Provides persistent caching with TTL support, automatic cleanup
    of expired entries, and thread-safe operations.

    Parameters
    ----------
    config : CacheConfig | None
        Cache configuration. Uses DEFAULT_CACHE_CONFIG if not specified.

    Attributes
    ----------
    config : CacheConfig
        The cache configuration
    db_path : str
        Path to the SQLite database (":memory:" for in-memory)

    Examples
    --------
    >>> cache = SQLiteCache()
    >>> cache.set("key1", {"price": 150.0}, ttl=3600)
    >>> cache.get("key1")
    {'price': 150.0}
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        self.config = config or DEFAULT_CACHE_CONFIG
        self.db_path = self.config.db_path or ":memory:"
        self._local = threading.local()
        self._lock = threading.Lock()

        logger.debug(
            "Initializing SQLite cache",
            db_path=self.db_path,
            ttl_seconds=self.config.ttl_seconds,
            max_entries=self.config.max_entries,
        )

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            self._local.connection.row_factory = sqlite3.Row

        return self._local.connection

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise CacheError(
                f"Database transaction failed: {e}",
                operation="transaction",
                cause=e,
            ) from e

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    value_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache (expires_at)
            """)

        logger.debug("Cache database initialized")

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Parameters
        ----------
        key : str
            The cache key

        Returns
        -------
        Any | None
            The cached value, or None if not found or expired

        Examples
        --------
        >>> cache.get("nonexistent_key")
        None
        """
        logger.debug("Cache get", key=key[:16] + "...")

        try:
            with self._transaction() as conn:
                cursor = conn.execute(
                    """
                    SELECT value, value_type, expires_at
                    FROM cache
                    WHERE key = ?
                    """,
                    (key,),
                )
                row = cursor.fetchone()

                if row is None:
                    logger.debug("Cache miss", key=key[:16] + "...")
                    return None

                expires_at = datetime.fromisoformat(row["expires_at"])
                if expires_at < datetime.now(UTC):
                    logger.debug("Cache expired", key=key[:16] + "...")
                    # Delete expired entry
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    return None

                value = self._deserialize(row["value"], row["value_type"])
                logger.debug("Cache hit", key=key[:16] + "...")
                return value

        except CacheError:
            raise
        except Exception as e:
            logger.error("Cache get failed", key=key[:16] + "...", error=str(e))
            raise CacheError(
                f"Failed to get cache entry: {e}",
                operation="get",
                key=key,
                cause=e,
            ) from e

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a value in the cache.

        Parameters
        ----------
        key : str
            The cache key
        value : Any
            The value to cache
        ttl : int | None
            Time-to-live in seconds. Uses config.ttl_seconds if not specified.
        metadata : dict[str, Any] | None
            Optional metadata to store with the entry

        Examples
        --------
        >>> cache.set("key1", {"data": [1, 2, 3]}, ttl=7200)
        """
        if ttl is None:
            ttl = self.config.ttl_seconds

        logger.debug(
            "Cache set",
            key=key[:16] + "...",
            ttl_seconds=ttl,
            value_type=type(value).__name__,
        )

        try:
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=ttl)
            serialized, value_type = self._serialize(value)
            metadata_json = json.dumps(metadata) if metadata else None

            with self._lock, self._transaction() as conn:
                # Check entry count and cleanup if needed
                cursor = conn.execute("SELECT COUNT(*) as count FROM cache")
                count = cursor.fetchone()["count"]

                if count >= self.config.max_entries:
                    logger.debug(
                        "Max entries reached, cleaning up",
                        current=count,
                        max=self.config.max_entries,
                    )
                    self._cleanup_oldest(conn, count - self.config.max_entries + 1)

                # Insert or replace the entry
                conn.execute(
                    """
                        INSERT OR REPLACE INTO cache
                        (key, value, value_type, created_at, expires_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                    (
                        key,
                        serialized,
                        value_type,
                        now.isoformat(),
                        expires_at.isoformat(),
                        metadata_json,
                    ),
                )

            logger.debug("Cache entry stored", key=key[:16] + "...")

        except CacheError:
            raise
        except Exception as e:
            logger.error("Cache set failed", key=key[:16] + "...", error=str(e))
            raise CacheError(
                f"Failed to set cache entry: {e}",
                operation="set",
                key=key,
                cause=e,
            ) from e

    def delete(self, key: str) -> bool:
        """Delete an entry from the cache.

        Parameters
        ----------
        key : str
            The cache key

        Returns
        -------
        bool
            True if an entry was deleted, False otherwise

        Examples
        --------
        >>> cache.delete("key1")
        True
        """
        logger.debug("Cache delete", key=key[:16] + "...")

        try:
            with self._transaction() as conn:
                cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                deleted = cursor.rowcount > 0

            if deleted:
                logger.debug("Cache entry deleted", key=key[:16] + "...")
            else:
                logger.debug("Cache entry not found", key=key[:16] + "...")

            return deleted

        except Exception as e:
            logger.error("Cache delete failed", key=key[:16] + "...", error=str(e))
            raise CacheError(
                f"Failed to delete cache entry: {e}",
                operation="delete",
                key=key,
                cause=e,
            ) from e

    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns
        -------
        int
            Number of entries cleared

        Examples
        --------
        >>> cache.clear()
        5
        """
        logger.info("Clearing cache")

        try:
            with self._lock, self._transaction() as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM cache")
                count = cursor.fetchone()["count"]
                conn.execute("DELETE FROM cache")

            logger.info("Cache cleared", entries_removed=count)
            return count

        except Exception as e:
            logger.error("Cache clear failed", error=str(e))
            raise CacheError(
                f"Failed to clear cache: {e}",
                operation="clear",
                cause=e,
            ) from e

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns
        -------
        int
            Number of entries removed

        Examples
        --------
        >>> cache.cleanup_expired()
        3
        """
        logger.debug("Cleaning up expired cache entries")

        try:
            now = datetime.now(UTC).isoformat()

            with self._lock, self._transaction() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM cache WHERE expires_at < ?",
                    (now,),
                )
                expired_count = cursor.fetchone()["count"]

                if expired_count > 0:
                    conn.execute(
                        "DELETE FROM cache WHERE expires_at < ?",
                        (now,),
                    )

            logger.debug("Expired entries cleaned up", count=expired_count)
            return expired_count

        except Exception as e:
            logger.error("Cache cleanup failed", error=str(e))
            raise CacheError(
                f"Failed to cleanup expired entries: {e}",
                operation="cleanup_expired",
                cause=e,
            ) from e

    def _cleanup_oldest(self, conn: sqlite3.Connection, count: int) -> None:
        """Remove the oldest entries to make room for new ones."""
        conn.execute(
            """
            DELETE FROM cache
            WHERE key IN (
                SELECT key FROM cache
                ORDER BY created_at ASC
                LIMIT ?
            )
            """,
            (count,),
        )

    def _serialize(self, value: Any) -> tuple[bytes, str]:
        """Serialize a value for storage."""
        if isinstance(value, pd.DataFrame):
            return pickle.dumps(value), "dataframe"
        elif isinstance(value, pd.Series):
            return pickle.dumps(value), "series"
        elif isinstance(value, (dict, list)):
            return json.dumps(value).encode(), "json"
        else:
            return pickle.dumps(value), "pickle"

    def _deserialize(self, data: bytes, value_type: str) -> Any:
        """Deserialize a stored value."""
        if value_type in ("dataframe", "series", "pickle"):
            return pickle.loads(data)  # nosec B301
        elif value_type == "json":
            return json.loads(data.decode())
        else:
            return pickle.loads(data)  # nosec B301

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns
        -------
        dict[str, Any]
            Cache statistics including entry count, size, etc.

        Examples
        --------
        >>> cache.get_stats()
        {'total_entries': 10, 'expired_entries': 2, ...}
        """
        try:
            now = datetime.now(UTC).isoformat()

            with self._transaction() as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM cache")
                total = cursor.fetchone()["count"]

                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM cache WHERE expires_at < ?",
                    (now,),
                )
                expired = cursor.fetchone()["count"]

            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "max_entries": self.config.max_entries,
                "ttl_seconds": self.config.ttl_seconds,
                "db_path": self.db_path,
            }

        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"error": str(e)}

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Cache connection closed")

    def __enter__(self) -> "SQLiteCache":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"SQLiteCache(db_path={self.db_path!r}, ttl={self.config.ttl_seconds}s)"


__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "CacheError",
    "SQLiteCache",
    "generate_cache_key",
]
