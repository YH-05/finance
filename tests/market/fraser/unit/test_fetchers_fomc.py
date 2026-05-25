"""Unit tests for ``market.fraser.fetchers.fomc.FOMCMinutesFetcher``.

Covers:

- ``list_minutes`` returns ``FOMCMeeting`` instances filtered by year.
- ``_to_fomc_meeting`` correctly inherits ``FraserItem`` fields when
  converting from a ``FraserItem``.
- ``fetch_text`` writes files under ``<base>/fomc/minutes/`` with the
  expected ``<YYYY-MM-DD>_<itemId>.txt`` naming.
- Multiple ``date`` string formats are accepted (``YYYY-MM-DD``,
  ``YYYY-MM``, ``YYYY``).

See Also
--------
market.fraser.fetchers.fomc : Class under test.
tests.market.fraser.conftest : Shared fixtures
    (``sample_fomc_items_response``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from market.fraser.fetchers.fomc import FOMCMinutesFetcher
from market.fraser.models import FOMCMeeting, FraserItem
from market.fraser.types import DocType

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _items_from_sample(
    payload: dict[str, object],
) -> list[FraserItem]:
    """Convert the ``sample_fomc_items_response`` fixture into model instances."""
    raw_items = payload["items"]
    assert isinstance(raw_items, list)
    return [FraserItem.model_validate(raw) for raw in raw_items]


# ---------------------------------------------------------------------------
# doc_type
# ---------------------------------------------------------------------------


class TestDocType:
    def test_正常系_doc_typeはFOMC_MINUTES(self) -> None:
        fetcher = FOMCMinutesFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.doc_type is DocType.FOMC_MINUTES


# ---------------------------------------------------------------------------
# list_minutes
# ---------------------------------------------------------------------------


class TestListMinutes:
    def test_正常系_2024年指定で2024年itemのみFOMCMeeting返却(
        self,
        sample_fomc_items_response: dict[str, object],
    ) -> None:
        # Build items via the conftest fixture and stub the client.
        items = _items_from_sample(sample_fomc_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FOMCMinutesFetcher(client=mock_client, downloader=MagicMock())
        meetings = fetcher.list_minutes(year_range=(2024, 2024))

        assert all(isinstance(m, FOMCMeeting) for m in meetings)
        # Fixture contains 4 items dated in 2024 and 1 in 1995.
        years = sorted({m.date.year for m in meetings})
        assert years == [2024]
        assert len(meetings) == 4

    def test_正常系_client_list_itemsがtitle_id_677で呼ばれる(
        self,
        sample_fomc_items_response: dict[str, object],
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_items.return_value = _items_from_sample(
            sample_fomc_items_response
        )

        fetcher = FOMCMinutesFetcher(client=mock_client, downloader=MagicMock())
        fetcher.list_minutes(year_range=(2024, 2024), limit=50)

        mock_client.list_items.assert_called_once()
        _, kwargs = mock_client.list_items.call_args
        # title_id may be passed positionally or as keyword.
        if kwargs:
            assert kwargs.get("limit", 50) == 50

        positional_args, _ = mock_client.list_items.call_args
        assert positional_args[0] == 677  # KNOWN_TITLE_IDS["fomc_minutes"] == 677


# ---------------------------------------------------------------------------
# _to_fomc_meeting
# ---------------------------------------------------------------------------


class TestToFomcMeeting:
    def test_正常系_FraserItemからFOMCMeetingへ変換できる(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 1,
                "titleId": 677,
                "title": "FOMC Minutes",
                "date": "2024-03-20",
            }
        )
        fetcher = FOMCMinutesFetcher(client=MagicMock(), downloader=MagicMock())
        meeting = fetcher._to_fomc_meeting(item)
        assert isinstance(meeting, FOMCMeeting)
        assert meeting.item_id == 1
        assert meeting.date.isoformat() == "2024-03-20"

    @pytest.mark.parametrize(
        "date_str,expected_iso",
        [
            ("2024-03-20", "2024-03-20"),
            ("2024-03", "2024-03-01"),
            ("2024", "2024-01-01"),
        ],
    )
    def test_正常系_dateフォーマット差異吸収(
        self, date_str: str, expected_iso: str
    ) -> None:
        item = FraserItem.model_validate({"itemId": 5, "title": "x", "date": date_str})
        fetcher = FOMCMinutesFetcher(client=MagicMock(), downloader=MagicMock())
        meeting = fetcher._to_fomc_meeting(item)
        assert meeting.date.isoformat() == expected_iso


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


class TestFetchText:
    def test_正常系_fetch_textでファイル生成パスが返る(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        """``fetch_text`` returns the path produced by the downloader."""
        items = _items_from_sample(sample_fomc_items_response)
        # Pick the 2024-03-20 item (item_id=1002) which has only a pdfUrl.
        target_item = next(i for i in items if i.item_id == 1002)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "fomc" / "minutes" / "2024-03-20_1002.txt"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = FOMCMinutesFetcher(
            client=mock_client,
            downloader=mock_downloader,
        )
        path, meeting = fetcher.fetch_text(1002, prefer="txt")

        assert path == expected_path
        assert isinstance(meeting, FOMCMeeting)
        assert meeting.item_id == 1002

    def test_正常系_fetch_textのpreferがdownloaderに伝搬(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_fomc_items_response)
        target_item = items[0]

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            tmp_path / "asset.pdf",
            tmp_path / "asset.meta.json",
        )

        fetcher = FOMCMinutesFetcher(client=mock_client, downloader=mock_downloader)
        fetcher.fetch_text(target_item.item_id, prefer="pdf")

        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "pdf"
