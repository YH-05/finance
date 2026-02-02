"""Tests for loader.py functions.

This module tests the loader functions including:
- _load_symbols_config(): Pydantic model loader with caching
- load_symbols_config(): Raw YAML loader with caching
- get_symbols(): High-level symbol getter
- get_symbol_group(): High-level group getter
- get_return_periods(): High-level periods getter

Created for Issue #2710 and enhanced for Issue #2712.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from analyze.config.loader import (
    _load_symbols_config,
    get_return_periods,
    get_symbol_group,
    get_symbols,
    load_symbols_config,
)
from analyze.config.models import SymbolsConfig


class TestLoadSymbolsConfig:
    """Tests for _load_symbols_config function."""

    def test_正常系_SymbolsConfigインスタンスを返す(self) -> None:
        """_load_symbols_config が SymbolsConfig インスタンスを返すことを確認."""
        # Clear cache to ensure fresh load
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        assert isinstance(config, SymbolsConfig)

    def test_正常系_lru_cacheでキャッシュされる(self) -> None:
        """_load_symbols_config が @lru_cache でキャッシュされることを確認."""
        # Clear cache
        _load_symbols_config.cache_clear()

        # First call
        config1 = _load_symbols_config()

        # Second call should return same instance (cached)
        config2 = _load_symbols_config()

        # Same instance due to caching
        assert config1 is config2

        # Verify cache hit
        cache_info = _load_symbols_config.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1

    def test_正常系_mag7シンボルを取得できる(self) -> None:
        """_load_symbols_config から MAG7 シンボルを取得できることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        mag7_symbols = config.get_symbols("mag7")
        assert len(mag7_symbols) == 7
        assert "AAPL" in mag7_symbols
        assert "MSFT" in mag7_symbols
        assert "NVDA" in mag7_symbols

    def test_正常系_indicesサブグループを取得できる(self) -> None:
        """_load_symbols_config から indices サブグループを取得できることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        us_indices = config.get_symbols("indices", "us")
        assert "^GSPC" in us_indices
        assert "^DJI" in us_indices

        global_indices = config.get_symbols("indices", "global")
        assert "^N225" in global_indices

    def test_正常系_currenciesサブグループを取得できる(self) -> None:
        """_load_symbols_config から currencies サブグループを取得できることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        jpy_crosses = config.get_symbols("currencies", "jpy_crosses")
        assert "USDJPY=X" in jpy_crosses
        assert "EURJPY=X" in jpy_crosses

    def test_正常系_return_periodsにアクセスできる(self) -> None:
        """_load_symbols_config から return_periods にアクセスできることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        assert config.return_periods.d1 == 1
        assert config.return_periods.w1 == 5
        assert config.return_periods.ytd == "ytd"

    def test_正常系_sector_stocksにアクセスできる(self) -> None:
        """_load_symbols_config から sector_stocks にアクセスできることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        xlf_symbols = config.get_symbols("sector_stocks", "XLF")
        assert "JPM" in xlf_symbols

    def test_正常系_commoditiesを取得できる(self) -> None:
        """_load_symbols_config から commodities を取得できることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        commodities = config.get_symbols("commodities")
        assert "GC=F" in commodities
        assert "CL=F" in commodities

    def test_正常系_sectorsを取得できる(self) -> None:
        """_load_symbols_config から sectors を取得できることを確認."""
        _load_symbols_config.cache_clear()

        config = _load_symbols_config()

        sectors = config.get_symbols("sectors")
        assert "XLF" in sectors
        assert "XLK" in sectors


class TestLoadSymbolsConfigRaw:
    """Tests for load_symbols_config (raw YAML) function."""

    def test_正常系_辞書を返す(self) -> None:
        """load_symbols_config が辞書を返すことを確認."""
        load_symbols_config.cache_clear()

        config = load_symbols_config()

        assert isinstance(config, dict)
        assert "mag7" in config
        assert "indices" in config
        assert "sectors" in config

    def test_正常系_lru_cacheでキャッシュされる(self) -> None:
        """load_symbols_config が @lru_cache でキャッシュされることを確認."""
        load_symbols_config.cache_clear()

        # First call
        config1 = load_symbols_config()

        # Second call should return same instance (cached)
        config2 = load_symbols_config()

        # Same instance due to caching
        assert config1 is config2

        # Verify cache hit
        cache_info = load_symbols_config.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1


class TestCacheBehavior:
    """Tests for cache behavior across loader functions."""

    def test_正常系_cache_clearでキャッシュがクリアされる(self) -> None:
        """cache_clear() でキャッシュがクリアされることを確認."""
        # First, load and populate cache
        _load_symbols_config.cache_clear()
        _load_symbols_config()

        # Clear cache
        _load_symbols_config.cache_clear()

        # Verify cache is cleared
        cache_info = _load_symbols_config.cache_info()
        assert cache_info.hits == 0
        assert cache_info.misses == 0

        # Load again
        _load_symbols_config()

        # Should be a new miss
        cache_info = _load_symbols_config.cache_info()
        assert cache_info.misses == 1

    def test_正常系_複数回のキャッシュヒットをカウントできる(self) -> None:
        """複数回のキャッシュヒットが正しくカウントされることを確認."""
        _load_symbols_config.cache_clear()

        # First call - miss
        _load_symbols_config()

        # Multiple subsequent calls - all hits
        for _ in range(5):
            _load_symbols_config()

        cache_info = _load_symbols_config.cache_info()
        assert cache_info.hits == 5
        assert cache_info.misses == 1

    def test_正常系_maxsize1で古いキャッシュは保持されない(self) -> None:
        """maxsize=1 なので1つのエントリのみキャッシュされることを確認."""
        _load_symbols_config.cache_clear()

        _load_symbols_config()

        cache_info = _load_symbols_config.cache_info()
        assert cache_info.maxsize == 1
        assert cache_info.currsize == 1


class TestPerformance:
    """Performance tests for loader functions."""

    def test_パフォーマンス_キャッシュヒット時は高速(self) -> None:
        """キャッシュヒット時の読み込みが高速であることを確認."""
        _load_symbols_config.cache_clear()

        # First call (cache miss) - may take longer
        _load_symbols_config()

        # Subsequent calls should be very fast (< 1ms)
        start = time.perf_counter()
        for _ in range(100):
            _load_symbols_config()
        elapsed = time.perf_counter() - start

        # 100 cached calls should take less than 10ms
        assert elapsed < 0.01, f"100 cached calls took {elapsed:.4f}s, expected < 0.01s"

    def test_パフォーマンス_初回読み込みは妥当な時間で完了(self) -> None:
        """初回読み込みが妥当な時間で完了することを確認."""
        _load_symbols_config.cache_clear()

        start = time.perf_counter()
        _load_symbols_config()
        elapsed = time.perf_counter() - start

        # Initial load should complete within 1 second
        assert elapsed < 1.0, f"Initial load took {elapsed:.4f}s, expected < 1.0s"


class TestHighLevelFunctions:
    """Tests for high-level accessor functions."""

    def test_正常系_get_symbolsでシンボルリストを取得(self) -> None:
        """get_symbols でシンボルリストを取得できることを確認."""
        _load_symbols_config.cache_clear()

        symbols = get_symbols("mag7")

        assert len(symbols) == 7
        assert "AAPL" in symbols

    def test_正常系_get_symbolsでサブグループを指定(self) -> None:
        """get_symbols でサブグループを指定できることを確認."""
        _load_symbols_config.cache_clear()

        us_indices = get_symbols("indices", "us")

        assert "^GSPC" in us_indices
        assert "^DJI" in us_indices

    def test_正常系_get_symbol_groupで詳細情報を取得(self) -> None:
        """get_symbol_group で詳細情報を取得できることを確認."""
        _load_symbols_config.cache_clear()

        group = get_symbol_group("mag7")

        assert len(group) == 7
        assert group[0]["symbol"] == "AAPL"
        assert group[0]["name"] == "Apple"

    def test_正常系_get_return_periodsで期間定義を取得(self) -> None:
        """get_return_periods で期間定義を取得できることを確認."""
        _load_symbols_config.cache_clear()

        periods = get_return_periods()

        assert periods["1D"] == 1
        assert periods["1W"] == 5
        assert periods["YTD"] == "ytd"
        assert periods["1Y"] == 252


class TestErrorHandling:
    """Tests for error handling in loader functions."""

    def test_異常系_ファイル不存在でFileNotFoundError(self) -> None:
        """設定ファイルが存在しない場合 FileNotFoundError を発生させることを確認."""
        _load_symbols_config.cache_clear()

        with patch("analyze.config.loader.SYMBOLS_CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = False
            mock_path.__str__ = lambda _: "/nonexistent/path.yaml"

            with pytest.raises(FileNotFoundError):
                _load_symbols_config()
