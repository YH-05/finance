"""Cache subpackage for SEC EDGAR filing data.

This subpackage provides SQLite-based caching for extracted filing text
with TTL (time-to-live) support and thread-safe operations.

Public API
----------
CacheManager
    SQLite-based cache manager for filing text
"""

from .manager import CacheManager

__all__ = [
    "CacheManager",
]
