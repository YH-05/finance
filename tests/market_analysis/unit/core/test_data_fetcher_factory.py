"""Unit tests for DataFetcherFactory."""

import pytest

from market_analysis.core import (
    BaseDataFetcher,
    DataFetcherFactory,
    FREDFetcher,
    YFinanceFetcher,
)


class TestDataFetcherFactoryCreate:
    """Tests for DataFetcherFactory.create method."""

    def test_create_yfinance_fetcher(self) -> None:
        """source='yfinance'でYFinanceFetcherが返される."""
        fetcher = DataFetcherFactory.create("yfinance")

        assert isinstance(fetcher, YFinanceFetcher)
        assert isinstance(fetcher, BaseDataFetcher)

    def test_create_fred_fetcher(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """source='fred'でFREDFetcherが返される."""
        # FRED_API_KEYが必要なのでモック設定
        monkeypatch.setenv("FRED_API_KEY", "test_api_key")

        fetcher = DataFetcherFactory.create("fred")

        assert isinstance(fetcher, FREDFetcher)
        assert isinstance(fetcher, BaseDataFetcher)

    def test_create_invalid_source_raises_value_error(self) -> None:
        """不正なソース指定でValueErrorが発生."""
        with pytest.raises(ValueError, match="Unknown data source"):
            DataFetcherFactory.create("invalid_source")

    def test_create_empty_source_raises_value_error(self) -> None:
        """空のソース指定でValueErrorが発生."""
        with pytest.raises(ValueError, match="Unknown data source"):
            DataFetcherFactory.create("")


class TestDataFetcherFactoryWithKwargs:
    """Tests for DataFetcherFactory with additional kwargs."""

    def test_create_yfinance_with_cache(self) -> None:
        """YFinanceFetcherにkwargsを渡せる."""
        from market_analysis.types import CacheConfig

        cache_config = CacheConfig(ttl_seconds=7200)
        fetcher = DataFetcherFactory.create("yfinance", cache_config=cache_config)

        assert isinstance(fetcher, YFinanceFetcher)

    def test_create_fred_with_api_key(self) -> None:
        """FREDFetcherにapi_keyを直接渡せる."""
        fetcher = DataFetcherFactory.create("fred", api_key="direct_api_key")

        assert isinstance(fetcher, FREDFetcher)


class TestDataFetcherFactoryGetSupportedSources:
    """Tests for DataFetcherFactory.get_supported_sources method."""

    def test_get_supported_sources_returns_list(self) -> None:
        """get_supported_sourcesがサポートソースのリストを返す."""
        sources = DataFetcherFactory.get_supported_sources()

        assert isinstance(sources, list)
        assert "yfinance" in sources
        assert "fred" in sources

    def test_get_supported_sources_count(self) -> None:
        """サポートソースが6つある（実4 + モック2）."""
        sources = DataFetcherFactory.get_supported_sources()

        # 4 real sources (yfinance, fred, bloomberg, factset) + 2 mock
        assert len(sources) == 6
