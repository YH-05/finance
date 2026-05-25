"""High-level client for FRASER REST API access.

This module provides the :class:`FraserClient` class, which integrates
:class:`FraserSession` (HTTP + rate limiting + retries) with
:func:`market.fraser.parser` (Pydantic validation) and a shared
:class:`market.cache.cache.SQLiteCache` so that callers receive typed
domain models with transparent caching.

Eight public methods are exposed, mirroring the FRASER REST endpoints
used by the project:

- :meth:`list_items` (``GET /items``)
- :meth:`get_item` (``GET /item/{id}``)
- :meth:`get_title` (``GET /title/{id}``)
- :meth:`get_toc` (``GET /item/{id}/toc``)
- :meth:`get_authors` (``GET /authors``)
- :meth:`get_subjects` (``GET /subjects``)
- :meth:`get_themes` (``GET /themes``)
- :meth:`get_timeline` (``GET /title/{id}/timeline``)

Each method follows the same cache-key → cache.get → session.get →
parser → cache.set pipeline so behaviour stays uniform and easy to test.

See Also
--------
market.fraser.session : Underlying HTTP session.
market.fraser.cache : TTL constants + ``get_fraser_cache`` factory.
market.fraser.parser : Pydantic validation wrappers.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

from market.fraser import parser
from market.fraser.cache import (
    AUTHOR_SUBJECT_THEME_TTL,
    ITEM_METADATA_TTL,
    ITEMS_LIST_TTL,
    TIMELINE_TTL,
    TITLE_METADATA_TTL,
    get_fraser_cache,
    make_fraser_cache_key,
)
from market.fraser.constants import FRASER_API_KEY_ENV
from market.fraser.errors import FraserAuthError
from market.fraser.rate_limiter import get_fraser_rate_limiter
from market.fraser.session import FraserSession
from market.fraser.types import FraserConfig
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.cache.cache import SQLiteCache
    from market.fraser.models import (
        FraserAuthor,
        FraserItem,
        FraserSubject,
        FraserTheme,
        FraserTimelineEvent,
        FraserTitle,
        FraserTocEntry,
    )

logger = get_logger(__name__)


class FraserClient:
    """High-level client for the FRASER REST API.

    Parameters
    ----------
    config : FraserConfig | None
        FRASER configuration. When ``None``, a default configuration is
        built and the API key is read from the ``FRASER_API_KEY``
        environment variable. ``FraserAuthError`` is raised if no key is
        configured.
    session : FraserSession | None
        Optional pre-built session. Useful for tests / dependency
        injection. When supplied, ``config`` is ignored for session
        construction (but still used for cache prefix consistency).
    cache : SQLiteCache | None
        Optional pre-built cache. When ``None``, a default persistent
        cache is created via :func:`get_fraser_cache`.

    Raises
    ------
    FraserAuthError
        When no API key is available (neither in ``config`` nor in the
        environment).

    Examples
    --------
    >>> with FraserClient() as client:  # doctest: +SKIP
    ...     items = client.list_items(title_id=677, limit=10)
    ...     print(len(items))
    """

    def __init__(
        self,
        config: FraserConfig | None = None,
        session: FraserSession | None = None,
        cache: SQLiteCache | None = None,
    ) -> None:
        if config is None:
            api_key = os.environ.get(FRASER_API_KEY_ENV, "")
            if not api_key and session is None:
                raise FraserAuthError(
                    "FRASER API key not provided. "
                    f"Set {FRASER_API_KEY_ENV} environment variable or pass "
                    "FraserConfig(api_key=...) explicitly."
                )
            config = FraserConfig(api_key=api_key)

        self._config: FraserConfig = config

        if session is None:
            self._session: FraserSession = FraserSession(
                config=self._config,
                rate_limiter=get_fraser_rate_limiter(self._config),
                retry_config=self._config.retry_config,
            )
        else:
            self._session = session

        self._cache: SQLiteCache = cache if cache is not None else get_fraser_cache()

        logger.info(
            "FraserClient initialised",
            base_url=self._config.base_url,
        )

    # =========================================================================
    # Context manager
    # =========================================================================

    def __enter__(self) -> FraserClient:
        """Return ``self`` for use in ``with`` statements."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close the underlying session on context exit."""
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()
        logger.debug("FraserClient closed")

    # =========================================================================
    # Public endpoint methods
    # =========================================================================

    def list_items(
        self,
        title_id: int,
        limit: int = 50,
        page: int = 1,
        *,
        use_cache: bool = True,
    ) -> list[FraserItem]:
        """List items for a given title (``GET /items``).

        Parameters
        ----------
        title_id : int
            FRASER title identifier (e.g., ``677`` for FOMC).
        limit : int
            Page size (default: 50).
        page : int
            1-based page index (default: 1).
        use_cache : bool
            When ``False``, bypass the cache for this call.

        Returns
        -------
        list[FraserItem]
            Items belonging to the title.

        Examples
        --------
        >>> items = client.list_items(title_id=677, limit=5)  # doctest: +SKIP
        """
        endpoint = "/items"
        params: dict[str, Any] = {
            "titleId": title_id,
            "limit": limit,
            "page": page,
        }
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=ITEMS_LIST_TTL,
            use_cache=use_cache,
        )
        return parser.parse_items(data)

    def get_item(
        self,
        item_id: int,
        *,
        use_cache: bool = True,
    ) -> FraserItem:
        """Fetch a single item by ID (``GET /item/{id}``)."""
        endpoint = f"/item/{item_id}"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=ITEM_METADATA_TTL,
            use_cache=use_cache,
        )
        return parser.parse_item(data)

    def get_title(
        self,
        title_id: int,
        *,
        use_cache: bool = True,
    ) -> FraserTitle:
        """Fetch a title by ID (``GET /title/{id}``)."""
        endpoint = f"/title/{title_id}"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=TITLE_METADATA_TTL,
            use_cache=use_cache,
        )
        return parser.parse_title(data)

    def get_toc(
        self,
        item_id: int,
        *,
        use_cache: bool = True,
    ) -> list[FraserTocEntry]:
        """Fetch an item's table of contents (``GET /item/{id}/toc``)."""
        endpoint = f"/item/{item_id}/toc"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=ITEM_METADATA_TTL,
            use_cache=use_cache,
        )
        return parser.parse_toc(data)

    def get_authors(
        self,
        *,
        use_cache: bool = True,
    ) -> list[FraserAuthor]:
        """Fetch the master authors list (``GET /authors``)."""
        endpoint = "/authors"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=AUTHOR_SUBJECT_THEME_TTL,
            use_cache=use_cache,
        )
        return parser.parse_authors(data)

    def get_subjects(
        self,
        *,
        use_cache: bool = True,
    ) -> list[FraserSubject]:
        """Fetch the master subjects list (``GET /subjects``)."""
        endpoint = "/subjects"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=AUTHOR_SUBJECT_THEME_TTL,
            use_cache=use_cache,
        )
        return parser.parse_subjects(data)

    def get_themes(
        self,
        *,
        use_cache: bool = True,
    ) -> list[FraserTheme]:
        """Fetch the master themes list (``GET /themes``)."""
        endpoint = "/themes"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=AUTHOR_SUBJECT_THEME_TTL,
            use_cache=use_cache,
        )
        return parser.parse_themes(data)

    def get_timeline(
        self,
        title_id: int,
        *,
        use_cache: bool = True,
    ) -> list[FraserTimelineEvent]:
        """Fetch a title's timeline (``GET /title/{id}/timeline``)."""
        endpoint = f"/title/{title_id}/timeline"
        params: dict[str, Any] = {}
        data = self._fetch_json(
            endpoint=endpoint,
            params=params,
            ttl=TIMELINE_TTL,
            use_cache=use_cache,
        )
        return parser.parse_timeline(data)

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _fetch_json(
        self,
        *,
        endpoint: str,
        params: dict[str, Any],
        ttl: int,
        use_cache: bool,
    ) -> Any:
        """Fetch a JSON payload with cache-aware read-through semantics.

        Pipeline
        --------
        1. Build a deterministic cache key via :func:`make_fraser_cache_key`.
        2. When ``use_cache`` is ``True``, return the cached JSON if hit.
        3. On miss (or ``use_cache=False``), call
           :meth:`FraserSession.get_with_retry` and decode the body.
        4. Store the decoded body in the cache for ``ttl`` seconds.

        Parameters
        ----------
        endpoint : str
            API endpoint path (e.g., ``"/items"``).
        params : dict[str, Any]
            Query parameters.
        ttl : int
            TTL in seconds for the cache entry.
        use_cache : bool
            When ``False``, skip the cache lookup but still write the
            fresh response to the cache for subsequent callers.

        Returns
        -------
        Any
            Decoded JSON payload (dict / list / scalar).
        """
        key = make_fraser_cache_key(endpoint, params)
        if use_cache:
            cached = self._cache.get(key)
            if cached is not None:
                logger.debug(
                    "Cache hit",
                    endpoint=endpoint,
                    key_prefix=key[:24] + "...",
                )
                return json.loads(cached) if isinstance(cached, str) else cached

        response = self._session.get_with_retry(endpoint, params=params)
        data: Any = response.json()

        try:
            payload = json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            payload = None
        if payload is not None:
            self._cache.set(key, payload, ttl=ttl)
            logger.debug(
                "Cache populated",
                endpoint=endpoint,
                key_prefix=key[:24] + "...",
                ttl_seconds=ttl,
            )

        return data


__all__ = ["FraserClient"]
