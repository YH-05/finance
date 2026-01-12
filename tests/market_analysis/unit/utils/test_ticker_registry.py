"""Tests for ticker_registry module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from market_analysis.utils.ticker_registry import (
    TickerInfo,
    TickerRegistry,
    get_ticker_registry,
)


@pytest.fixture
def sample_config() -> dict:
    """Sample ticker configuration."""
    return {
        "Stock Indices": {
            "^GSPC": {
                "name_ja": "S&P 500",
                "name_en": "S&P 500 Index",
                "category": "index",
                "region": "US",
                "currency": "USD",
                "description": "米国大型株500銘柄の時価総額加重平均指数。",
            },
            "^N225": {
                "name_ja": "日経平均株価",
                "name_en": "Nikkei 225",
                "category": "index",
                "region": "JP",
                "currency": "JPY",
                "description": "東京証券取引所プライム市場の代表的な225銘柄。",
            },
        },
        "Forex": {
            "USDJPY=X": {
                "name_ja": "米ドル/円",
                "name_en": "USD/JPY",
                "category": "forex",
                "base": "USD",
                "quote": "JPY",
                "description": "米ドルと日本円の為替レート。",
            },
        },
        "Commodities": {
            "GC=F": {
                "name_ja": "金先物",
                "name_en": "Gold Futures",
                "category": "commodity",
                "unit": "USD/oz",
                "description": "COMEX金先物。",
            },
        },
    }


@pytest.fixture
def config_file(sample_config: dict, tmp_path: Path) -> Path:
    """Create a temporary config file."""
    config_path = tmp_path / "tickers.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(sample_config, f)
    return config_path


class TestTickerInfo:
    """Tests for TickerInfo dataclass."""

    def test_create_ticker_info(self) -> None:
        """Test creating a TickerInfo instance."""
        info = TickerInfo(
            symbol="^GSPC",
            name_ja="S&P 500",
            name_en="S&P 500 Index",
            category="index",
            group="Stock Indices",
            description="Test description",
        )

        assert info.symbol == "^GSPC"
        assert info.name_ja == "S&P 500"
        assert info.name_en == "S&P 500 Index"
        assert info.category == "index"
        assert info.group == "Stock Indices"
        assert info.description == "Test description"
        assert info.metadata == {}

    def test_ticker_info_with_metadata(self) -> None:
        """Test creating a TickerInfo with metadata."""
        info = TickerInfo(
            symbol="USDJPY=X",
            name_ja="米ドル/円",
            name_en="USD/JPY",
            category="forex",
            group="Forex",
            description="為替レート",
            metadata={"base": "USD", "quote": "JPY"},
        )

        assert info.metadata["base"] == "USD"
        assert info.metadata["quote"] == "JPY"

    def test_ticker_info_is_frozen(self) -> None:
        """Test that TickerInfo is immutable."""
        info = TickerInfo(
            symbol="^GSPC",
            name_ja="S&P 500",
            name_en="S&P 500 Index",
            category="index",
            group="Stock Indices",
            description="Test",
        )

        with pytest.raises(AttributeError):
            info.symbol = "^DJI"


class TestTickerRegistry:
    """Tests for TickerRegistry class."""

    def test_load_config(self, config_file: Path) -> None:
        """Test loading ticker configuration."""
        registry = TickerRegistry(config_path=config_file)

        assert len(registry) == 4
        assert "^GSPC" in registry
        assert "USDJPY=X" in registry
        assert "GC=F" in registry

    def test_get_ticker(self, config_file: Path) -> None:
        """Test getting ticker by symbol."""
        registry = TickerRegistry(config_path=config_file)

        info = registry.get("^GSPC")
        assert info is not None
        assert info.name_ja == "S&P 500"
        assert info.name_en == "S&P 500 Index"
        assert info.category == "index"

    def test_get_nonexistent_ticker(self, config_file: Path) -> None:
        """Test getting a non-existent ticker returns None."""
        registry = TickerRegistry(config_path=config_file)

        info = registry.get("INVALID")
        assert info is None

    def test_get_by_category(self, config_file: Path) -> None:
        """Test getting tickers by category."""
        registry = TickerRegistry(config_path=config_file)

        indices = registry.get_by_category("index")
        assert len(indices) == 2
        symbols = [t.symbol for t in indices]
        assert "^GSPC" in symbols
        assert "^N225" in symbols

    def test_get_by_category_empty(self, config_file: Path) -> None:
        """Test getting tickers by non-existent category."""
        registry = TickerRegistry(config_path=config_file)

        result = registry.get_by_category("crypto")
        assert result == []

    def test_get_by_group(self, config_file: Path) -> None:
        """Test getting tickers by group."""
        registry = TickerRegistry(config_path=config_file)

        forex = registry.get_by_group("Forex")
        assert len(forex) == 1
        assert forex[0].symbol == "USDJPY=X"

    def test_get_symbols(self, config_file: Path) -> None:
        """Test getting all symbols."""
        registry = TickerRegistry(config_path=config_file)

        symbols = registry.get_symbols()
        assert len(symbols) == 4
        assert "^GSPC" in symbols
        assert "GC=F" in symbols

    def test_get_symbols_by_category(self, config_file: Path) -> None:
        """Test getting symbols filtered by category."""
        registry = TickerRegistry(config_path=config_file)

        symbols = registry.get_symbols(category="index")
        assert len(symbols) == 2
        assert "^GSPC" in symbols
        assert "^N225" in symbols

    def test_get_symbols_by_group(self, config_file: Path) -> None:
        """Test getting symbols filtered by group."""
        registry = TickerRegistry(config_path=config_file)

        symbols = registry.get_symbols(group="Commodities")
        assert len(symbols) == 1
        assert "GC=F" in symbols

    def test_list_categories(self, config_file: Path) -> None:
        """Test listing all categories."""
        registry = TickerRegistry(config_path=config_file)

        categories = registry.list_categories()
        assert "index" in categories
        assert "forex" in categories
        assert "commodity" in categories

    def test_list_groups(self, config_file: Path) -> None:
        """Test listing all groups."""
        registry = TickerRegistry(config_path=config_file)

        groups = registry.list_groups()
        assert "Stock Indices" in groups
        assert "Forex" in groups
        assert "Commodities" in groups

    def test_contains(self, config_file: Path) -> None:
        """Test contains check."""
        registry = TickerRegistry(config_path=config_file)

        assert registry.contains("^GSPC")
        assert not registry.contains("INVALID")

    def test_iter(self, config_file: Path) -> None:
        """Test iterating over registry."""
        registry = TickerRegistry(config_path=config_file)

        symbols = list(registry)
        assert len(symbols) == 4
        assert "^GSPC" in symbols

    def test_missing_config_file(self, tmp_path: Path) -> None:
        """Test handling of missing config file."""
        registry = TickerRegistry(config_path=tmp_path / "nonexistent.json")

        assert len(registry) == 0
        assert registry.get("^GSPC") is None

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Test handling of invalid JSON."""
        config_path = tmp_path / "invalid.json"
        with open(config_path, "w") as f:
            f.write("not valid json")

        registry = TickerRegistry(config_path=config_path)

        assert len(registry) == 0

    def test_metadata_extraction(self, config_file: Path) -> None:
        """Test that metadata is correctly extracted."""
        registry = TickerRegistry(config_path=config_file)

        info = registry.get("USDJPY=X")
        assert info is not None
        assert info.metadata.get("base") == "USD"
        assert info.metadata.get("quote") == "JPY"

    def test_lazy_loading(self, config_file: Path) -> None:
        """Test that config is loaded lazily."""
        registry = TickerRegistry(config_path=config_file)

        # Config should not be loaded yet
        assert not registry._loaded

        # Accessing triggers loading
        _ = registry.get("^GSPC")
        assert registry._loaded


