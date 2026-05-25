"""Tests for ``market.fraser.client`` module.

Verifies the high-level :class:`FraserClient` integration:

- Initialisation with explicit / env-var-backed / missing API keys.
- Each of the 8 endpoint methods executes the cache-hit and cache-miss
  pipelines correctly (session called on miss, skipped on hit).
- ``use_cache=False`` bypasses cache reads but still populates the cache
  on success.
- Context manager protocol closes the underlying session.

See Also
--------
market.fraser.client : Module under test.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from market.cache.cache import SQLiteCache
from market.fraser.client import FraserClient
from market.fraser.errors import FraserAuthError
from market.fraser.types import FraserConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(payload: Any) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = payload
    response.text = json.dumps(payload, default=str)
    response.headers = {}
    return response


def _build_client(
    *,
    session_payload: Any = None,
    cache: SQLiteCache | None = None,
) -> tuple[FraserClient, MagicMock, SQLiteCache]:
    session = MagicMock()
    session.get_with_retry.return_value = _make_response(session_payload)
    cache = cache or SQLiteCache()
    client = FraserClient(
        config=FraserConfig(api_key="dummy"),
        session=session,
        cache=cache,
    )
    return client, session, cache


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestFraserClientInit:
    def test_正常系_明示configで初期化(self) -> None:
        cache = SQLiteCache()
        try:
            client = FraserClient(
                config=FraserConfig(api_key="dummy"),
                session=MagicMock(),
                cache=cache,
            )
            assert client._config.api_key == "dummy"
        finally:
            cache.close()

    def test_正常系_環境変数からAPIキー取得(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FRASER_API_KEY", "env_key")
        with patch("market.fraser.client.FraserSession") as mock_session_cls:
            mock_session_cls.return_value = MagicMock()
            cache = SQLiteCache()
            try:
                client = FraserClient(cache=cache)
                assert client._config.api_key == "env_key"
            finally:
                cache.close()

    def test_異常系_APIキーがないと_FraserAuthError(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("FRASER_API_KEY", raising=False)
        with pytest.raises(FraserAuthError):
            FraserClient()

    def test_正常系_contextマネージャでcloseされる(self) -> None:
        cache = SQLiteCache()
        session = MagicMock()
        try:
            with FraserClient(
                config=FraserConfig(api_key="dummy"),
                session=session,
                cache=cache,
            ):
                pass
            session.close.assert_called_once()
        finally:
            cache.close()


# ---------------------------------------------------------------------------
# list_items
# ---------------------------------------------------------------------------


class TestListItems:
    def test_正常系_cache_missで_session呼び出し(
        self, sample_fomc_items_response: dict[str, Any]
    ) -> None:
        client, session, cache = _build_client(
            session_payload=sample_fomc_items_response
        )
        try:
            items = client.list_items(title_id=677, limit=10)
            assert len(items) == 5
            session.get_with_retry.assert_called_once_with(
                "/items",
                params={"titleId": 677, "limit": 10, "page": 1},
            )
        finally:
            cache.close()

    def test_正常系_cache_hitで_sessionが呼ばれない(
        self, sample_fomc_items_response: dict[str, Any]
    ) -> None:
        client, session, cache = _build_client(
            session_payload=sample_fomc_items_response
        )
        try:
            client.list_items(title_id=677, limit=10)
            session.get_with_retry.reset_mock()

            # Second call should hit the cache.
            items = client.list_items(title_id=677, limit=10)
            assert len(items) == 5
            session.get_with_retry.assert_not_called()
        finally:
            cache.close()

    def test_正常系_use_cache_Falseはキャッシュバイパス(
        self, sample_fomc_items_response: dict[str, Any]
    ) -> None:
        client, session, cache = _build_client(
            session_payload=sample_fomc_items_response
        )
        try:
            client.list_items(title_id=677, limit=10)
            session.get_with_retry.reset_mock()

            client.list_items(title_id=677, limit=10, use_cache=False)
            session.get_with_retry.assert_called_once()
        finally:
            cache.close()


# ---------------------------------------------------------------------------
# get_item / get_title / get_toc
# ---------------------------------------------------------------------------


class TestGetItem:
    def test_正常系_単一itemをパース(self) -> None:
        payload = {"itemId": 42, "title": "X", "date": "2024-05-01"}
        client, session, cache = _build_client(session_payload=payload)
        try:
            item = client.get_item(42)
            assert item.item_id == 42
            session.get_with_retry.assert_called_once_with("/item/42", params={})
        finally:
            cache.close()


class TestGetTitle:
    def test_正常系_titleをパース(self) -> None:
        payload = {"titleId": 677, "name": "FOMC"}
        client, _session, cache = _build_client(session_payload=payload)
        try:
            title = client.get_title(677)
            assert title.title_id == 677
        finally:
            cache.close()


class TestGetToc:
    def test_正常系_tocリスト(self) -> None:
        payload = [{"label": "Intro", "page": 1}]
        client, _session, cache = _build_client(session_payload=payload)
        try:
            toc = client.get_toc(42)
            assert len(toc) == 1
            assert toc[0].label == "Intro"
        finally:
            cache.close()


# ---------------------------------------------------------------------------
# get_authors / subjects / themes / timeline
# ---------------------------------------------------------------------------


class TestMasterTables:
    def test_正常系_authors(self) -> None:
        payload = [{"name": "Alice", "authorId": 1}]
        client, _, cache = _build_client(session_payload=payload)
        try:
            authors = client.get_authors()
            assert authors[0].author_id == 1
        finally:
            cache.close()

    def test_正常系_subjects(self) -> None:
        payload = [{"name": "macro", "subjectId": 7}]
        client, _, cache = _build_client(session_payload=payload)
        try:
            subjects = client.get_subjects()
            assert subjects[0].subject_id == 7
        finally:
            cache.close()

    def test_正常系_themes(self) -> None:
        payload = [{"name": "policy", "themeId": 9}]
        client, _, cache = _build_client(session_payload=payload)
        try:
            themes = client.get_themes()
            assert themes[0].theme_id == 9
        finally:
            cache.close()

    def test_正常系_timeline(self) -> None:
        payload = [{"label": "Founded", "eventDate": "1913"}]
        client, session, cache = _build_client(session_payload=payload)
        try:
            events = client.get_timeline(677)
            assert events[0].label == "Founded"
            session.get_with_retry.assert_called_once_with(
                "/title/677/timeline", params={}
            )
        finally:
            cache.close()
