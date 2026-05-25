"""Unit tests for ``MonetaryPolicyReportFetcher``.

Covers:

- ``doc_type`` reports :data:`DocType.MONETARY_POLICY_REPORT`.
- ``list_reports`` filters by year and returns
  :class:`MonetaryPolicyReport` instances.
- Historical Humphrey-Hawkins archive (1979-2000) is reachable.
- ``fetch_text`` defaults to ``prefer='pdf'`` because the legacy
  archive is PDF-only.

See Also
--------
market.fraser.fetchers.monetary_policy : Class under test.
tests.market.fraser.conftest : Shared fixtures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from market.fraser.fetchers.monetary_policy import MonetaryPolicyReportFetcher
from market.fraser.models import FraserItem, MonetaryPolicyReport
from market.fraser.types import DocType

if TYPE_CHECKING:
    from pathlib import Path

_MPR_TITLE_ID: int = 33333


@pytest.fixture
def mpr_title_id(monkeypatch: pytest.MonkeyPatch) -> int:
    """Inject a dummy title_id for ``monetary_policy_report`` into KNOWN_TITLE_IDS."""
    from market.fraser.fetchers import base as base_module

    monkeypatch.setitem(
        base_module.KNOWN_TITLE_IDS, "monetary_policy_report", _MPR_TITLE_ID
    )
    return _MPR_TITLE_ID


def _items_from_sample(payload: dict[str, object]) -> list[FraserItem]:
    raw_items = payload["items"]
    assert isinstance(raw_items, list)
    return [FraserItem.model_validate(raw) for raw in raw_items]


# ---------------------------------------------------------------------------
# doc_type
# ---------------------------------------------------------------------------


class TestDocType:
    def test_正常系_doc_typeはMONETARY_POLICY_REPORT(self) -> None:
        fetcher = MonetaryPolicyReportFetcher(
            client=MagicMock(), downloader=MagicMock()
        )
        assert fetcher.doc_type is DocType.MONETARY_POLICY_REPORT


# ---------------------------------------------------------------------------
# list_reports
# ---------------------------------------------------------------------------


class TestListReports:
    def test_正常系_2020_2024年指定でモダン期2件取得(
        self,
        sample_mpr_items_response: dict[str, object],
        mpr_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_mpr_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = MonetaryPolicyReportFetcher(
            client=mock_client, downloader=MagicMock()
        )
        reports = fetcher.list_reports(year_range=(2020, 2024))

        assert all(isinstance(r, MonetaryPolicyReport) for r in reports)
        # Fixture contains 2 items in 2024 plus 1 in 2000 and 1 in 1979.
        assert len(reports) == 2
        assert {r.date.year for r in reports} == {2024}

    def test_正常系_歴史アーカイブ_HumphreyHawkins対応(
        self,
        sample_mpr_items_response: dict[str, object],
        mpr_title_id: int,
    ) -> None:
        """``year_range`` accepts historical lower bounds (1979)."""
        items = _items_from_sample(sample_mpr_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = MonetaryPolicyReportFetcher(
            client=mock_client, downloader=MagicMock()
        )
        reports = fetcher.list_reports(year_range=(1979, 2024))

        assert len(reports) == 4
        years = sorted({r.date.year for r in reports})
        assert years == [1979, 2000, 2024]
        # Confirm the Humphrey-Hawkins-era item is included.
        hh = next(r for r in reports if r.date.year == 1979)
        assert hh.item_id == 4099
        assert "Humphrey-Hawkins" in (hh.title or "")


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


class TestFetchText:
    def test_正常系_fetch_text_prefer_pdfデフォルト動作(
        self,
        sample_mpr_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_mpr_items_response)
        target_item = next(i for i in items if i.item_id == 4001)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "monetary_policy" / "2024-02-09_4001.pdf"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = MonetaryPolicyReportFetcher(
            client=mock_client,
            downloader=mock_downloader,
        )
        # Call without ``prefer`` — default must be ``"pdf"``.
        path, report = fetcher.fetch_text(4001)

        assert path == expected_path
        assert isinstance(report, MonetaryPolicyReport)
        # Confirm ``prefer="pdf"`` was forwarded to the downloader.
        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "pdf"

    def test_正常系_fetch_text_prefer_txt明示で上書き(
        self,
        sample_mpr_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_mpr_items_response)
        target_item = next(i for i in items if i.item_id == 4001)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            tmp_path / "asset.txt",
            tmp_path / "asset.meta.json",
        )

        fetcher = MonetaryPolicyReportFetcher(
            client=mock_client, downloader=mock_downloader
        )
        fetcher.fetch_text(4001, prefer="txt")

        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "txt"


# ---------------------------------------------------------------------------
# _to_mpr
# ---------------------------------------------------------------------------


class TestToMPR:
    def test_正常系_FraserItemからMonetaryPolicyReportへ変換(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 99,
                "title": "MPR",
                "date": "2024-01-01",
            }
        )
        fetcher = MonetaryPolicyReportFetcher(
            client=MagicMock(), downloader=MagicMock()
        )
        report = fetcher._to_mpr(item)
        assert isinstance(report, MonetaryPolicyReport)
        assert report.item_id == 99

    def test_正常系_MonetaryPolicyReport入力はそのまま返却(self) -> None:
        report = MonetaryPolicyReport.model_validate(
            {
                "itemId": 11,
                "title": "MPR",
                "date": "2024-01-01",
                "reportPeriod": "February 2024",
            }
        )
        fetcher = MonetaryPolicyReportFetcher(
            client=MagicMock(), downloader=MagicMock()
        )
        result = fetcher._to_mpr(report)
        assert result is report
        assert result.report_period == "February 2024"
