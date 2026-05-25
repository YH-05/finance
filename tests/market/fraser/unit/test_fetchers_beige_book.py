"""Unit tests for ``market.fraser.fetchers.beige_book.BeigeBookFetcher``.

Covers:

- ``doc_type`` reports :data:`DocType.BEIGE_BOOK`.
- ``list_reports`` filters by year and returns ``BeigeBookReport``.
- ``fetch_all`` parallelises via ``ThreadPoolExecutor`` and tolerates
  partial failures (returns ``{item_id: Path | Exception}``).
- ``MAX_WORKERS_LIMIT`` clamps oversized ``max_workers``.
- ``fetch_all`` with ``max_workers < 1`` raises :class:`ValueError`.

See Also
--------
market.fraser.fetchers.beige_book : Class under test.
tests.market.fraser.conftest : Shared fixtures.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from market.fraser.fetchers.beige_book import (
    MAX_WORKERS_LIMIT,
    BeigeBookFetcher,
)
from market.fraser.models import BeigeBookReport, FraserItem
from market.fraser.types import DocType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Title id slot for "beige_book" must be present in KNOWN_TITLE_IDS for the
# fetcher's ``title_id`` property to resolve. We monkeypatch the constant
# directly via a fixture below — keeping the conftest unchanged.
_BEIGE_BOOK_TITLE_ID: int = 77777


@pytest.fixture
def beige_book_title_id(monkeypatch: pytest.MonkeyPatch) -> int:
    """Inject a dummy title_id for ``beige_book`` into KNOWN_TITLE_IDS."""
    from market.fraser.fetchers import base as base_module

    monkeypatch.setitem(base_module.KNOWN_TITLE_IDS, "beige_book", _BEIGE_BOOK_TITLE_ID)
    return _BEIGE_BOOK_TITLE_ID


def _items_from_sample(
    payload: dict[str, object],
) -> list[FraserItem]:
    """Convert the ``sample_beige_book_items_response`` fixture into models."""
    raw_items = payload["items"]
    assert isinstance(raw_items, list)
    return [FraserItem.model_validate(raw) for raw in raw_items]


# ---------------------------------------------------------------------------
# doc_type
# ---------------------------------------------------------------------------


class TestDocType:
    def test_正常系_doc_typeはBEIGE_BOOK(self) -> None:
        fetcher = BeigeBookFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.doc_type is DocType.BEIGE_BOOK


# ---------------------------------------------------------------------------
# list_reports
# ---------------------------------------------------------------------------


class TestListReports:
    def test_正常系_2023_2024年指定で4件取得(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())
        reports = fetcher.list_reports(year_range=(2023, 2024))

        assert all(isinstance(r, BeigeBookReport) for r in reports)
        years = sorted({r.date.year for r in reports})
        assert years == [2023, 2024]
        # Fixture contains 2 items in 2023, 2 in 2024, and 1 in 1995.
        assert len(reports) == 4

    def test_正常系_client_list_itemsがtitle_idで呼ばれる(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())
        fetcher.list_reports(year_range=(2023, 2024), limit=50)

        mock_client.list_items.assert_called_once()
        positional_args, kwargs = mock_client.list_items.call_args
        assert positional_args[0] == _BEIGE_BOOK_TITLE_ID
        assert kwargs.get("limit", 50) == 50


# ---------------------------------------------------------------------------
# _convert_to (shared helper replacing the legacy ``_to_beige_book_report``)
# ---------------------------------------------------------------------------


class TestConvertToBeigeBookReport:
    """Exercises :meth:`BaseFraserFetcher._convert_to` for BeigeBookReport.

    The legacy ``_to_beige_book_report`` per-fetcher helper was removed
    in PR #3967 in favour of the shared ``_convert_to`` static helper.
    Unlike the deleted helper, ``_convert_to`` always re-validates and
    therefore returns a fresh instance even when the input already
    matches the target type — the equality assertion below replaces the
    previous identity check.
    """

    def test_正常系_FraserItemからBeigeBookReportへ変換(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 1,
                "titleId": 1234,
                "title": "Beige Book January 2024",
                "date": "2024-01-17",
            }
        )
        fetcher = BeigeBookFetcher(client=MagicMock(), downloader=MagicMock())
        report = fetcher._convert_to(item, BeigeBookReport)
        assert isinstance(report, BeigeBookReport)
        assert report.item_id == 1
        assert report.date.isoformat() == "2024-01-17"

    def test_正常系_BeigeBookReport入力でもdistrict保持(self) -> None:
        """``_convert_to`` re-validates so ``district`` survives the round-trip.

        The previous behaviour returned the same instance via ``isinstance``
        short-circuit; ``_convert_to`` always builds a new model, so we
        assert equality on the carried-over field instead of identity.
        """
        report = BeigeBookReport.model_validate(
            {
                "itemId": 9,
                "title": "x",
                "date": "2024-01-01",
                "district": "Boston",
            }
        )
        fetcher = BeigeBookFetcher(client=MagicMock(), downloader=MagicMock())
        result = fetcher._convert_to(report, BeigeBookReport)
        assert isinstance(result, BeigeBookReport)
        assert result.district == "Boston"


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


class TestFetchText:
    def test_正常系_fetch_textでBeigeBookReportが返る(
        self,
        sample_beige_book_items_response: dict[str, object],
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        target_item = next(i for i in items if i.item_id == 2003)

        mock_client = MagicMock()
        mock_client.get_item.return_value = target_item

        expected_path = tmp_path / "beige_book" / "2024-03-06_2003.txt"
        expected_meta = expected_path.with_suffix(".meta.json")
        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            expected_path,
            expected_meta,
        )

        fetcher = BeigeBookFetcher(
            client=mock_client,
            downloader=mock_downloader,
        )
        path, report = fetcher.fetch_text(2003, prefer="txt")

        assert path == expected_path
        assert isinstance(report, BeigeBookReport)
        assert report.item_id == 2003


# ---------------------------------------------------------------------------
# fetch_all
# ---------------------------------------------------------------------------


class TestFetchAll:
    def test_正常系_fetch_all並列DLでdict返却(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
        tmp_path: Path,
    ) -> None:
        """``fetch_all`` returns dict[item_id, Path] when every download succeeds."""
        items = _items_from_sample(sample_beige_book_items_response)
        target_items = [i for i in items if i.date.year in (2023, 2024)]
        assert len(target_items) == 4

        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        # ``fetch_text`` is bypassed by patching ``_fetch_text_path`` directly
        # so we don't have to wire up the downloader for each per-item call.
        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())

        def _fake_fetch(item_id: int, prefer: str) -> Path:
            return tmp_path / f"beige_book_{item_id}.{prefer}"

        with patch.object(
            fetcher, "_fetch_text_path", side_effect=_fake_fetch
        ) as patched:
            results = fetcher.fetch_all((2023, 2024), max_workers=4)

        assert set(results.keys()) == {i.item_id for i in target_items}
        for item_id, outcome in results.items():
            assert isinstance(outcome, Path)
            assert outcome == tmp_path / f"beige_book_{item_id}.txt"
        # _fetch_text_path was invoked once per target item.
        assert patched.call_count == len(target_items)

    def test_正常系_fetch_all_max_workersクランプ(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
        tmp_path: Path,
    ) -> None:
        """``max_workers`` above ``MAX_WORKERS_LIMIT`` is silently clamped."""
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())

        captured: dict[str, object] = {}

        class _RecordingExecutor(ThreadPoolExecutor):
            def __init__(self, max_workers: int, **_kwargs: object) -> None:
                captured["max_workers"] = max_workers
                super().__init__(max_workers=max_workers)

        with (
            patch.object(
                fetcher,
                "_fetch_text_path",
                side_effect=lambda item_id, prefer: tmp_path / f"{item_id}.txt",
            ),
            patch(
                "market.fraser.fetchers.beige_book.ThreadPoolExecutor",
                _RecordingExecutor,
            ),
        ):
            fetcher.fetch_all((2023, 2024), max_workers=100)

        assert captured["max_workers"] == MAX_WORKERS_LIMIT

    def test_異常系_max_workersが0以下でValueError(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items
        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())

        with pytest.raises(ValueError, match="max_workers must be >= 1"):
            fetcher.fetch_all((2023, 2024), max_workers=0)

    def test_正常系_fetch_all部分障害をException値で保持(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
        tmp_path: Path,
    ) -> None:
        """A failing future is captured in the result dict as an Exception value."""
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())

        failing_id = 2003

        def _fake_fetch(item_id: int, prefer: str) -> Path:
            if item_id == failing_id:
                raise RuntimeError(f"injected failure for {item_id}")
            return tmp_path / f"beige_book_{item_id}.{prefer}"

        with patch.object(fetcher, "_fetch_text_path", side_effect=_fake_fetch):
            results = fetcher.fetch_all((2023, 2024), max_workers=2)

        assert failing_id in results
        assert isinstance(results[failing_id], RuntimeError)
        assert "injected failure" in str(results[failing_id])

        # All other items still produced Path values.
        for item_id, outcome in results.items():
            if item_id == failing_id:
                continue
            assert isinstance(outcome, Path)

    def test_正常系_fetch_all範囲外空結果(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())
        # Range with no items in fixture (fixture covers 1995, 2023, 2024).
        results = fetcher.fetch_all((1900, 1950), max_workers=4)
        assert results == {}

    def test_正常系_fetch_all_preferがfetch_textへ伝搬(
        self,
        sample_beige_book_items_response: dict[str, object],
        beige_book_title_id: int,
        tmp_path: Path,
    ) -> None:
        items = _items_from_sample(sample_beige_book_items_response)
        mock_client = MagicMock()
        mock_client.list_items.return_value = items

        fetcher = BeigeBookFetcher(client=mock_client, downloader=MagicMock())
        observed: list[str] = []

        def _fake_fetch(item_id: int, prefer: str) -> Path:
            observed.append(prefer)
            return tmp_path / f"{item_id}.{prefer}"

        with patch.object(fetcher, "_fetch_text_path", side_effect=_fake_fetch):
            fetcher.fetch_all((2024, 2024), max_workers=2, prefer="pdf")

        assert set(observed) == {"pdf"}, (
            "fetch_all did not propagate prefer to _fetch_text_path"
        )
