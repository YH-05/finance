"""Unit tests for Cache class.

Tests for providers/cache.py based on Issue #115 acceptance criteria:
1. Generate file path from cache key
2. TTL (Time To Live) based cache invalidation
3. Save/load data in Parquet format
4. Auto-create cache directory if not exists
"""

import os
import time
from pathlib import Path

import pandas as pd
import pytest

from factor.providers.cache import Cache
from factor.utils.logging_config import get_logger

logger = get_logger(__name__)


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in tmp_path fixture

    Returns
    -------
    Path
        Temporary directory path for cache
    """
    return tmp_path / "cache"


@pytest.fixture
def cache(cache_dir: Path) -> Cache:
    """Create a Cache instance for testing.

    Parameters
    ----------
    cache_dir : Path
        Temporary cache directory path

    Returns
    -------
    Cache
        Cache instance configured with 24-hour TTL
    """
    return Cache(cache_path=cache_dir, ttl_hours=24)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing.

    Returns
    -------
    pd.DataFrame
        Sample DataFrame with id, name, value columns
    """
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["apple", "banana", "cherry"],
            "value": [100.0, 200.0, 300.0],
        }
    )


class TestCacheInit:
    """Tests for Cache initialization."""

    def test_正常系_デフォルトTTLで初期化される(self, cache_dir: Path) -> None:
        """デフォルトのTTL（24時間）で初期化されることを確認。"""
        cache = Cache(cache_path=cache_dir)

        assert cache.ttl_hours == 24

    def test_正常系_カスタムTTLで初期化される(self, cache_dir: Path) -> None:
        """カスタムのTTL値で初期化されることを確認。"""
        cache = Cache(cache_path=cache_dir, ttl_hours=48)

        assert cache.ttl_hours == 48

    def test_正常系_文字列パスで初期化できる(self, cache_dir: Path) -> None:
        """文字列形式のパスでも初期化できることを確認。"""
        cache = Cache(cache_path=str(cache_dir), ttl_hours=24)

        assert cache.cache_path == cache_dir

    def test_正常系_キャッシュディレクトリが自動作成される(
        self, cache_dir: Path
    ) -> None:
        """キャッシュディレクトリが存在しない場合、自動的に作成されることを確認。"""
        assert not cache_dir.exists()

        Cache(cache_path=cache_dir, ttl_hours=24)

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_正常系_既存のディレクトリでも初期化できる(self, cache_dir: Path) -> None:
        """既に存在するディレクトリでも問題なく初期化できることを確認。"""
        cache_dir.mkdir(parents=True, exist_ok=True)
        assert cache_dir.exists()

        cache = Cache(cache_path=cache_dir, ttl_hours=24)

        assert cache.cache_path == cache_dir


class TestCacheKeyToPath:
    """Tests for cache key to file path conversion."""

    def test_正常系_キャッシュキーからファイルパスを生成できる(
        self, cache: Cache, cache_dir: Path
    ) -> None:
        """キャッシュキーから正しいファイルパスが生成されることを確認。"""
        key = "test_key"

        file_path = cache._key_to_path(key)

        assert file_path.parent == cache_dir
        assert file_path.suffix == ".parquet"
        assert "test_key" in str(file_path)

    def test_正常系_異なるキーで異なるパスが生成される(self, cache: Cache) -> None:
        """異なるキーに対して異なるファイルパスが生成されることを確認。"""
        path1 = cache._key_to_path("key1")
        path2 = cache._key_to_path("key2")

        assert path1 != path2

    def test_正常系_同じキーで同じパスが生成される(self, cache: Cache) -> None:
        """同じキーに対して常に同じファイルパスが生成されることを確認。"""
        path1 = cache._key_to_path("same_key")
        path2 = cache._key_to_path("same_key")

        assert path1 == path2

    def test_正常系_特殊文字を含むキーでもパスが生成できる(self, cache: Cache) -> None:
        """特殊文字を含むキーでもファイルパスが正しく生成されることを確認。"""
        key = "stock/AAPL/2024-01-01"

        file_path = cache._key_to_path(key)

        assert file_path.suffix == ".parquet"
        # ファイルシステムで有効なパスになっていることを確認
        assert "/" not in file_path.name or file_path.exists() is False


