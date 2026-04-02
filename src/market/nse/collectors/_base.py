"""Base mixin for NSE collectors with shared session management.

Provides ``_get_session()``, ``validate()``, and ``__init__`` logic
shared across all NSE collector classes (QuoteCollector,
IndicesCollector, CorporateCollector, StockListCollector).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from market.nse.session import NseSession
from utils_core.logging import get_logger

logger = get_logger(__name__)

__all__ = ["NseCollectorMixin"]


class NseCollectorMixin:
    """Mixin providing NSE session lifecycle management and data validation.

    All NSE collectors share the same session injection pattern and
    validation logic.  Subclasses must define ``_REQUIRED_COLUMNS`` as a
    class-level ``frozenset[str]`` listing the column names that must be
    present in a valid DataFrame.

    Parameters
    ----------
    session : NseSession | None
        Pre-configured NseSession for dependency injection.
        If None, a new NseSession is created when needed.

    Attributes
    ----------
    _REQUIRED_COLUMNS : frozenset[str]
        Column names required for ``validate()`` to return True.
        Must be defined by each concrete subclass.
    """

    _REQUIRED_COLUMNS: frozenset[str] = frozenset()

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

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched data DataFrame.

        Checks that the DataFrame:
        - Is not empty
        - Contains all columns listed in ``_REQUIRED_COLUMNS``

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = QuoteCollector()
        >>> df = pd.DataFrame({"symbol": ["RELIANCE"], "company_name": ["Reliance Industries Limited"]})
        >>> collector.validate(df)
        True
        >>> collector.validate(pd.DataFrame())
        False
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        missing = self._REQUIRED_COLUMNS - set(df.columns)
        if missing:
            logger.warning(
                "Validation failed: missing required columns",
                missing_columns=sorted(missing),
                actual_columns=list(df.columns),
            )
            return False

        logger.debug(
            "Validation passed",
            row_count=len(df),
        )
        return True
