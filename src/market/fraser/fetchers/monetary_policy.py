"""Monetary Policy Report fetcher.

This module exposes :class:`MonetaryPolicyReportFetcher`, a thin
specialisation of :class:`BaseFraserFetcher` for FRASER Monetary Policy
Reports to the Congress. The fetcher defaults to ``prefer='pdf'``
because the historical archive (including the Humphrey-Hawkins reports
from 1979-2000) is overwhelmingly PDF-only — preferring TXT would force
a PDF fallback for the majority of items.

See Also
--------
market.fraser.fetchers.base : Shared abstract base class.
market.fraser.fetchers.fomc : Reference fetcher pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import MonetaryPolicyReport
from market.fraser.types import DocType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class MonetaryPolicyReportFetcher(BaseFraserFetcher):
    """Fetcher for Monetary Policy Report documents.

    Examples
    --------
    >>> from market.fraser import MonetaryPolicyReportFetcher
    >>> fetcher = MonetaryPolicyReportFetcher()  # doctest: +SKIP
    >>> reports = fetcher.list_reports(year_range=(2020, 2024))  # doctest: +SKIP
    >>> path, report = fetcher.fetch_text(reports[0].item_id)  # doctest: +SKIP
    """

    @property
    def doc_type(self) -> DocType:
        """Return :data:`DocType.MONETARY_POLICY_REPORT`."""
        return DocType.MONETARY_POLICY_REPORT

    def list_reports(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[MonetaryPolicyReport]:
        """List Monetary Policy Reports in ``year_range``.

        Parameters
        ----------
        year_range : tuple[int, int]
            Inclusive ``(start_year, end_year)`` window. Accepts
            historical lower bounds (e.g., ``1979`` for the original
            Humphrey-Hawkins reports).
        limit : int
            Maximum number of items returned by the underlying
            ``GET /items`` call (default: ``100``).

        Returns
        -------
        list[MonetaryPolicyReport]
            Monetary Policy Reports covering the requested calendar
            window.
        """
        items = self._client.list_items(self.title_id, limit=limit)
        filtered = self._filter_by_year_range(items, year_range)
        return [self._convert_to(item, MonetaryPolicyReport) for item in filtered]

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: Literal["txt", "pdf"] = "pdf",
    ) -> tuple[Path, MonetaryPolicyReport]:
        """Fetch and download a single Monetary Policy Report.

        Defaults to ``prefer='pdf'`` because the historical archive
        (1979-2000 Humphrey-Hawkins reports in particular) is almost
        exclusively PDF-only. Override with ``prefer='txt'`` to force
        the text-first selection path.

        See :meth:`BaseFraserFetcher.fetch_text` for the underlying
        pipeline. The return type narrows the second element to
        :class:`MonetaryPolicyReport`.

        Returns
        -------
        tuple[Path, MonetaryPolicyReport]
            ``(asset_path, report)``.
        """
        path, item = super().fetch_text(item_id, prefer=prefer)
        report = self._convert_to(item, MonetaryPolicyReport)
        return path, report


__all__ = ["MonetaryPolicyReportFetcher"]
