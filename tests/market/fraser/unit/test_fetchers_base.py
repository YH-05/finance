"""Unit tests for ``market.fraser.fetchers.base.BaseFraserFetcher``.

These tests cover the abstract base class behaviour:

- ``_resolve_title_id`` priority: ``KNOWN_TITLE_IDS`` hit, JSON fallback,
  validation error when neither source provides a value.
- ``_filter_by_year_range`` boundary handling for ``YYYY-MM-DD`` /
  ``YYYY-MM`` / ``YYYY`` style ``date`` strings.
- ``fetch_text`` delegation to the downloader (with mocked dependencies).

A minimal :class:`_DummyFetcher` subclass is used to instantiate the
abstract base because :class:`BaseFraserFetcher` itself cannot be
instantiated directly.

See Also
--------
market.fraser.fetchers.base : Class under test.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from market.fraser.errors import FraserValidationError
from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import FraserItem
from market.fraser.types import DocType

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


class _DummyFetcher(BaseFraserFetcher):
    """Concrete subclass used solely for exercising the abstract base."""

    _doc_type_override: DocType = DocType.FOMC_MINUTES

    @property
    def doc_type(self) -> DocType:
        return self._doc_type_override


def _make_item(item_id: int, date_str: str) -> FraserItem:
    """Build a minimal ``FraserItem`` with the supplied ``date`` string."""
    return FraserItem.model_validate(
        {
            "itemId": item_id,
            "title": f"Item {item_id}",
            "date": date_str,
        }
    )


# ---------------------------------------------------------------------------
# _resolve_title_id
# ---------------------------------------------------------------------------


class TestResolveTitleId:
    """Tests for :meth:`BaseFraserFetcher._resolve_title_id`."""

    def test_正常系_known_title_idsに値があれば即返却(self) -> None:
        # FOMC_MINUTES is hard-coded as 677 in ``KNOWN_TITLE_IDS``.
        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.title_id == 677

    def test_正常系_known_title_idsがNoneでもjsonに値があれば返却(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Override KNOWN_TITLE_IDS so that the FOMC_MINUTES entry is None,
        # forcing the JSON fallback to be exercised.
        from market.fraser.fetchers import base as base_module

        monkeypatch.setattr(
            base_module,
            "KNOWN_TITLE_IDS",
            {"fomc_minutes": None},
        )

        # Write a fallback titles JSON file pointing at id 999.
        titles_file = tmp_path / "fraser_titles.json"
        titles_file.write_text(json.dumps({"fomc_minutes": 999}))
        monkeypatch.setattr(base_module, "DEFAULT_TITLES_JSON_PATH", titles_file)

        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher.title_id == 999

    def test_異常系_両方Noneで_FraserValidationError(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from market.fraser.fetchers import base as base_module

        monkeypatch.setattr(
            base_module,
            "KNOWN_TITLE_IDS",
            {"fomc_minutes": None},
        )

        # Point fallback path at a non-existent file so the JSON branch fails.
        monkeypatch.setattr(
            base_module,
            "DEFAULT_TITLES_JSON_PATH",
            tmp_path / "missing.json",
        )

        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        with pytest.raises(FraserValidationError) as excinfo:
            _ = fetcher.title_id
        assert excinfo.value.field == "title_id"


# ---------------------------------------------------------------------------
# _filter_by_year_range
# ---------------------------------------------------------------------------


class TestFilterByYearRange:
    """Boundary tests for :meth:`BaseFraserFetcher._filter_by_year_range`."""

    def test_正常系_範囲内のitemのみ返却される(self) -> None:
        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        items = [
            _make_item(1, "2023-12-31"),
            _make_item(2, "2024-01-01"),
            _make_item(3, "2024-06-15"),
            _make_item(4, "2024-12-31"),
            _make_item(5, "2025-01-01"),
        ]
        result = fetcher._filter_by_year_range(items, (2024, 2024))
        assert [i.item_id for i in result] == [2, 3, 4]

    def test_エッジケース_空リストで空結果(self) -> None:
        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher._filter_by_year_range([], (2024, 2024)) == []

    def test_正常系_年のみのdate文字列でも正しく動作(self) -> None:
        # ``_coerce_date`` normalises ``"2024"`` to ``date(2024, 1, 1)``.
        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        items = [_make_item(1, "2024"), _make_item(2, "2023")]
        result = fetcher._filter_by_year_range(items, (2024, 2024))
        assert [i.item_id for i in result] == [1]


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


class TestFetchText:
    """Tests for :meth:`BaseFraserFetcher.fetch_text` delegation."""

    def test_正常系_clientとdownloaderが呼ばれてtupleが返る(
        self, tmp_path: Path
    ) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 42,
                "title": "Test",
                "date": "2024-03-20",
                "location": {
                    "textUrl": ["https://example.org/42.txt"],
                },
            }
        )

        mock_client = MagicMock()
        mock_client.get_item.return_value = item

        mock_downloader = MagicMock()
        asset_path = tmp_path / "asset.txt"
        meta_path = tmp_path / "asset.meta.json"
        mock_downloader.download_with_meta.return_value = (asset_path, meta_path)

        fetcher = _DummyFetcher(client=mock_client, downloader=mock_downloader)
        result_path, result_item = fetcher.fetch_text(42, prefer="txt")

        mock_client.get_item.assert_called_once_with(42)
        mock_downloader.download_with_meta.assert_called_once_with(
            item, "fomc/minutes", prefer="txt"
        )
        assert result_path == asset_path
        assert result_item is item

    def test_正常系_fetch_pdfがprefer_pdfで委譲される(self, tmp_path: Path) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 43,
                "title": "Test PDF",
                "date": "2024-03-20",
                "location": {"pdfUrl": ["https://example.org/43.pdf"]},
            }
        )

        mock_client = MagicMock()
        mock_client.get_item.return_value = item

        mock_downloader = MagicMock()
        mock_downloader.download_with_meta.return_value = (
            tmp_path / "x.pdf",
            tmp_path / "x.meta.json",
        )

        fetcher = _DummyFetcher(client=mock_client, downloader=mock_downloader)
        fetcher.fetch_pdf(43)

        # ``fetch_pdf`` is a thin wrapper that forces ``prefer='pdf'``.
        _, kwargs = mock_downloader.download_with_meta.call_args
        assert kwargs["prefer"] == "pdf"


# ---------------------------------------------------------------------------
# Dependency injection defaults
# ---------------------------------------------------------------------------


class TestDefaultDependencies:
    """Tests covering the dependency-injection defaults of ``__init__``."""

    def test_正常系_クライアントもダウンローダもデフォルト生成される(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When called with no arguments both dependencies are auto-built."""
        from market.fraser.fetchers import base as base_module

        sentinel_session = MagicMock(name="default-session")
        sentinel_client = MagicMock(name="default-client")
        # Default downloader construction now goes through the public
        # ``client.session`` property (DIP-compliant), so wire the mock
        # accordingly.
        sentinel_client.session = sentinel_session
        sentinel_downloader = MagicMock(name="default-downloader")

        monkeypatch.setattr(base_module, "FraserClient", lambda: sentinel_client)

        captured_kwargs: dict[str, object] = {}

        def _fake_downloader(*, session: object, base_dir: Path) -> object:
            captured_kwargs["session"] = session
            captured_kwargs["base_dir"] = base_dir
            return sentinel_downloader

        monkeypatch.setattr(base_module, "FraserDownloader", _fake_downloader)

        fetcher = _DummyFetcher(base_dir=tmp_path)

        assert fetcher._client is sentinel_client
        assert fetcher._downloader is sentinel_downloader
        assert captured_kwargs["session"] is sentinel_session
        assert captured_kwargs["base_dir"] == tmp_path

    def test_正常系_doc_subdir_FOMC_MINUTES_returns_fomc_minutes(
        self,
    ) -> None:
        fetcher = _DummyFetcher(client=MagicMock(), downloader=MagicMock())
        assert fetcher._doc_subdir() == "fomc/minutes"
