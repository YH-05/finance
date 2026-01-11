"""Tests for market_analysis.utils.cache module."""

import time

import pandas as pd
import pytest

from market_analysis.types import CacheConfig
from market_analysis.utils.cache import (
    SQLiteCache,
    generate_cache_key,
    get_cache,
    reset_cache,
)


class TestGenerateCacheKey:
    """Tests for cache key generation."""

    def test_generates_consistent_key(self) -> None:
        """Test key generation is consistent."""
        key1 = generate_cache_key("AAPL", "2024-01-01", "2024-12-31")
        key2 = generate_cache_key("AAPL", "2024-01-01", "2024-12-31")
        assert key1 == key2

    def test_different_symbols_different_keys(self) -> None:
        """Test different symbols produce different keys."""
        key1 = generate_cache_key("AAPL", "2024-01-01", "2024-12-31")
        key2 = generate_cache_key("GOOGL", "2024-01-01", "2024-12-31")
        assert key1 != key2

    def test_key_length(self) -> None:
        """Test key is SHA256 hex (64 chars)."""
        key = generate_cache_key("AAPL")
        assert len(key) == 64


class TestSQLiteCache:
    """Tests for SQLiteCache class."""

    @pytest.fixture
    def cache(self) -> SQLiteCache:
        """Create a test cache instance."""
        config = CacheConfig(
            enabled=True,
            ttl_seconds=3600,
            max_entries=100,
            db_path=None,  # In-memory
        )
        return SQLiteCache(config)

    def test_get_missing_key_returns_none(self, cache: SQLiteCache) -> None:
        """Test get returns None for missing key."""
        assert cache.get("nonexistent") is None

    def test_set_and_get(self, cache: SQLiteCache) -> None:
        """Test basic set and get."""
        cache.set("key1", {"price": 150.0})
        result = cache.get("key1")
        assert result == {"price": 150.0}

    def test_set_and_get_list(self, cache: SQLiteCache) -> None:
        """Test set and get with list."""
        cache.set("key1", [1, 2, 3])
        result = cache.get("key1")
        assert result == [1, 2, 3]

    def test_set_and_get_dataframe(self, cache: SQLiteCache) -> None:
        """Test set and get with DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        cache.set("df_key", df)
        result = cache.get("df_key")
        pd.testing.assert_frame_equal(result, df)

    def test_ttl_expiration(self) -> None:
        """Test TTL expiration."""
        config = CacheConfig(ttl_seconds=1)  # 1 second TTL
        cache = SQLiteCache(config)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(1.1)  # Wait for expiration
        assert cache.get("key1") is None

    def test_delete(self, cache: SQLiteCache) -> None:
        """Test delete removes entry."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        deleted = cache.delete("key1")
        assert deleted is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self, cache: SQLiteCache) -> None:
        """Test delete returns False for nonexistent key."""
        deleted = cache.delete("nonexistent")
        assert deleted is False

    def test_clear(self, cache: SQLiteCache) -> None:
        """Test clear removes all entries."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear()
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self) -> None:
        """Test cleanup_expired removes only expired entries."""
        config = CacheConfig(ttl_seconds=1)
        cache = SQLiteCache(config)

        cache.set("key1", "value1")
        time.sleep(1.1)  # Let key1 expire
        cache.set("key2", "value2", ttl=3600)  # key2 has long TTL

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_max_entries_cleanup(self) -> None:
        """Test max entries triggers cleanup."""
        config = CacheConfig(max_entries=3)
        cache = SQLiteCache(config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should trigger cleanup

        stats = cache.get_stats()
        assert stats["total_entries"] <= 3

    def test_get_stats(self, cache: SQLiteCache) -> None:
        """Test get_stats returns correct info."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert "max_entries" in stats

    def test_context_manager(self) -> None:
        """Test cache works as context manager."""
        with SQLiteCache() as cache:
            cache.set("key", "value")
            assert cache.get("key") == "value"


class TestGlobalCache:
    """Tests for global cache functions."""

    def teardown_method(self) -> None:
        """Reset global cache after each test."""
        reset_cache()

    def test_get_cache_singleton(self) -> None:
        """Test get_cache returns same instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_reset_cache(self) -> None:
        """Test reset_cache creates new instance."""
        cache1 = get_cache()
        cache1.set("key", "value")

        reset_cache()
        cache2 = get_cache()

        assert cache1 is not cache2
        assert cache2.get("key") is None
