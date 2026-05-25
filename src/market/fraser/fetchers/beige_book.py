"""Beige Book fetcher with parallel download support.

This module exposes :class:`BeigeBookFetcher`, a thin specialisation of
:class:`BaseFraserFetcher` for FRASER Beige Book reports. It adds a
parallel :meth:`BeigeBookFetcher.fetch_all` helper that fans out
``fetch_text`` calls across a bounded :class:`ThreadPoolExecutor`, using
the same partial-failure-tolerant ``dict[int, Path | Exception]``
pattern established by :func:`edgar.batch._run_batch`.

The ``max_workers=4`` default keeps the worst-case effective throughput
well below the FRASER 30 req/min ceiling enforced by
:class:`market.alphavantage.rate_limiter.DualWindowRateLimiter`. Each
worker thread serialises through the shared rate limiter via the
underlying :class:`market.fraser.session.FraserSession`, so the parallel
pipeline is correct under contention even when the rate limit is
saturated.

See Also
--------
market.fraser.fetchers.base : Shared abstract base class.
market.fraser.fetchers.fomc : FOMC-specific fetcher pattern reused here.
edgar.batch : Reference ``_run_batch`` ThreadPoolExecutor pattern.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from tqdm import tqdm

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import BeigeBookReport
from market.fraser.types import DocType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from market.fraser.models import FraserItem

logger = get_logger(__name__)


# Hard upper bound on ``max_workers`` to keep parallel ``fetch_text``
# calls within the FRASER 30 req/min rate-limit envelope. Five concurrent
# downloads can momentarily exceed the limiter (each ``fetch_text``
# triggers two upstream requests: ``get_item`` + asset download), so we
# cap at four (per project-108 plan task-6 design note).
MAX_WORKERS_LIMIT: int = 4


class BeigeBookFetcher(BaseFraserFetcher):
    """Fetcher for Beige Book report documents.

    Provides the standard ``list_reports`` / ``fetch_text`` surface plus
    a :meth:`fetch_all` helper that parallelises downloads with bounded
    concurrency and partial-failure tolerance.

    Examples
    --------
    >>> from market.fraser import BeigeBookFetcher
    >>> fetcher = BeigeBookFetcher()  # doctest: +SKIP
    >>> reports = fetcher.list_reports(year_range=(2023, 2024))  # doctest: +SKIP
    >>> results = fetcher.fetch_all((2023, 2024), max_workers=4)  # doctest: +SKIP
    >>> for item_id, outcome in results.items():  # doctest: +SKIP
    ...     if isinstance(outcome, Exception):
    ...         print(f"{item_id}: failed - {outcome}")
    ...     else:
    ...         print(f"{item_id}: {outcome}")
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.BEIGE_BOOK`."""
        return DocType.BEIGE_BOOK

    # =========================================================================
    # Public API
    # =========================================================================

    def list_reports(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[BeigeBookReport]:
        """List Beige Book reports whose ``date.year`` is in ``year_range``.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[BeigeBookReport]
            Beige Book reports covering the requested calendar window.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        filtered = self._filter_by_year_range(items, year_range)
        return [self._to_beige_book_report(item) for item in filtered]

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: str = "txt",
    ) -> tuple[Path, BeigeBookReport]:
        """Fetch and download a single Beige Book report.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`BeigeBookReport`.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        report = self._to_beige_book_report(item)
        return path, report

    def fetch_all(
        self,
        year_range: tuple[int, int],
        *,
        max_workers: int = 4,
        prefer: str = "txt",
        limit: int = 100,
    ) -> dict[int, Path | Exception]:
        """Download every Beige Book report in ``year_range`` in parallel.

        Uses :class:`concurrent.futures.ThreadPoolExecutor` to fan out
        :meth:`fetch_text` calls, then collects the results into a
        ``{item_id: Path | Exception}`` dict so that partial failures
        never abort the batch. Per-future exceptions are logged at
        ``WARNING`` level and stored in the result dict.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window.
        max_workers : int
            Maximum number of concurrent download threads
            (default ``4``). Values above :data:`MAX_WORKERS_LIMIT` are
            silently clamped to keep the worker pool within the FRASER
            30 req/min ceiling.
        prefer : str
            Preferred asset format passed through to :meth:`fetch_text`
            (``"txt"`` or ``"pdf"``; default ``"txt"``).
        limit : int
            Maximum number of items requested from FRASER when listing
            reports (default: ``100``).

        Returns
        -------
        dict[int, Path | Exception]
            Mapping of ``item_id`` to downloaded asset path on success,
            or the raised exception instance on failure.
        """
        if max_workers < 1:
            raise ValueError(
                f"max_workers must be >= 1, got {max_workers}",
            )
        effective_workers = min(max_workers, MAX_WORKERS_LIMIT)

        reports = self.list_reports(year_range, limit=limit)
        results: dict[int, Path | Exception] = {}

        if not reports:
            logger.info(
                "BeigeBookFetcher.fetch_all: no reports in range",
                year_range=year_range,
            )
            return results

        total = len(reports)
        logger.info(
            "BeigeBookFetcher.fetch_all starting",
            total=total,
            max_workers=effective_workers,
            prefer=prefer,
        )

        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            future_to_id = {
                executor.submit(self._fetch_text_path, report.item_id, prefer): (
                    report.item_id
                )
                for report in reports
            }

            with tqdm(total=total, desc="Beige Book") as pbar:
                for future in as_completed(future_to_id):
                    item_id = future_to_id[future]
                    try:
                        results[item_id] = future.result()
                    except Exception as exc:
                        results[item_id] = exc
                        logger.warning(
                            "Beige Book fetch_all task failed",
                            item_id=item_id,
                            error=str(exc),
                            error_type=type(exc).__name__,
                            exc_info=True,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failed_count = total - success_count
        logger.info(
            "BeigeBookFetcher.fetch_all completed",
            total=total,
            success=success_count,
            failed=failed_count,
        )
        return results

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _fetch_text_path(self, item_id: int, prefer: str) -> Path:
        """Return only the ``Path`` portion of :meth:`fetch_text`.

        This thin wrapper keeps :meth:`fetch_all` independent of the
        model returned by :meth:`fetch_text` (Beige Book reports) so
        that the ``Future.result()`` payload is just a ``Path``.

        Parameters
        ----------
        item_id : int
            FRASER item identifier.
        prefer : str
            Preferred asset format.

        Returns
        -------
        Path
            Downloaded asset path.
        """
        path, _report = self.fetch_text(item_id, prefer=prefer)
        return path

    def _to_beige_book_report(self, item: FraserItem) -> BeigeBookReport:
        """Convert a generic :class:`FraserItem` to :class:`BeigeBookReport`.

        Mirrors the ``FOMCMeeting`` conversion pattern in
        :mod:`market.fraser.fetchers.fomc` (the future refactor will
        lift these helpers onto :class:`BaseFraserFetcher` — out of
        scope per project-108 plan).
        """
        if isinstance(item, BeigeBookReport):
            return item
        payload = item.model_dump(by_alias=False)
        return BeigeBookReport.model_validate(payload)


__all__ = [
    "MAX_WORKERS_LIMIT",
    "BeigeBookFetcher",
]
