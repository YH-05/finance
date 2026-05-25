"""Unit tests for ``market.fraser.fetchers.speeches.FRBSpeechFetcher``.

Covers:

- ``doc_type`` reports :data:`DocType.FRB_SPEECHES`.
- ``list_speeches`` filters by year and returns ``FRBSpeech`` instances.
- ``list_speeches(speaker=None)`` returns all year-matching speeches.
- ``list_speeches(speaker='Powell')`` filters by author name
  (case-insensitive: Powell == powell == POWELL).
- Historical (1980) speeches are reachable when ``year_range`` includes
  the historical archive.
- ``fetch_text`` narrows the return tuple to :class:`FRBSpeech`.

See Also
--------
market.fraser.fetchers.speeches : Class under test.
tests.market.fraser.conftest : Shared fixtures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from market.fraser.fetchers.speeches import FRBSpeechFetcher
from market.fraser.models import FraserItem, FRBSpeech
from market.fraser.types import DocType

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

_FRB_SPEECHES_TITLE_ID: int = 55555


@pytest.fixture
def frb_speeches_title_id(monkeypatch: pytest.MonkeyPatch) -> int:
    """Inject a dummy title_id for ``frb_speeches`` into KNOWN_TITLE_IDS."""
    from market.fraser.fetchers import base as base_module

    monkeypatch.setitem(
        base_module.KNOWN_TITLE_IDS, "frb_speeches", _FRB_SPEECHES_TITLE_ID
    )
    return _FRB_SPEECHES_TITLE_ID


def _items_from_sample(payload: dict[str, object]) -> list[FraserItem]:
    raw_items = payload["items"]
    assert isinstance(raw_items, list)
    return [FraserItem.model_validate(raw) for raw in raw_items]


# ---------------------------------------------------------------------------
# doc_type
# ---------------------------------------------------------------------------


class TestDocType:
    def test_正常系_doc_typeはFRB_SPEECHES(self) -> None:
        fetcher = FRBSpeechFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.doc_type is DocType.FRB_SPEECHES


# ---------------------------------------------------------------------------
# list_speeches (no speaker filter)
# ---------------------------------------------------------------------------


class TestListSpeechesNoFilter:
    def test_正常系_speakerNoneで2024年全件返却(
        self,
        sample_speech_items_response: dict[str, object],
        frb_speeches_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_speech_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FRBSpeechFetcher(client=mock_client, downloader=MagicMock())
        speeches = fetcher.list_speeches(year_range=(2024, 2024))

        assert all(isinstance(s, FRBSpeech) for s in speeches)
        # Fixture has 4 speeches dated in 2024 (3001, 3002, 3003, 3005).
        assert len(speeches) == 4
        assert all(s.date.year == 2024 for s in speeches)


# ---------------------------------------------------------------------------
# list_speeches (speaker filter)
# ---------------------------------------------------------------------------


class TestListSpeechesSpeakerFilter:
    def test_正常系_speakerPowell大文字小文字区別なし(
        self,
        sample_speech_items_response: dict[str, object],
        frb_speeches_title_id: int,
    ) -> None:
        """Speaker filtering is case-insensitive (Powell == powell == POWELL)."""
        items = _items_from_sample(sample_speech_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FRBSpeechFetcher(client=mock_client, downloader=MagicMock())

        # Three variants must all return the same Powell speech ids.
        ids_capital = {
            s.item_id for s in fetcher.list_speeches((2024, 2024), speaker="Powell")
        }
        ids_lower = {
            s.item_id for s in fetcher.list_speeches((2024, 2024), speaker="powell")
        }
        ids_upper = {
            s.item_id for s in fetcher.list_speeches((2024, 2024), speaker="POWELL")
        }

        assert ids_capital == ids_lower == ids_upper
        # 3001 + 3002 are Powell authors; 3005 mentions Powell in description.
        assert ids_capital == {3001, 3002, 3005}

    def test_正常系_speakerCook単一マッチ(
        self,
        sample_speech_items_response: dict[str, object],
        frb_speeches_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_speech_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FRBSpeechFetcher(client=mock_client, downloader=MagicMock())
        cook_speeches = fetcher.list_speeches((2024, 2024), speaker="Cook")

        assert len(cook_speeches) == 1
        assert cook_speeches[0].item_id == 3003

    def test_正常系_speaker未マッチで空リスト(
        self,
        sample_speech_items_response: dict[str, object],
        frb_speeches_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_speech_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FRBSpeechFetcher(client=mock_client, downloader=MagicMock())
        assert fetcher.list_speeches((2024, 2024), speaker="Bernanke") == []

    def test_正常系_歴史アーカイブVolcker1980年取得(
        self,
        sample_speech_items_response: dict[str, object],
        frb_speeches_title_id: int,
    ) -> None:
        """Speaker filter works on historical archive (1970s-1980s)."""
        items = _items_from_sample(sample_speech_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = FRBSpeechFetcher(client=mock_client, downloader=MagicMock())
        volcker = fetcher.list_speeches((1970, 1985), speaker="Volcker")

        assert len(volcker) == 1
        assert volcker[0].item_id == 3004
        assert volcker[0].date.year == 1980


# ---------------------------------------------------------------------------
# _to_frb_speech
# ---------------------------------------------------------------------------


class TestToFrbSpeech:
    def test_正常系_FraserItemからFRBSpeechへ変換(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 42,
                "title": "Speech",
                "date": "2024-01-01",
            }
        )
        fetcher = FRBSpeechFetcher(client=MagicMock(), downloader=MagicMock())
        speech = fetcher._to_frb_speech(item)
        assert isinstance(speech, FRBSpeech)
        assert speech.item_id == 42

    def test_正常系_FRBSpeech入力はそのまま返却(self) -> None:
        speech = FRBSpeech.model_validate(
            {
                "itemId": 7,
                "title": "x",
                "date": "2024-01-01",
                "speaker": "Powell",
            }
        )
        fetcher = FRBSpeechFetcher(client=MagicMock(), downloader=MagicMock())
        result = fetcher._to_frb_speech(speech)
        assert result is speech
        assert result.speaker == "Powell"


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


class TestFetchText:
    def test_正常系_fetch_textでFRBSpeechが返る(
        self,
        sample_speech_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_speech_items_response)
        target_item = next(i for i in items if i.item_id == 3001)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "speeches" / "2024-02-07_3001.txt"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = FRBSpeechFetcher(
            client=mock_client,
            downloader=mock_downloader,
        )
        path, speech = fetcher.fetch_text(3001, prefer="txt")

        assert path == expected_path
        assert isinstance(speech, FRBSpeech)
        assert speech.item_id == 3001
