"""Abstract base class for FRASER document-type fetchers.

:class:`BaseFraserFetcher` encapsulates the common pipeline shared by
all FRASER document fetchers (FOMC minutes, FOMC statements, Beige
Book, etc.):

1. ``client.list_items`` / ``client.get_item`` for metadata retrieval.
2. ``_filter_by_year_range`` for date-window filtering.
3. ``downloader.download_with_meta`` for atomic file persistence with
   a ``.meta.json`` sidecar.

Subclasses must provide :meth:`doc_type` so that the base class can
resolve the correct FRASER ``title_id`` (via ``KNOWN_TITLE_IDS`` and the
``fraser_titles.json`` fallback) and pick the correct on-disk
subdirectory (via ``DOC_TYPE_SUBDIRS``).

Notes
-----
This base class deliberately does **not** inherit from
``market.fred.BaseDataFetcher``: ``BaseDataFetcher`` is tailored for
pandas ``DataFrame`` outputs, whereas FRASER returns structured JSON
documents plus binary / text file downloads. Two distinct shapes →
two distinct bases (per HF1 review).

See Also
--------
market.fraser.client : :class:`FraserClient` used for metadata calls.
market.fraser.downloader : :class:`FraserDownloader` used for asset
    persistence.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from market.fraser.client import FraserClient
from market.fraser.constants import DOC_TYPE_SUBDIRS, KNOWN_TITLE_IDS
from market.fraser.downloader import FraserDownloader
from market.fraser.errors import FraserValidationError
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.fraser.models import FraserItem
    from market.fraser.types import DocType

logger = get_logger(__name__)


# Default location for the operator-confirmed ``title_id`` mapping.
# Populated by ``python -m market.fraser.scripts.discover_titles``.
DEFAULT_TITLES_JSON_PATH: Path = Path("data/config/fraser_titles.json")


class BaseFraserFetcher(ABC):
    """Abstract base for FRASER document-type fetchers.

    Parameters
    ----------
    client : FraserClient | None
        Pre-built FRASER client. When ``None``, a default client is
        instantiated (which reads ``FRASER_API_KEY`` from the
        environment / ``.env`` file).
    downloader : FraserDownloader | None
        Pre-built downloader. When ``None``, a default downloader is
        instantiated that reuses the client's HTTP session and writes
        under ``base_dir``.
    base_dir : Path
        Root directory for downloaded assets and meta-data sidecars
        (default: ``Path('data/raw/fraser')``).

    Notes
    -----
    Subclasses must override :meth:`doc_type` to expose the relevant
    :class:`market.fraser.types.DocType` member. The base class uses
    this to look up the canonical ``title_id`` and to compute the
    on-disk subdirectory layout.

    Examples
    --------
    >>> from market.fraser.fetchers.fomc import FOMCMinutesFetcher
    >>> fetcher = FOMCMinutesFetcher()  # doctest: +SKIP
    >>> meetings = fetcher.list_minutes((2024, 2024))  # doctest: +SKIP
    """

    def __init__(
        self,
        client: FraserClient | None = None,
        downloader: FraserDownloader | None = None,
        base_dir: Path = Path("data/raw/fraser"),
    ) -> None:
        # Lazily build the default client only when not injected so that
        # constructor calls in test code (which inject mocks) never hit
        # the ``FRASER_API_KEY`` env lookup.
        if client is None:
            client = FraserClient()
        self._client: FraserClient = client

        if downloader is None:
            downloader = FraserDownloader(
                session=self._client._session, base_dir=base_dir
            )
        self._downloader: FraserDownloader = downloader

        self._base_dir: Path = Path(base_dir)

        logger.debug(
            "BaseFraserFetcher initialised",
            base_dir=str(self._base_dir),
            doc_type=str(self.doc_type),
        )

    # =========================================================================
    # Abstract interface
    # =========================================================================

    @property
    @abstractmethod
    def doc_type(self) -> DocType:
        """Document type identifier (e.g., ``DocType.FOMC_MINUTES``)."""

    # =========================================================================
    # Public properties
    # =========================================================================

    @cached_property
    def title_id(self) -> int:
        """Resolve the FRASER ``title_id`` for :attr:`doc_type`.

        The resolution is cached per-instance: the first access hits
        :meth:`_resolve_title_id` (which may read
        ``fraser_titles.json`` from disk), subsequent accesses are O(1).

        Returns
        -------
        int
            The numeric FRASER title identifier.

        Raises
        ------
        FraserValidationError
            When neither :data:`KNOWN_TITLE_IDS` nor the operator JSON
            override provides a value for :attr:`doc_type`.
        """
        return self._resolve_title_id()

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _resolve_title_id(self) -> int:
        """Resolve the FRASER ``title_id`` for the current document type.

        Resolution order:

        1. ``KNOWN_TITLE_IDS[self.doc_type.value]`` — the hard-coded,
           reviewed mapping.
        2. ``DEFAULT_TITLES_JSON_PATH`` — operator-confirmed override
           emitted by the ``discover_titles`` CLI.

        Raises
        ------
        FraserValidationError
            When neither source supplies a non-``None`` integer.
        """
        key = self.doc_type.value

        known_value = KNOWN_TITLE_IDS.get(key)
        if isinstance(known_value, int):
            return known_value

        path = DEFAULT_TITLES_JSON_PATH
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                logger.warning(
                    "Failed to read fraser_titles.json",
                    path=str(path),
                    error=str(exc),
                )
                payload = {}
            value = payload.get(key) if isinstance(payload, dict) else None
            if isinstance(value, int):
                return value

        raise FraserValidationError(
            (
                f"title_id for {key!r} is not configured. "
                "Set KNOWN_TITLE_IDS or run "
                "`python -m market.fraser.scripts.discover_titles`."
            ),
            field="title_id",
            value=key,
        )

    def _filter_by_year_range(
        self,
        items: list[FraserItem],
        year_range: tuple[int, int],
    ) -> list[FraserItem]:
        """Filter ``items`` whose ``date.year`` falls within ``year_range``.

        Parameters
        ----------
        items : list[FraserItem]
            Source items to filter.
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.

        Returns
        -------
        list[FraserItem]
            Items whose ``date.year`` is within the window.
        """
        start, end = year_range
        return [item for item in items if start <= item.date.year <= end]

    def _doc_subdir(self) -> str:
        """Return the on-disk subdirectory for :attr:`doc_type`."""
        return DOC_TYPE_SUBDIRS[self.doc_type.value]

    @staticmethod
    def _convert_to[M: BaseModel](item: FraserItem, model_cls: type[M]) -> M:
        """Re-validate ``item``'s fields against the more specific ``model_cls``.

        Used by concrete fetchers to upcast a generic :class:`FraserItem`
        returned by ``list_items`` into the document-type specific Pydantic
        model (``FOMCMeeting``, ``BeigeBookReport``, etc.). Centralising
        the conversion here removes the three-class duplication of
        ``_to_fomc_meeting`` that existed previously
        (see PR review HIGH-2 / project-115 Wave4).

        Parameters
        ----------
        item : FraserItem
            Generic item returned by ``FraserClient.list_items``.
        model_cls : type[M]
            Pydantic V2 model subclass to project ``item`` into.

        Returns
        -------
        M
            Validated instance of ``model_cls``.
        """
        return model_cls.model_validate(item.model_dump(by_alias=False))

    # =========================================================================
    # Public fetch operations
    # =========================================================================

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: Literal["txt", "pdf"] = "txt",
    ) -> tuple[Path, FraserItem]:
        """Fetch metadata for ``item_id`` and download the asset.

        The asset is written to
        ``<base_dir>/<doc_subdir>/<YYYY-MM-DD>_<item_id>.<ext>``
        and a ``.meta.json`` sidecar with the model dump is co-located.

        Parameters
        ----------
        item_id : int
            FRASER item identifier.
        prefer : Literal["txt", "pdf"]
            Preferred asset format. The other format is used as fallback
            when the preferred one is absent.

        Returns
        -------
        tuple[Path, FraserItem]
            ``(asset_path, item)``.
        """
        item = self._client.get_item(item_id)
        asset_path, _meta_path = self._downloader.download_with_meta(
            item, self._doc_subdir(), prefer=prefer
        )
        return asset_path, item

    def fetch_pdf(self, item_id: int) -> tuple[Path, FraserItem]:
        """Convenience wrapper that forces ``prefer='pdf'`` on :meth:`fetch_text`.

        Returns
        -------
        tuple[Path, FraserItem]
            ``(asset_path, item)`` — same shape as :meth:`fetch_text`.
        """
        return self.fetch_text(item_id, prefer="pdf")


__all__ = ["DEFAULT_TITLES_JSON_PATH", "BaseFraserFetcher"]
