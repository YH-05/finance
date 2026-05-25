"""Cache helpers for the FRASER REST API module.

This module provides TTL constants for each FRASER endpoint category
and convenience functions for obtaining a SQLiteCache instance configured
for FRASER data, plus a SHA-256 based cache-key builder.

The implementation deliberately delegates to the shared
``market.cache.cache`` infrastructure (``SQLiteCache``,
``create_persistent_cache``) and does **not** define its own
``SQLiteCache`` subclass, mirroring the pattern used by
``market.alphavantage.cache`` and ``market.jquants.cache``. This decision
was confirmed during PR1 HF1 review (see ``docs/project/project-108``).

See Also
--------
market.cache.cache : Core ``SQLiteCache`` implementation.
market.alphavantage.cache : Reference implementation with the same
    delegation pattern.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Final

from market.cache.cache import SQLiteCache, create_persistent_cache
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# TTL constants (seconds)
# ---------------------------------------------------------------------------

TITLE_METADATA_TTL: Final[int] = 2592000
"""TTL for FRASER title metadata (30 days).

Title-level metadata (publisher, item_count, description) changes
infrequently.
"""

ITEMS_LIST_TTL: Final[int] = 604800
"""TTL for paginated item lists under a title (7 days).

Item listings can pick up new releases, so a shorter TTL is used.
"""

ITEM_METADATA_TTL: Final[int] = 2592000
"""TTL for individual item metadata (30 days)."""

AUTHOR_SUBJECT_THEME_TTL: Final[int] = 2592000
"""TTL for author / subject / theme tag lookups (30 days).

These reference tables are essentially static.
"""

TIMELINE_TTL: Final[int] = 604800
"""TTL for timeline event lookups (7 days)."""


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def get_fraser_cache(ttl: int = ITEM_METADATA_TTL) -> SQLiteCache:
    """Get a SQLiteCache instance configured for FRASER data.

    Creates a persistent cache sharing the same ``market_data.db``
    database as the rest of the ``market`` package (no separate FRASER
    database file, no separate process). Callers must use the
    ``"fraser:"`` prefix on every cache key so the namespace stays
    distinct.

    Parameters
    ----------
    ttl : int
        Default TTL in seconds applied when a caller does not pass
        an explicit ``ttl`` to ``SQLiteCache.set`` (default:
        :data:`ITEM_METADATA_TTL` = 30 days).

    Returns
    -------
    SQLiteCache
        A configured cache instance writing to the shared
        ``market_data.db``.

    Examples
    --------
    >>> cache = get_fraser_cache()  # doctest: +SKIP
    >>> cache.set("fraser:title:677", payload, ttl=TITLE_METADATA_TTL)
    """
    cache = create_persistent_cache(
        ttl_seconds=ttl,
        max_entries=10000,
    )
    logger.debug("FRASER cache instance created", ttl_seconds=ttl)
    return cache


def make_fraser_cache_key(endpoint: str, params: dict[str, Any]) -> str:
    """Build a deterministic, collision-resistant FRASER cache key.

    The key is constructed as ``"fraser:" + sha256(endpoint + sorted_params)``
    so that:

    - The ``"fraser:"`` prefix isolates FRASER entries from other
      packages sharing the same ``market_data.db``.
    - ``params`` ordering is normalised via ``sort_keys=True`` so that
      callers passing dictionaries in different insertion orders still
      produce the same key.

    Parameters
    ----------
    endpoint : str
        API endpoint path (e.g., ``"/items"``, ``"/title/677"``).
    params : dict[str, Any]
        Query parameters used for the request. May be empty.

    Returns
    -------
    str
        Cache key of the form ``"fraser:<64-char hex digest>"``.

    Examples
    --------
    >>> key = make_fraser_cache_key("/items", {"titleId": 677, "limit": 10})
    >>> key.startswith("fraser:")
    True
    >>> len(key) == len("fraser:") + 64
    True
    """
    payload = json.dumps(
        {"endpoint": endpoint, "params": params},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"fraser:{digest}"


__all__ = [
    "AUTHOR_SUBJECT_THEME_TTL",
    "ITEMS_LIST_TTL",
    "ITEM_METADATA_TTL",
    "TIMELINE_TTL",
    "TITLE_METADATA_TTL",
    "get_fraser_cache",
    "make_fraser_cache_key",
]
