"""FRB speech fetcher with optional speaker filtering.

This module exposes :class:`FRBSpeechFetcher`, a thin specialisation of
:class:`BaseFraserFetcher` for FRASER Federal Reserve Board speeches.
The fetcher mirrors the FOMC pattern but adds case-insensitive
``speaker`` filtering on :meth:`list_speeches`, allowing callers to
restrict results to a single speaker (e.g., ``"Powell"``, ``"Volcker"``).

The historical archive on FRASER goes back to the 1960s for major
speakers, so the ``year_range`` parameter accepts any non-negative
integer pair; no implicit lower bound is enforced.

See Also
--------
market.fraser.fetchers.base : Shared abstract base class.
market.fraser.fetchers.fomc : Reference fetcher pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import FRBSpeech
from market.fraser.types import DocType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class FRBSpeechFetcher(BaseFraserFetcher):
    """Fetcher for Federal Reserve Board speech documents.

    Examples
    --------
    >>> from market.fraser import FRBSpeechFetcher
    >>> fetcher = FRBSpeechFetcher()  # doctest: +SKIP
    >>> powell = fetcher.list_speeches(  # doctest: +SKIP
    ...     year_range=(2024, 2024), speaker="Powell"
    ... )
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.FRB_SPEECHES`."""
        return DocType.FRB_SPEECHES

    # =========================================================================
    # Public API
    # =========================================================================

    def list_speeches(
        self,
        year_range: tuple[int, int],
        *,
        speaker: str | None = None,
        limit: int = 100,
    ) -> list[FRBSpeech]:
        """List FRB speeches whose ``date.year`` is in ``year_range``.

        When ``speaker`` is provided, the result is further filtered to
        items whose ``authors[*].name`` (case-insensitive) contains the
        supplied substring. Items without authors are silently dropped
        from the speaker-filtered subset (no author info → cannot match).

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        speaker : str | None
            Optional speaker substring. Case-insensitive
            (``"Powell"`` == ``"powell"`` == ``"POWELL"``). When
            ``None``, no speaker filter is applied.
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[FRBSpeech]
            Filtered speeches.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        year_filtered = self._filter_by_year_range(items, year_range)
        speeches = [self._convert_to(item, FRBSpeech) for item in year_filtered]

        if speaker is None:
            return speeches
        return self._filter_by_speaker(speeches, speaker)

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: Literal["txt", "pdf"] = "txt",
    ) -> tuple[Path, FRBSpeech]:
        """Fetch and download a single FRB speech.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`FRBSpeech`.

        Returns
        -------
        tuple[Path, FRBSpeech]
            ``(asset_path, speech)``.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        speech = self._convert_to(item, FRBSpeech)
        return path, speech

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _filter_by_speaker(
        self,
        speeches: list[FRBSpeech],
        speaker: str,
    ) -> list[FRBSpeech]:
        """Filter ``speeches`` by case-insensitive speaker substring.

        Matching is performed against three fields, in order of
        preference: ``speech.speaker``, ``speech.authors[*].name``, and
        ``speech.description``. A speech matches when any of those
        fields (after ``str.lower()``) contains the lowered ``speaker``
        substring.

        Parameters
        ----------
        speeches : list[FRBSpeech]
            Source speeches.
        speaker : str
            Speaker substring (case-insensitive).

        Returns
        -------
        list[FRBSpeech]
            Speeches whose speaker / author metadata mentions
            ``speaker``.
        """
        needle = speaker.lower()
        result: list[FRBSpeech] = []
        for speech in speeches:
            if speech.speaker and needle in speech.speaker.lower():
                result.append(speech)
                continue
            authors = speech.authors or []
            if any(a.name and needle in a.name.lower() for a in authors):
                result.append(speech)
                continue
            if speech.description and needle in speech.description.lower():
                result.append(speech)
        return result


__all__ = ["FRBSpeechFetcher"]
