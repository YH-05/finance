"""Tests for ``market.fraser.cache`` module.

Verifies TTL constants, the :func:`get_fraser_cache` factory,
:func:`make_fraser_cache_key` (SHA-256 based key construction with
collision avoidance), and that ``cache.py`` does **not** define its own
``SQLiteCache`` subclass (HF1 confirmation).

See Also
--------
market.fraser.cache : Module under test.
market.alphavantage.cache : Reference implementation pattern.
market.cache.cache : Shared ``SQLiteCache`` base.
"""

from __future__ import annotations

import inspect

import market.fraser.cache as cache_module
from market.cache.cache import SQLiteCache
from market.fraser.cache import (
    AUTHOR_SUBJECT_THEME_TTL,
    ITEM_METADATA_TTL,
    ITEMS_LIST_TTL,
    TIMELINE_TTL,
    TITLE_METADATA_TTL,
    get_fraser_cache,
    make_fraser_cache_key,
)


class TestTTLConstants:
    """Verify each FRASER TTL constant has the documented value."""

    def test_正常系_TITLE_METADATA_TTLが30日(self) -> None:
        assert TITLE_METADATA_TTL == 2592000

    def test_正常系_ITEMS_LIST_TTLが7日(self) -> None:
        assert ITEMS_LIST_TTL == 604800

    def test_正常系_ITEM_METADATA_TTLが30日(self) -> None:
        assert ITEM_METADATA_TTL == 2592000

    def test_正常系_AUTHOR_SUBJECT_THEME_TTLが30日(self) -> None:
        assert AUTHOR_SUBJECT_THEME_TTL == 2592000

    def test_正常系_TIMELINE_TTLが7日(self) -> None:
        assert TIMELINE_TTL == 604800

    def test_正常系_全TTL定数が正の整数(self) -> None:
        ttl_values = [
            TITLE_METADATA_TTL,
            ITEMS_LIST_TTL,
            ITEM_METADATA_TTL,
            AUTHOR_SUBJECT_THEME_TTL,
            TIMELINE_TTL,
        ]
        for ttl in ttl_values:
            assert isinstance(ttl, int)
            assert ttl > 0


class TestGetFraserCache:
    """Verify :func:`get_fraser_cache` returns a configured SQLiteCache."""

    def test_正常系_返り値がSQLiteCacheインスタンス(self) -> None:
        cache = get_fraser_cache()
        try:
            assert isinstance(cache, SQLiteCache)
        finally:
            cache.close()

    def test_正常系_キャッシュが有効化されている(self) -> None:
        cache = get_fraser_cache()
        try:
            assert cache.config.enabled is True
        finally:
            cache.close()

    def test_正常系_デフォルトTTLがITEM_METADATA_TTL(self) -> None:
        cache = get_fraser_cache()
        try:
            assert cache.config.ttl_seconds == ITEM_METADATA_TTL
        finally:
            cache.close()

    def test_正常系_ttl引数を渡すと反映される(self) -> None:
        cache = get_fraser_cache(ttl=600)
        try:
            assert cache.config.ttl_seconds == 600
        finally:
            cache.close()

    def test_正常系_max_entriesが10000(self) -> None:
        cache = get_fraser_cache()
        try:
            assert cache.config.max_entries == 10000
        finally:
            cache.close()


class TestMakeFraserCacheKey:
    """Verify :func:`make_fraser_cache_key` builds collision-safe keys."""

    def test_正常系_fraserプレフィックス付き(self) -> None:
        key = make_fraser_cache_key("/items", {"titleId": 677})
        assert key.startswith("fraser:")

    def test_正常系_SHA256ダイジェスト長(self) -> None:
        key = make_fraser_cache_key("/items", {"titleId": 677})
        # ``"fraser:"`` (7) + SHA-256 hex (64) == 71 chars total.
        assert len(key) == 7 + 64

    def test_正常系_paramsの順序差で同じキー(self) -> None:
        key_a = make_fraser_cache_key("/items", {"titleId": 677, "limit": 10})
        key_b = make_fraser_cache_key("/items", {"limit": 10, "titleId": 677})
        assert key_a == key_b

    def test_正常系_endpoint違いで別キー(self) -> None:
        key_a = make_fraser_cache_key("/items", {"titleId": 677})
        key_b = make_fraser_cache_key("/title/677", {})
        assert key_a != key_b

    def test_正常系_params違いで別キー(self) -> None:
        key_a = make_fraser_cache_key("/items", {"titleId": 677})
        key_b = make_fraser_cache_key("/items", {"titleId": 678})
        assert key_a != key_b

    def test_正常系_空paramsでもキー生成(self) -> None:
        key = make_fraser_cache_key("/authors", {})
        assert key.startswith("fraser:")
        assert len(key) == 7 + 64


class TestNoOwnSQLiteCache:
    """HF1: ``cache.py`` must reuse ``SQLiteCache``, not subclass it."""

    def test_正常系_FraserSQLiteCacheクラスが存在しない(self) -> None:
        # The module must not define its own SQLiteCache subclass.
        assert not hasattr(cache_module, "FraserSQLiteCache")

    def test_正常系_モジュール内にSQLiteCache継承クラスがない(self) -> None:
        for _, obj in inspect.getmembers(cache_module, inspect.isclass):
            if obj is SQLiteCache:
                continue
            assert not issubclass(obj, SQLiteCache), (
                f"{obj.__name__} unexpectedly subclasses SQLiteCache"
            )
