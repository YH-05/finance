"""SQLite-based cache manager for SEC EDGAR filing data.

This module provides a persistent cache implementation using SQLite
for storing extracted filing text with TTL (time-to-live) support.

Features
--------
- SQLite-backed persistent storage
- TTL-based expiration (default 90 days)
- UPSERT (INSERT OR REPLACE) for idempotent saves
- Thread-safe operations via threading.Lock
- Automatic expired entry cleanup
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from utils_core.logging import get_logger

from ..config import DEFAULT_CACHE_DIR
from ..errors import CacheError

logger = get_logger(__name__)

# Default TTL for cached filing text (90 days)
DEFAULT_TTL_DAYS = 90


class CacheManager:
    """SQLite-based cache manager for SEC EDGAR filing text.

    Provides persistent caching with TTL support, automatic cleanup
    of expired entries, and thread-safe operations.

    Parameters
    ----------
    cache_dir : Path | None
        Directory for the SQLite database file. Uses DEFAULT_CACHE_DIR
        if not specified. The directory is created if it does not exist.
    ttl_days : int
        Default time-to-live for cached entries in days.

    Attributes
    ----------
    cache_dir : Path
        Directory containing the SQLite database
    ttl_days : int
        Default TTL in days
    db_path : Path
        Full path to the SQLite database file

    Examples
    --------
    >>> cache = CacheManager(cache_dir=Path("/tmp/test_cache"), ttl_days=30)
    >>> cache.save_text("0001234567-24-000001", "Filing text content")
    >>> cache.get_cached_text("0001234567-24-000001")
    'Filing text content'
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_days: int = DEFAULT_TTL_DAYS,
    ) -> None:
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.ttl_days = ttl_days
        self.db_path = self.cache_dir / "edgar_cache.db"
        self._lock = threading.Lock()

        logger.debug(
            "Initializing CacheManager",
            cache_dir=str(self.cache_dir),
            ttl_days=self.ttl_days,
            db_path=str(self.db_path),
        )

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connection with transaction handling.

        Yields
        ------
        sqlite3.Connection
            A database connection with autocommit disabled.

        Raises
        ------
        CacheError
            If the database transaction fails.
        """
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise CacheError(
                f"Database transaction failed: {e}",
                context={"operation": "transaction", "db_path": str(self.db_path)},
            ) from e
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize the database schema.

        Creates the edgar_cache table and indexes if they do not exist.

        Raises
        ------
        CacheError
            If schema initialization fails.
        """
        logger.debug("Initializing cache database schema", db_path=str(self.db_path))
        try:
            with self._connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS edgar_cache (
                        filing_id TEXT PRIMARY KEY,
                        text TEXT NOT NULL,
                        cached_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_edgar_cache_expires_at
                    ON edgar_cache (expires_at)
                """)

            logger.debug("Cache database schema initialized", db_path=str(self.db_path))

        except CacheError:
            raise
        except Exception as e:
            logger.warning(
                "Failed to initialize cache database", error=str(e), exc_info=True
            )
            raise CacheError(
                f"Failed to initialize cache database: {e}",
                context={"operation": "init_db", "db_path": str(self.db_path)},
            ) from e

    def get_cached_text(self, filing_id: str) -> str | None:
        """Retrieve cached text for a filing.

        Returns the cached text if it exists and has not expired.
        Expired entries are deleted on access.

        Parameters
        ----------
        filing_id : str
            The unique filing identifier (accession number)

        Returns
        -------
        str | None
            The cached text, or None if not found or expired

        Raises
        ------
        CacheError
            If the database query fails

        Examples
        --------
        >>> cache = CacheManager()
        >>> cache.get_cached_text("0001234567-24-000001")
        'Filing text content'
        >>> cache.get_cached_text("nonexistent-id")
        None
        """
        logger.debug("Cache get", filing_id=filing_id)

        try:
            now = int(time.time())

            with self._connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT text, expires_at
                    FROM edgar_cache
                    WHERE filing_id = ?
                    """,
                    (filing_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    logger.debug("Cache miss", filing_id=filing_id)
                    return None

                if row["expires_at"] < now:
                    logger.debug(
                        "Cache expired",
                        filing_id=filing_id,
                        expired_at=row["expires_at"],
                        now=now,
                    )
                    conn.execute(
                        "DELETE FROM edgar_cache WHERE filing_id = ?",
                        (filing_id,),
                    )
                    return None

                logger.debug("Cache hit", filing_id=filing_id)
                return row["text"]

        except CacheError:
            raise
        except Exception as e:
            logger.warning(
                "Failed to get cached text", filing_id=filing_id, exc_info=True
            )
            raise CacheError(
                f"Failed to get cached text for filing '{filing_id}': {e}",
                context={"operation": "get_cached_text", "filing_id": filing_id},
            ) from e

    def save_text(
        self,
        filing_id: str,
        text: str,
        ttl_days: int | None = None,
    ) -> None:
        """Save filing text to the cache.

        Uses INSERT OR REPLACE (UPSERT) to update existing entries.

        Parameters
        ----------
        filing_id : str
            The unique filing identifier (accession number)
        text : str
            The filing text content to cache
        ttl_days : int | None
            Time-to-live in days. Uses instance default if not specified.

        Raises
        ------
        CacheError
            If the save operation fails

        Examples
        --------
        >>> cache = CacheManager()
        >>> cache.save_text("0001234567-24-000001", "Filing text content")
        >>> cache.save_text("0001234567-24-000001", "Updated text", ttl_days=180)
        """
        effective_ttl = ttl_days if ttl_days is not None else self.ttl_days
        now = int(time.time())
        expires_at = now + (effective_ttl * 86400)

        logger.debug(
            "Cache save",
            filing_id=filing_id,
            text_length=len(text),
            ttl_days=effective_ttl,
            expires_at=expires_at,
        )

        try:
            with self._lock, self._connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO edgar_cache
                    (filing_id, text, cached_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (filing_id, text, now, expires_at),
                )

            logger.info(
                "Cache entry saved",
                filing_id=filing_id,
                text_length=len(text),
                ttl_days=effective_ttl,
            )

        except CacheError:
            raise
        except Exception as e:
            logger.warning(
                "Failed to save text to cache", filing_id=filing_id, exc_info=True
            )
            raise CacheError(
                f"Failed to save text for filing '{filing_id}': {e}",
                context={
                    "operation": "save_text",
                    "filing_id": filing_id,
                    "text_length": len(text),
                },
            ) from e

    def clear_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns
        -------
        int
            Number of expired entries removed

        Raises
        ------
        CacheError
            If the cleanup operation fails

        Examples
        --------
        >>> cache = CacheManager()
        >>> removed = cache.clear_expired()
        >>> print(f"Removed {removed} expired entries")
        Removed 3 expired entries
        """
        logger.debug("Clearing expired cache entries")

        try:
            now = int(time.time())

            with self._lock, self._connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM edgar_cache WHERE expires_at < ?",
                    (now,),
                )
                expired_count = cursor.fetchone()["count"]

                if expired_count > 0:
                    conn.execute(
                        "DELETE FROM edgar_cache WHERE expires_at < ?",
                        (now,),
                    )

            logger.info(
                "Expired cache entries cleared",
                removed_count=expired_count,
            )
            return expired_count

        except CacheError:
            raise
        except Exception as e:
            logger.warning("Failed to clear expired cache entries", exc_info=True)
            raise CacheError(
                f"Failed to clear expired cache entries: {e}",
                context={"operation": "clear_expired"},
            ) from e

    def __repr__(self) -> str:
        """Return string representation."""
        return f"CacheManager(cache_dir={self.cache_dir!r}, ttl_days={self.ttl_days})"


__all__ = [
    "DEFAULT_TTL_DAYS",
    "CacheManager",
]
