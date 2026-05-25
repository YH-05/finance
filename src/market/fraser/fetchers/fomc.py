"""FOMC document fetchers built on :class:`BaseFraserFetcher`.

This module exposes three FOMC fetchers, each a thin specialisation of
:class:`BaseFraserFetcher` that only differs in its :attr:`doc_type`
(and therefore in the resolved FRASER ``title_id``):

- :class:`FOMCMinutesFetcher` — FOMC meeting minutes (PR3).
- :class:`FOMCStatementsFetcher` — FOMC policy statements (PR4 前半).
- :class:`FOMCPressConferencesFetcher` — FOMC chair press conference
  transcripts (PR4 前半).

All three share the ``_to_fomc_meeting`` conversion helper and expose
the same public surface (``list_*`` + ``fetch_text``). Lifting the
helper onto :class:`BaseFraserFetcher` is deliberately deferred to a
future refactor (out of scope for PR4 前半 per project-108 plan).

See Also
--------
market.fraser.fetchers.base : Shared abstract base class.
market.fraser.models : :class:`FOMCMeeting` Pydantic V2 model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import FOMCMeeting
from market.fraser.types import DocType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from market.fraser.models import FraserItem

logger = get_logger(__name__)


class FOMCMinutesFetcher(BaseFraserFetcher):
    """Fetcher for FOMC Minutes documents.

    Examples
    --------
    >>> from market.fraser import FOMCMinutesFetcher
    >>> fetcher = FOMCMinutesFetcher()  # doctest: +SKIP
    >>> meetings = fetcher.list_minutes(year_range=(2024, 2024))  # doctest: +SKIP
    >>> for meeting in meetings:  # doctest: +SKIP
    ...     print(meeting.date, meeting.item_id)
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.FOMC_MINUTES`."""
        return DocType.FOMC_MINUTES

    # =========================================================================
    # Public API
    # =========================================================================

    def list_minutes(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[FOMCMeeting]:
        """List FOMC Minutes whose ``date.year`` is within ``year_range``.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[FOMCMeeting]
            FOMC Minutes covering the requested calendar window.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        filtered = self._filter_by_year_range(items, year_range)
        return [self._to_fomc_meeting(item) for item in filtered]

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: str = "txt",
    ) -> tuple[Path, FOMCMeeting]:
        """Fetch and download a single FOMC Minutes item.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`FOMCMeeting` for ergonomic call-site typing.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        meeting = self._to_fomc_meeting(item)
        return path, meeting

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _to_fomc_meeting(self, item: FraserItem) -> FOMCMeeting:
        """Convert a generic :class:`FraserItem` to :class:`FOMCMeeting`.

        Uses ``model_dump`` + ``model_validate`` so that the inherited
        fields (``item_id``, ``date``, ``location`` etc.) round-trip
        through Pydantic's validation pipeline. This preserves any
        ``meeting_date`` / ``meeting_type`` fields that the FRASER
        response may carry.
        """
        if isinstance(item, FOMCMeeting):
            return item
        # ``by_alias=False`` keeps the snake_case keys ``FOMCMeeting``
        # expects on input; ``model_validate`` handles the rest.
        payload = item.model_dump(by_alias=False)
        return FOMCMeeting.model_validate(payload)


class FOMCStatementsFetcher(BaseFraserFetcher):
    """Fetcher for FOMC policy Statement documents.

    Mirrors :class:`FOMCMinutesFetcher` 1:1 with two differences:

    - :attr:`doc_type` is :data:`DocType.FOMC_STATEMENTS`.
    - The resolved ``title_id`` therefore comes from the
      ``"fomc_statements"`` slot of ``KNOWN_TITLE_IDS`` /
      ``fraser_titles.json``.

    Examples
    --------
    >>> from market.fraser import FOMCStatementsFetcher
    >>> fetcher = FOMCStatementsFetcher()  # doctest: +SKIP
    >>> statements = fetcher.list_statements(year_range=(2024, 2024))  # doctest: +SKIP
    >>> for stmt in statements:  # doctest: +SKIP
    ...     print(stmt.date, stmt.item_id)
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.FOMC_STATEMENTS`."""
        return DocType.FOMC_STATEMENTS

    # =========================================================================
    # Public API
    # =========================================================================

    def list_statements(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[FOMCMeeting]:
        """List FOMC Statements whose ``date.year`` is within ``year_range``.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[FOMCMeeting]
            FOMC Statements covering the requested calendar window.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        filtered = self._filter_by_year_range(items, year_range)
        return [self._to_fomc_meeting(item) for item in filtered]

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: str = "txt",
    ) -> tuple[Path, FOMCMeeting]:
        """Fetch and download a single FOMC Statement item.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`FOMCMeeting` for ergonomic call-site typing.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        meeting = self._to_fomc_meeting(item)
        return path, meeting

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _to_fomc_meeting(self, item: FraserItem) -> FOMCMeeting:
        """Convert a generic :class:`FraserItem` to :class:`FOMCMeeting`.

        See :meth:`FOMCMinutesFetcher._to_fomc_meeting` for details.
        Duplicated here intentionally (project-108 task-5 scope) — the
        future refactor will lift this onto :class:`BaseFraserFetcher`.
        """
        if isinstance(item, FOMCMeeting):
            return item
        payload = item.model_dump(by_alias=False)
        return FOMCMeeting.model_validate(payload)


class FOMCPressConferencesFetcher(BaseFraserFetcher):
    """Fetcher for FOMC chair Press Conference transcript documents.

    Mirrors :class:`FOMCMinutesFetcher` 1:1 with two differences:

    - :attr:`doc_type` is :data:`DocType.FOMC_PRESS_CONFERENCES`.
    - The resolved ``title_id`` therefore comes from the
      ``"fomc_press_conferences"`` slot of ``KNOWN_TITLE_IDS`` /
      ``fraser_titles.json``.

    Examples
    --------
    >>> from market.fraser import FOMCPressConferencesFetcher
    >>> fetcher = FOMCPressConferencesFetcher()  # doctest: +SKIP
    >>> pcs = fetcher.list_press_conferences(year_range=(2024, 2024))  # doctest: +SKIP
    >>> for pc in pcs:  # doctest: +SKIP
    ...     print(pc.date, pc.item_id)
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.FOMC_PRESS_CONFERENCES`."""
        return DocType.FOMC_PRESS_CONFERENCES

    # =========================================================================
    # Public API
    # =========================================================================

    def list_press_conferences(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[FOMCMeeting]:
        """List FOMC Press Conferences whose ``date.year`` is within ``year_range``.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[FOMCMeeting]
            FOMC Press Conference transcripts covering the requested
            calendar window.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        filtered = self._filter_by_year_range(items, year_range)
        return [self._to_fomc_meeting(item) for item in filtered]

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: str = "txt",
    ) -> tuple[Path, FOMCMeeting]:
        """Fetch and download a single FOMC Press Conference item.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`FOMCMeeting` for ergonomic call-site typing.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        meeting = self._to_fomc_meeting(item)
        return path, meeting

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _to_fomc_meeting(self, item: FraserItem) -> FOMCMeeting:
        """Convert a generic :class:`FraserItem` to :class:`FOMCMeeting`.

        See :meth:`FOMCMinutesFetcher._to_fomc_meeting` for details.
        Duplicated here intentionally (project-108 task-5 scope) — the
        future refactor will lift this onto :class:`BaseFraserFetcher`.
        """
        if isinstance(item, FOMCMeeting):
            return item
        payload = item.model_dump(by_alias=False)
        return FOMCMeeting.model_validate(payload)


__all__ = [
    "FOMCMinutesFetcher",
    "FOMCPressConferencesFetcher",
    "FOMCStatementsFetcher",
]
