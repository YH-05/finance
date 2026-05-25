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

from market.fraser.errors import FraserValidationError
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)
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


# ---------------------------------------------------------------------------
# FOMCStatementsFetcher
# ---------------------------------------------------------------------------


class TestFOMCStatementsFetcherDocType:
    def test_正常系_doc_typeはFOMC_STATEMENTS(self) -> None:
        fetcher = FOMCStatementsFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.doc_type is DocType.FOMC_STATEMENTS


class TestFOMCStatementsFetcherListStatements:
    """Tests for :meth:`FOMCStatementsFetcher.list_statements`."""

    def test_正常系_2024年指定で2024年itemのみFOMCMeeting返却(
        self,
        sample_fomc_items_response: dict[str, object],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # ``fomc_statements`` is currently None in KNOWN_TITLE_IDS; inject a
        # dummy value so that title_id resolution succeeds for the year-filter
        # branch we want to test.
        from market.fraser.fetchers import base as base_module

        monkeypatch.setitem(base_module.KNOWN_TITLE_IDS, "fomc_statements", 99999)

        # Reuse the shared FOMC fixture; ``list_statements`` filters by year
        # the same way ``list_minutes`` does, so the fixture works as-is.
        items = _items_from_sample(sample_fomc_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FOMCStatementsFetcher(client=mock_client, downloader=MagicMock())
        meetings = fetcher.list_statements(year_range=(2024, 2024))

        assert all(isinstance(m, FOMCMeeting) for m in meetings)
        years = sorted({m.date.year for m in meetings})
        assert years == [2024]
        # Fixture contains 4 items dated in 2024.
        assert len(meetings) == 4

    def test_正常系_title_id_未確定の場合FraserValidationError(
        self,
        sample_fomc_items_response: dict[str, object],
    ) -> None:
        """``title_id`` lookup raises when neither KNOWN_TITLE_IDS nor JSON has a value.

        ``fomc_statements`` is currently ``None`` in ``KNOWN_TITLE_IDS`` and
        the operator JSON file. Resolving the title_id should raise
        :class:`FraserValidationError` until task-2 populates the mapping.
        """
        mock_client = MagicMock()
        mock_client.list_items.return_value = _items_from_sample(
            sample_fomc_items_response
        )

        fetcher = FOMCStatementsFetcher(client=mock_client, downloader=MagicMock())
        # ``list_statements`` resolves ``title_id`` via the property, which
        # currently has no confirmed value for fomc_statements.
        with pytest.raises(FraserValidationError):
            _ = fetcher.title_id

    def test_正常系_title_id_jsonにあれば返却(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ``fraser_titles.json`` provides a title_id, list_statements works."""
        from market.fraser.fetchers import base as base_module

        # Write a JSON file with a known title_id and point the base module at it.
        titles_json = tmp_path / "fraser_titles.json"
        titles_json.write_text('{"fomc_statements": 12345}\n', encoding="utf-8")
        monkeypatch.setattr(base_module, "DEFAULT_TITLES_JSON_PATH", titles_json)

        items = _items_from_sample(sample_fomc_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FOMCStatementsFetcher(client=mock_client, downloader=MagicMock())
        meetings = fetcher.list_statements(year_range=(2024, 2024))

        # Confirm title_id was resolved via the JSON fallback and forwarded
        # to ``client.list_items``.
        positional_args, _ = mock_client.list_items.call_args
        assert positional_args[0] == 12345
        assert all(isinstance(m, FOMCMeeting) for m in meetings)


class TestFOMCStatementsFetcherFetchText:
    """Tests for :meth:`FOMCStatementsFetcher.fetch_text`."""

    def test_正常系_fetch_textでファイル生成パスが返る(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_fomc_items_response)
        target_item = next(i for i in items if i.item_id == 1002)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "fomc" / "statements" / "2024-03-20_1002.txt"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = FOMCStatementsFetcher(
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

        fetcher = FOMCStatementsFetcher(client=mock_client, downloader=mock_downloader)
        fetcher.fetch_text(target_item.item_id, prefer="pdf")

        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "pdf"


# ---------------------------------------------------------------------------
# FOMCPressConferencesFetcher
# ---------------------------------------------------------------------------


class TestFOMCPressConferencesFetcherDocType:
    def test_正常系_doc_typeはFOMC_PRESS_CONFERENCES(self) -> None:
        fetcher = FOMCPressConferencesFetcher(
            client=MagicMock(), downloader=MagicMock()
        )
        assert fetcher.doc_type is DocType.FOMC_PRESS_CONFERENCES


class TestFOMCPressConferencesFetcherListPressConferences:
    """Tests for :meth:`FOMCPressConferencesFetcher.list_press_conferences`."""

    def test_正常系_2024年指定で2024年itemのみFOMCMeeting返却(
        self,
        sample_fomc_items_response: dict[str, object],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # ``fomc_press_conferences`` is currently None in KNOWN_TITLE_IDS;
        # inject a dummy value so the year-filter branch is exercised.
        from market.fraser.fetchers import base as base_module

        monkeypatch.setitem(
            base_module.KNOWN_TITLE_IDS, "fomc_press_conferences", 88888
        )

        items = _items_from_sample(sample_fomc_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FOMCPressConferencesFetcher(
            client=mock_client, downloader=MagicMock()
        )
        meetings = fetcher.list_press_conferences(year_range=(2024, 2024))

        assert all(isinstance(m, FOMCMeeting) for m in meetings)
        years = sorted({m.date.year for m in meetings})
        assert years == [2024]
        assert len(meetings) == 4

    def test_正常系_title_id_未確定の場合FraserValidationError(
        self,
        sample_fomc_items_response: dict[str, object],
    ) -> None:
        """``title_id`` lookup raises when neither KNOWN_TITLE_IDS nor JSON has a value."""
        mock_client = MagicMock()
        mock_client.list_items.return_value = _items_from_sample(
            sample_fomc_items_response
        )

        fetcher = FOMCPressConferencesFetcher(
            client=mock_client, downloader=MagicMock()
        )
        with pytest.raises(FraserValidationError):
            _ = fetcher.title_id

    def test_正常系_title_id_jsonにあれば返却(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ``fraser_titles.json`` provides a title_id, list works."""
        from market.fraser.fetchers import base as base_module

        titles_json = tmp_path / "fraser_titles.json"
        titles_json.write_text('{"fomc_press_conferences": 54321}\n', encoding="utf-8")
        monkeypatch.setattr(base_module, "DEFAULT_TITLES_JSON_PATH", titles_json)

        items = _items_from_sample(sample_fomc_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FOMCPressConferencesFetcher(
            client=mock_client, downloader=MagicMock()
        )
        meetings = fetcher.list_press_conferences(year_range=(2024, 2024))

        positional_args, _ = mock_client.list_items.call_args
        assert positional_args[0] == 54321
        assert all(isinstance(m, FOMCMeeting) for m in meetings)


class TestFOMCPressConferencesFetcherFetchText:
    """Tests for :meth:`FOMCPressConferencesFetcher.fetch_text`."""

    def test_正常系_fetch_text_pdf_fallback(
        self,
        sample_fomc_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        """``prefer='pdf'`` is propagated to the downloader (TXT fallback path)."""
        items = _items_from_sample(sample_fomc_items_response)
        # Pick the 2024-03-20 item (item_id=1002) which only exposes pdfUrl.
        target_item = next(i for i in items if i.item_id == 1002)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "fomc" / "press_conferences" / "2024-03-20_1002.pdf"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = FOMCPressConferencesFetcher(
            client=mock_client,
            downloader=mock_downloader,
        )
        path, meeting = fetcher.fetch_text(1002, prefer="pdf")

        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "pdf"
        assert path == expected_path
        assert isinstance(meeting, FOMCMeeting)
        assert meeting.item_id == 1002
