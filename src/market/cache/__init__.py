"""Cache module for the market package.

This module provides caching functionality for market data including:
- CacheConfig: Configuration for cache behavior
- SQLiteCache: SQLite-based cache with TTL support
- generate_cache_key: Generate unique cache keys for market data
- get_cache/reset_cache: Global cache instance management
- create_persistent_cache: Create file-based persistent cache

Public API
----------
CacheConfig
    Configuration dataclass for cache behavior (frozen/immutable)
SQLiteCache
    SQLite-based cache with TTL support and thread-safe operations
generate_cache_key
    Generate unique cache keys for market data
get_cache
    Get or create the global cache instance
reset_cache
    Reset the global cache instance
create_persistent_cache
    Create a persistent file-based cache
DEFAULT_CACHE_CONFIG
    Default in-memory cache configuration
DEFAULT_CACHE_DB_PATH
    Default path for persistent cache database
PERSISTENT_CACHE_CONFIG
    Default persistent cache configuration
"""

from .cache import (
    DEFAULT_CACHE_CONFIG,
    DEFAULT_CACHE_DB_PATH,
    PERSISTENT_CACHE_CONFIG,
    SQLiteCache,
    create_persistent_cache,
    generate_cache_key,
    get_cache,
    reset_cache,
)
from .types import CacheConfig

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "DEFAULT_CACHE_DB_PATH",
    "PERSISTENT_CACHE_CONFIG",
    "CacheConfig",
    "SQLiteCache",
    "create_persistent_cache",
    "generate_cache_key",
    "get_cache",
    "reset_cache",
]
