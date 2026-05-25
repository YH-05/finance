"""FOMC document fetchers built on :class:`BaseFraserFetcher`.

This module currently exposes :class:`FOMCMinutesFetcher` — the only
FOMC fetcher introduced by PR3. :class:`FOMCStatementsFetcher` and
:class:`FOMCPressConferencesFetcher` will be added in PR4 once their
``title_id`` values are discovered.

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


__all__ = ["FOMCMinutesFetcher"]