class TestCacheSetAndGet:
    """Tests for cache set and get operations."""

    def test_正常系_データをParquet形式で保存して読み込める(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """データをParquet形式で保存し、正しく読み込めることを確認。"""
        key = "test_data"

        cache.set(key, sample_dataframe)
        result = cache.get(key)

        assert result is not None
        pd.testing.assert_frame_equal(result, sample_dataframe)

    def test_正常系_空のDataFrameも保存できる(self, cache: Cache) -> None:
        """空のDataFrameも保存・読み込みできることを確認。"""
        key = "empty_data"
        empty_df = pd.DataFrame()

        cache.set(key, empty_df)
        result = cache.get(key)

        assert result is not None
        assert len(result) == 0

    def test_正常系_複数のキーでデータを保存できる(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """複数の異なるキーでデータを保存・読み込みできることを確認。"""
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.copy()
        df2["value"] = df2["value"] * 2

        cache.set("key1", df1)
        cache.set("key2", df2)

        result1 = cache.get("key1")
        result2 = cache.get("key2")

        assert result1 is not None
        assert result2 is not None
        pd.testing.assert_frame_equal(result1, df1)
        pd.testing.assert_frame_equal(result2, df2)

    def test_正常系_同じキーで上書き保存できる(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """同じキーでデータを上書き保存できることを確認。"""
        key = "overwrite_key"
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.copy()
        df2["value"] = [999.0, 888.0, 777.0]

        cache.set(key, df1)
        cache.set(key, df2)
        result = cache.get(key)

        assert result is not None
        pd.testing.assert_frame_equal(result, df2)

    def test_異常系_存在しないキーでgetするとNoneを返す(self, cache: Cache) -> None:
        """存在しないキーでgetした場合、Noneが返されることを確認。"""
        result = cache.get("nonexistent_key")

        assert result is None


class TestCacheTTL:
    """Tests for cache TTL (Time To Live) functionality."""

    def test_正常系_TTL内のキャッシュは有効と判定される(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """TTL内のキャッシュがis_validでTrueを返すことを確認。"""
        key = "fresh_data"
        cache.set(key, sample_dataframe)

        assert cache.is_valid(key) is True

    def test_正常系_TTL超過のキャッシュは無効と判定される(
        self, cache_dir: Path, sample_dataframe: pd.DataFrame
    ) -> None:
        """TTL超過のキャッシュがis_validでFalseを返すことを確認。"""
        cache = Cache(cache_path=cache_dir, ttl_hours=1)
        key = "old_data"
        cache.set(key, sample_dataframe)

        # ファイルの更新時刻を2時間前に変更
        file_path = cache._key_to_path(key)
        old_time = time.time() - 2 * 3600  # 2 hours ago
        os.utime(file_path, (old_time, old_time))

        assert cache.is_valid(key) is False

    def test_正常系_TTL超過のキャッシュはgetでNoneを返す(
        self, cache_dir: Path, sample_dataframe: pd.DataFrame
    ) -> None:
        """TTL超過のキャッシュがgetでNoneを返すことを確認。"""
        cache = Cache(cache_path=cache_dir, ttl_hours=1)
        key = "expired_data"
        cache.set(key, sample_dataframe)

        # ファイルの更新時刻を2時間前に変更
        file_path = cache._key_to_path(key)
        old_time = time.time() - 2 * 3600
        os.utime(file_path, (old_time, old_time))

        result = cache.get(key)

        assert result is None

    def test_正常系_存在しないキーはis_validでFalseを返す(self, cache: Cache) -> None:
        """存在しないキーに対してis_validがFalseを返すことを確認。"""
        assert cache.is_valid("nonexistent_key") is False

    def test_正常系_TTL0時間では即座に無効になる(
        self, cache_dir: Path, sample_dataframe: pd.DataFrame
    ) -> None:
        """TTLが0時間の場合、保存直後でも無効になることを確認。"""
        cache = Cache(cache_path=cache_dir, ttl_hours=0)
        key = "instant_expire"
        cache.set(key, sample_dataframe)

        # TTL=0なので即座に無効
        time.sleep(0.1)  # 少し待機
        assert cache.is_valid(key) is False


class TestCacheInvalidate:
    """Tests for cache invalidation."""

    def test_正常系_キャッシュを無効化できる(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """invalidateメソッドでキャッシュを削除できることを確認。"""
        key = "to_delete"
        cache.set(key, sample_dataframe)

        # キャッシュが存在することを確認
        assert cache.get(key) is not None

        cache.invalidate(key)

        # キャッシュが削除されていることを確認
        assert cache.get(key) is None
        assert cache.is_valid(key) is False

    def test_正常系_存在しないキーをinvalidateしてもエラーにならない(
        self, cache: Cache
    ) -> None:
        """存在しないキーをinvalidateしてもエラーが発生しないことを確認。"""
        # 例外が発生しないことを確認
        cache.invalidate("nonexistent_key")

    def test_正常系_invalidate後に再度setできる(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """invalidate後に同じキーで再度データを保存できることを確認。"""
        key = "reuse_key"
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.copy()
        df2["value"] = [1.0, 2.0, 3.0]

        cache.set(key, df1)
        cache.invalidate(key)
        cache.set(key, df2)

        result = cache.get(key)
        assert result is not None
        pd.testing.assert_frame_equal(result, df2)


class TestCacheEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_正常系_日本語キーでも動作する(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """日本語を含むキーでも正常に動作することを確認。"""
        key = "株価データ_2024"

        cache.set(key, sample_dataframe)
        result = cache.get(key)

        assert result is not None
        pd.testing.assert_frame_equal(result, sample_dataframe)

    def test_正常系_長いキーでも動作する(
        self, cache: Cache, sample_dataframe: pd.DataFrame
    ) -> None:
        """長いキー名でも正常に動作することを確認。"""
        key = "a" * 200  # 200文字のキー

        cache.set(key, sample_dataframe)
        result = cache.get(key)

        assert result is not None
        pd.testing.assert_frame_equal(result, sample_dataframe)

    def test_正常系_様々なデータ型を含むDataFrameを保存できる(
        self, cache: Cache
    ) -> None:
        """様々なデータ型を含むDataFrameを保存・読み込みできることを確認。"""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )
        key = "mixed_types"

        cache.set(key, df)
        result = cache.get(key)

        assert result is not None
        assert list(result.columns) == ["int_col", "float_col", "str_col", "bool_col"]

    def test_正常系_DatetimeIndexを含むDataFrameを保存できる(
        self, cache: Cache
    ) -> None:
        """DatetimeIndexを持つDataFrameを保存・読み込みできることを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=dates)
        key = "time_series"

        cache.set(key, df)
        result = cache.get(key)

        assert result is not None
        assert len(result) == 5
