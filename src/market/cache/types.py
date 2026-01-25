"""Type definitions for the market.cache package.

This module provides type definitions for cache operations including:
- Cache configuration dataclass
"""

from dataclasses import dataclass

__all__ = [
    "CacheConfig",
]


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for cache behavior.

    This is an immutable configuration dataclass that defines how caching
    should behave in the market package.

    Parameters
    ----------
    enabled : bool
        Whether caching is enabled (default: True)
    ttl_seconds : int
        Time-to-live for cache entries in seconds (default: 3600).
        Must be a positive integer.
    max_entries : int
        Maximum number of cache entries (default: 1000).
        Must be a positive integer.
    db_path : str | None
        Path to SQLite database file (default: None, uses in-memory).
        When None, an in-memory SQLite database is used.

    Examples
    --------
    >>> config = CacheConfig(ttl_seconds=7200, max_entries=500)
    >>> config.ttl_seconds
    7200

    >>> # In-memory cache (default)
    >>> config = CacheConfig()
    >>> config.db_path is None
    True

    >>> # Persistent cache
    >>> config = CacheConfig(db_path="/path/to/cache.db")
    >>> config.db_path
    '/path/to/cache.db'

    Notes
    -----
    This dataclass is frozen (immutable) to ensure thread-safety and
    prevent accidental modification of cache configuration during runtime.
    """

    enabled: bool = True
    ttl_seconds: int = 3600
    max_entries: int = 1000
    db_path: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration values after initialization.

        Raises
        ------
        ValueError
            If ttl_seconds or max_entries is not positive
        """
        if self.ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be positive, got {self.ttl_seconds}")
        if self.max_entries <= 0:
            raise ValueError(f"max_entries must be positive, got {self.max_entries}")
