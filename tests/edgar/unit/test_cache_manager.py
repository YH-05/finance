"""Unit tests for edgar.cache.manager module.

Tests for CacheManager class including save_text(), get_cached_text(),
and clear_expired() with SQLite-based caching and TTL expiration.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from edgar.cache.manager import DEFAULT_TTL_DAYS, CacheManager


class TestCacheManagerSaveAndGet:
    """Tests for CacheManager.save_text() and get_cached_text() methods."""

    def test_正常系_テキスト保存と取得(self, tmp_path: Path) -> None:
        """save_text/get_cached_text should store and retrieve text.

        Verify the basic round-trip: save text then retrieve it
        using the same filing_id.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Sample filing text")

        result = cache.get_cached_text("filing-001")
        assert result == "Sample filing text"

    def test_正常系_同じfiling_idで上書き保存(self, tmp_path: Path) -> None:
        """save_text should overwrite existing entries via UPSERT.

        Verify that saving with the same filing_id replaces the
        previous text content (INSERT OR REPLACE behavior).
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Original text")
        cache.save_text("filing-001", "Updated text")

        result = cache.get_cached_text("filing-001")
        assert result == "Updated text"

    def test_正常系_TTL期限内はキャッシュヒット(self, tmp_path: Path) -> None:
        """get_cached_text should return text within TTL.

        Verify that entries are returned when they have not expired.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=1)
        cache.save_text("filing-001", "Cached text")

        result = cache.get_cached_text("filing-001")
        assert result == "Cached text"

    def test_正常系_カスタムTTLで保存(self, tmp_path: Path) -> None:
        """save_text should accept custom ttl_days parameter.

        Verify that a custom TTL overrides the instance default
        and the entry remains accessible.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Custom TTL text", ttl_days=180)

        result = cache.get_cached_text("filing-001")
        assert result == "Custom TTL text"

    def test_正常系_複数エントリの独立した保存と取得(self, tmp_path: Path) -> None:
        """save_text/get_cached_text should handle multiple entries.

        Verify that different filing_ids store and retrieve
        independently without interference.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Text for filing 001")
        cache.save_text("filing-002", "Text for filing 002")

        assert cache.get_cached_text("filing-001") == "Text for filing 001"
        assert cache.get_cached_text("filing-002") == "Text for filing 002"

    def test_異常系_存在しないfiling_idでNone(self, tmp_path: Path) -> None:
        """get_cached_text should return None for nonexistent filing_id.

        Verify that querying a filing_id that was never saved
        returns None instead of raising an error.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        result = cache.get_cached_text("nonexistent-id")
        assert result is None

    def test_異常系_TTL期限切れでNone(self, tmp_path: Path) -> None:
        """get_cached_text should return None for expired entries.

        Verify that entries past their TTL expiration are treated
        as cache misses and deleted on access.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Expired text")

        # Force expiration by directly updating expires_at in the DB
        conn = sqlite3.connect(str(cache.db_path))
        conn.execute(
            "UPDATE edgar_cache SET expires_at = ? WHERE filing_id = ?",
            (int(time.time()) - 1, "filing-001"),
        )
        conn.commit()
        conn.close()

        result = cache.get_cached_text("filing-001")
        assert result is None

    def test_異常系_TTL期限切れエントリはアクセス時に削除される(
        self, tmp_path: Path
    ) -> None:
        """get_cached_text should delete expired entries on access.

        Verify that after accessing an expired entry, it is removed
        from the database entirely.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Expired text")

        # Force expiration
        conn = sqlite3.connect(str(cache.db_path))
        conn.execute(
            "UPDATE edgar_cache SET expires_at = ? WHERE filing_id = ?",
            (int(time.time()) - 1, "filing-001"),
        )
        conn.commit()
        conn.close()

        # Access triggers deletion
        cache.get_cached_text("filing-001")

        # Verify entry was deleted from DB
        conn = sqlite3.connect(str(cache.db_path))
        cursor = conn.execute(
            "SELECT COUNT(*) FROM edgar_cache WHERE filing_id = ?",
            ("filing-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 0

    def test_エッジケース_空テキストの保存と取得(self, tmp_path: Path) -> None:
        """save_text/get_cached_text should handle empty text.

        Verify that an empty string can be saved and retrieved
        without being confused with a cache miss (None).
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "")

        result = cache.get_cached_text("filing-001")
        assert result == ""


