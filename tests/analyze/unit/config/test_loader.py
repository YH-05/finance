"""Tests for _load_symbols_config() function in loader.py.

This module tests the Pydantic model loader function for Issue #2710.
"""

from __future__ import annotations

from functools import lru_cache

import pytest

from analyze.config.loader import _load_symbols_config
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
