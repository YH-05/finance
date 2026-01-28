"""Cache class for data provider results.

This module provides caching functionality for data fetched from providers.
Data is stored in Parquet format with TTL-based invalidation.
"""

import hashlib
import time
from pathlib import Path

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


class Cache:
    """Data cache with TTL-based invalidation.

    Caches data fetched from providers in Parquet format with
    configurable Time To Live (TTL) for automatic invalidation.

    Parameters
    ----------
    cache_path : str | Path
        Directory path for cache storage
    ttl_hours : int, default=24
        Time To Live in hours for cache entries

    Examples
    --------
    >>> cache = Cache("/tmp/cache", ttl_hours=24)
    >>> cache.set("key", df)
    >>> data = cache.get("key")
    """

    def __init__(self, cache_path: str | Path, ttl_hours: int = 24) -> None:
        """Initialize Cache.

        Parameters
        ----------
        cache_path : str | Path
            Directory path for cache storage
        ttl_hours : int, default=24
            Time To Live in hours for cache entries
        """
        self.cache_path = Path(cache_path)
        self.ttl_hours = ttl_hours

        # Create cache directory if it doesn't exist
        self.cache_path.mkdir(parents=True, exist_ok=True)

        logger.debug(
            "Cache initialized",
            cache_path=str(self.cache_path),
            ttl_hours=self.ttl_hours,
        )

    def get(self, key: str) -> pd.DataFrame | None:
        """Get cached data by key.

        Returns None if the cache entry doesn't exist or has expired.

        Parameters
        ----------
        key : str
            Cache key

        Returns
        -------
        pd.DataFrame | None
            Cached data if valid, None otherwise
        """
        if not self.is_valid(key):
            logger.debug("Cache miss or expired", key=key)
            return None

        file_path = self._key_to_path(key)

        try:
            data = pd.read_parquet(file_path)
            logger.debug(
                "Cache hit",
                key=key,
                file_path=str(file_path),
                rows=len(data),
            )
            return data
        except Exception as e:
            logger.error(
                "Failed to read cache",
                key=key,
                file_path=str(file_path),
                error=str(e),
            )
            return None

    def set(self, key: str, data: pd.DataFrame) -> None:
        """Store data in cache.

        Parameters
        ----------
        key : str
            Cache key
        data : pd.DataFrame
            Data to cache
        """
        file_path = self._key_to_path(key)

        logger.debug(
            "Saving data to cache",
            key=key,
            file_path=str(file_path),
            rows=len(data),
        )

        data.to_parquet(file_path)

        logger.info(
            "Cache entry saved",
            key=key,
            file_path=str(file_path),
            rows=len(data),
        )

    def invalidate(self, key: str) -> None:
        """Invalidate (delete) cached entry.

        Does nothing if the cache entry doesn't exist.

        Parameters
        ----------
        key : str
            Cache key to invalidate
        """
        file_path = self._key_to_path(key)

        if file_path.exists():
            file_path.unlink()
            logger.info("Cache entry invalidated", key=key, file_path=str(file_path))
        else:
            logger.debug("Cache entry not found for invalidation", key=key)

    def is_valid(self, key: str) -> bool:
        """Check if cache entry is valid (exists and within TTL).

        Parameters
        ----------
        key : str
            Cache key

        Returns
        -------
        bool
            True if cache is valid, False otherwise
        """
        file_path = self._key_to_path(key)

        if not file_path.exists():
            logger.debug("Cache file does not exist", key=key)
            return False

        # Check TTL
        file_mtime = file_path.stat().st_mtime
        current_time = time.time()
        age_hours = (current_time - file_mtime) / 3600

        is_valid = age_hours < self.ttl_hours

        logger.debug(
            "Cache validity check",
            key=key,
            age_hours=round(age_hours, 2),
            ttl_hours=self.ttl_hours,
            is_valid=is_valid,
        )

        return is_valid

    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path.

        Uses SHA256 hash to create a filesystem-safe filename from
        the cache key. This handles special characters, long keys,
        and non-ASCII characters safely.

        Parameters
        ----------
        key : str
            Cache key

        Returns
        -------
        Path
            File path for the cache entry
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        # Sanitize key for logging/debugging (keep first 20 chars)
        safe_key = "".join(c if c.isalnum() or c in "_-" else "_" for c in key[:20])
        filename = f"{safe_key}_{key_hash}.parquet"

        return self.cache_path / filename