class TestCacheManagerClearExpired:
    """Tests for CacheManager.clear_expired() method."""

    def test_正常系_clear_expiredで期限切れ削除(self, tmp_path: Path) -> None:
        """clear_expired should remove expired entries and return count.

        Verify that clear_expired() deletes all expired entries
        and returns the number of removed entries.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Text 1")
        cache.save_text("filing-002", "Text 2")

        # Force expiration for filing-001 only
        conn = sqlite3.connect(str(cache.db_path))
        conn.execute(
            "UPDATE edgar_cache SET expires_at = ? WHERE filing_id = ?",
            (int(time.time()) - 1, "filing-001"),
        )
        conn.commit()
        conn.close()

        removed = cache.clear_expired()
        assert removed == 1
        assert cache.get_cached_text("filing-001") is None
        assert cache.get_cached_text("filing-002") == "Text 2"

    def test_正常系_clear_expiredで期限切れなしなら0(self, tmp_path: Path) -> None:
        """clear_expired should return 0 when no entries are expired.

        Verify that clear_expired() returns 0 and does not delete
        any entries when all entries are still valid.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        cache.save_text("filing-001", "Valid text")

        removed = cache.clear_expired()
        assert removed == 0
        assert cache.get_cached_text("filing-001") == "Valid text"

    def test_エッジケース_空のキャッシュでclear_expired(self, tmp_path: Path) -> None:
        """clear_expired should return 0 for empty cache.

        Verify that clear_expired() handles an empty database
        without errors.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        removed = cache.clear_expired()
        assert removed == 0


class TestCacheManagerInit:
    """Tests for CacheManager initialization."""

    def test_正常系_DBファイルパス確認(self, tmp_path: Path) -> None:
        """CacheManager should create db file in cache_dir.

        Verify that the SQLite database file is created at the
        expected path within the cache directory.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        assert cache.db_path == tmp_path / "edgar_cache.db"
        assert cache.db_path.exists()

    def test_正常系_デフォルトTTL確認(self, tmp_path: Path) -> None:
        """CacheManager should use default TTL of 90 days.

        Verify that the default ttl_days matches DEFAULT_TTL_DAYS.
        """
        cache = CacheManager(cache_dir=tmp_path)
        assert cache.ttl_days == DEFAULT_TTL_DAYS
        assert cache.ttl_days == 90

    def test_正常系_cache_dirが自動作成される(self, tmp_path: Path) -> None:
        """CacheManager should create cache_dir if it does not exist.

        Verify that the constructor creates the cache directory
        and any necessary parent directories.
        """
        nested_dir = tmp_path / "a" / "b" / "c"
        cache = CacheManager(cache_dir=nested_dir, ttl_days=90)
        assert nested_dir.exists()
        assert cache.db_path.exists()

    def test_正常系_DBスキーマが正しく作成される(self, tmp_path: Path) -> None:
        """CacheManager should create the edgar_cache table with correct schema.

        Verify that the database table has the expected columns:
        filing_id (TEXT PK), text (TEXT), cached_at (INT), expires_at (INT).
        """
        CacheManager(cache_dir=tmp_path, ttl_days=90)

        conn = sqlite3.connect(str(tmp_path / "edgar_cache.db"))
        cursor = conn.execute("PRAGMA table_info(edgar_cache)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert "filing_id" in columns
        assert "text" in columns
        assert "cached_at" in columns
        assert "expires_at" in columns


class TestCacheManagerConcurrency:
    """Tests for CacheManager thread safety."""

    def test_エッジケース_並行アクセスでスレッドセーフ(self, tmp_path: Path) -> None:
        """CacheManager should be thread-safe for concurrent writes.

        Verify that concurrent save_text() calls from multiple threads
        do not corrupt the database or raise errors.
        """
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        errors: list[Exception] = []

        def save_entry(filing_id: str, text: str) -> None:
            try:
                cache.save_text(filing_id, text)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=save_entry, args=(f"filing-{i:03d}", f"Text {i}"))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # Verify all entries were saved
        for i in range(10):
            result = cache.get_cached_text(f"filing-{i:03d}")
            assert result == f"Text {i}"
