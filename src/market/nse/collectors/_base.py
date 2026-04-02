"""Base mixin for NSE collectors with shared session management.

Provides ``_get_session()`` and ``__init__`` logic shared across all
NSE collector classes (QuoteCollector, IndicesCollector,
CorporateCollector, StockListCollector).
"""

from __future__ import annotations

from market.nse.session import NseSession
from utils_core.logging import get_logger

logger = get_logger(__name__)


class NseCollectorMixin:
    """Mixin providing NSE session lifecycle management.

    All NSE collectors share the same session injection pattern:
    accept an optional ``NseSession`` in the constructor and resolve
    it lazily via ``_get_session()``.

    Parameters
    ----------
    session : NseSession | None
        Pre-configured NseSession for dependency injection.
        If None, a new NseSession is created when needed.
    """

    def __init__(self, session: NseSession | None = None) -> None:
        self._session_instance: NseSession | None = session

    def _get_session(self) -> tuple[NseSession, bool]:
        """Resolve the session: use injected or create new.

        Returns
        -------
        tuple[NseSession, bool]
            A tuple of (session, should_close).  ``should_close`` is True
            when a new session was created internally and must be closed
            by the caller.

        Examples
        --------
        >>> collector = QuoteCollector()
        >>> session, should_close = collector._get_session()
        >>> try:
        ...     response = session.get_with_retry(url)
        ... finally:
        ...     if should_close:
        ...         session.close()
        """
        if self._session_instance is not None:
            return self._session_instance, False
        return NseSession(), True