class TestGetTickerRegistry:
    """Tests for get_ticker_registry function."""

    def test_returns_singleton(self) -> None:
        """Test that get_ticker_registry returns the same instance."""
        # Reset singleton
        import market_analysis.utils.ticker_registry as module

        module._default_registry = None

        registry1 = get_ticker_registry()
        registry2 = get_ticker_registry()

        assert registry1 is registry2


class TestDefaultConfig:
    """Tests using the default configuration file."""

    def test_default_config_loads(self) -> None:
        """Test that the default config file loads successfully."""
        # Reset singleton to use default config
        import market_analysis.utils.ticker_registry as module

        module._default_registry = None

        registry = TickerRegistry()

        # Should have tickers from the default config
        assert len(registry) > 0

    def test_default_config_has_indices(self) -> None:
        """Test that default config contains stock indices."""
        registry = TickerRegistry()

        assert registry.contains("^GSPC")
        assert registry.contains("^N225")

    def test_default_config_has_forex(self) -> None:
        """Test that default config contains forex pairs."""
        registry = TickerRegistry()

        assert registry.contains("USDJPY=X")
        assert registry.contains("EURUSD=X")

    def test_default_config_has_commodities(self) -> None:
        """Test that default config contains commodities."""
        registry = TickerRegistry()

        assert registry.contains("GC=F")
        assert registry.contains("CL=F")
