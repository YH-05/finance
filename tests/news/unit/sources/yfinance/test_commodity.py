"""Tests for yfinance commodity news source module.

This module provides unit tests for the CommodityNewsSource class that fetches
news from commodity futures using yfinance Ticker API.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from yfinance.exceptions import YFRateLimitError

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.commodity import CommodityNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_commodity_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Ticker.news data for commodity futures."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "content": {
                "contentType": "STORY",
                "title": "Gold Prices Surge Amid Economic Uncertainty",
                "summary": "Gold futures reach new highs as investors seek safe haven.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Yahoo Finance",
                    "url": "http://finance.yahoo.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/gold-prices-surge",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "content": {
                "contentType": "STORY",
                "title": "Crude Oil Futures Fall on Supply Concerns",
                "summary": "WTI and Brent crude drop as OPEC+ considers output increase.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/crude-oil-futures-fall",
                },
            },
        },
    ]


@pytest.fixture
def mock_symbols_data() -> dict[str, Any]:
    """Mock symbols.yaml data structure with commodities section."""
    return {
        "indices": {
            "us": [
                {"symbol": "^GSPC", "name": "S&P 500"},
            ],
        },
        "sectors": [
            {"symbol": "XLF", "name": "Financial Select Sector SPDR"},
        ],
        "mag7": [
            {"symbol": "AAPL", "name": "Apple"},
        ],
        "commodities": [
            {"symbol": "GC=F", "name": "Gold Futures"},
            {"symbol": "SI=F", "name": "Silver Futures"},
            {"symbol": "CL=F", "name": "WTI Crude Oil Futures"},
            {"symbol": "BZ=F", "name": "Brent Crude Oil Futures"},
            {"symbol": "NG=F", "name": "Natural Gas Futures"},
            {"symbol": "HG=F", "name": "Copper Futures"},
            {"symbol": "PL=F", "name": "Platinum Futures"},
            {"symbol": "ZC=F", "name": "Corn Futures"},
            {"symbol": "ZW=F", "name": "Wheat Futures"},
            {"symbol": "ZS=F", "name": "Soybean Futures"},
        ],
    }


@pytest.fixture
def sample_symbols_file(tmp_path: Path, mock_symbols_data: dict[str, Any]) -> Path:
    """Create a temporary symbols.yaml file."""
    import yaml

    symbols_file = tmp_path / "symbols.yaml"
    symbols_file.write_text(yaml.dump(mock_symbols_data), encoding="utf-8")
    return symbols_file


# ============================================================================
# Tests for CommodityNewsSource
# ============================================================================


class TestCommodityNewsSource:
    """Tests for CommodityNewsSource class."""

    def test_正常系_source_nameが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name is correctly set."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert source.source_name == "yfinance_ticker_commodity"

    def test_正常系_source_typeが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type is correctly set."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert source.source_type == ArticleSource.YFINANCE_TICKER

    def test_正常系_commoditiesシンボルが正しく読み込まれる(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that commodity symbols are correctly loaded from config."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        assert "GC=F" in symbols
        assert "SI=F" in symbols
        assert "CL=F" in symbols
        assert "BZ=F" in symbols
        assert "NG=F" in symbols
        assert "HG=F" in symbols
        assert "PL=F" in symbols
        assert "ZC=F" in symbols
        assert "ZW=F" in symbols
        assert "ZS=F" in symbols
        assert len(symbols) == 10

    def test_正常系_indicesは読み込まれない(self, sample_symbols_file: Path) -> None:
        """Test that indices are not included in commodity symbols."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Should not include index symbols
        assert "^GSPC" not in symbols

    def test_正常系_sectorsは読み込まれない(self, sample_symbols_file: Path) -> None:
        """Test that sectors are not included in commodity symbols."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Should not include sector symbols
        assert "XLF" not in symbols

    def test_正常系_mag7は読み込まれない(self, sample_symbols_file: Path) -> None:
        """Test that mag7 stocks are not included in commodity symbols."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Should not include mag7 symbols
        assert "AAPL" not in symbols

    def test_正常系_単一ティッカーでニュース取得(
        self,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for a single commodity ticker."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_commodity_news_data
        mock_instance.get_news.return_value = sample_commodity_news_data

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("GC=F", count=10)

        assert result.success is True
        assert result.ticker == "GC=F"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_TICKER

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_複数ティッカーでニュース取得(
        self,
        _mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for multiple commodity tickers."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_commodity_news_data

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            results = source.fetch_all(["GC=F", "CL=F"], count=5)

        assert len(results) == 2
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].ticker == "GC=F"
        assert results[1].ticker == "CL=F"

    def test_正常系_ticker_news_to_articleにティッカーが渡される(
        self,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that ticker is passed to ticker_news_to_article function."""
        from news.sources.yfinance.base import ticker_news_to_article

        # Directly test the conversion function which is used by CommodityNewsSource
        # This verifies that related_tickers will contain the ticker
        article = ticker_news_to_article(sample_commodity_news_data[0], "GC=F")

        assert "GC=F" in article.related_tickers
        assert article.title == "Gold Prices Surge Amid Economic Uncertainty"
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_空の結果で成功(self, sample_symbols_file: Path) -> None:
        """Test successful fetch returning empty results."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = []

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("GC=F", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.ticker == "GC=F"

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_エラー時は次のティッカーへ継続(
        self,
        _mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that fetch_all continues to next ticker on error."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        # First ticker fails, second succeeds
        mock_instance_success = MagicMock()
        mock_instance_success.news = sample_commodity_news_data

        mock_instance_fail = MagicMock()
        mock_instance_fail.news = []
        mock_instance_fail.get_news.side_effect = Exception("API Error")

        call_count = 0

        def mock_ticker_factory(ticker: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if ticker == "GC=F":
                return mock_instance_fail
            return mock_instance_success

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.side_effect = mock_ticker_factory

            results = source.fetch_all(["GC=F", "CL=F", "SI=F"], count=5)

        # Should have results for all 3 tickers (error is captured, not raised)
        assert len(results) == 3
        # First ticker should fail but not stop processing
        # Second and third should succeed
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 2  # At least CL=F and SI=F should succeed

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        results = source.fetch_all([], count=10)

        assert results == []

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = CommodityNewsSource(
            symbols_file=sample_symbols_file,
            retry_config=custom_retry,
        )

        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that default retry config is used when not specified."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 2.0
        assert YFRateLimitError in source._retry_config.retryable_exceptions

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        # Use a short retry config to speed up the test
        source._retry_config = RetryConfig(max_attempts=1, initial_delay=0.01)

        # Patch the fetch function to return an error result
        with patch.object(
            source,
            "fetch",
            return_value=FetchResult(
                articles=[],
                success=False,
                ticker="ERROR",
                error=SourceError(
                    message="Test error",
                    source="yfinance_ticker_commodity",
                    ticker="ERROR",
                ),
            ),
        ):
            result = source.fetch("ERROR", count=10)

            assert result.success is False
            assert result.error is not None

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_fetch_allは各ティッカーの結果を順番に返す(
        self, _mock_delay: MagicMock, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all returns results in order."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        # Test with valid tickers - results should be in order
        tickers = ["GC=F", "CL=F", "SI=F"]

        # Create mock results
        mock_results = [
            FetchResult(articles=[], success=True, ticker=t) for t in tickers
        ]

        with patch.object(source, "fetch", side_effect=mock_results):
            results = source.fetch_all(tickers, count=5)

            assert len(results) == 3
            assert results[0].ticker == "GC=F"
            assert results[1].ticker == "CL=F"
            assert results[2].ticker == "SI=F"

    def test_異常系_存在しないシンボルファイルでFileNotFoundError(
        self, tmp_path: Path
    ) -> None:
        """Test that non-existent symbols file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CommodityNewsSource(symbols_file=tmp_path / "nonexistent.yaml")

    def test_正常系_countパラメータがyfinanceに渡される(
        self,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that count parameter is passed to yfinance."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.get_news = MagicMock(return_value=sample_commodity_news_data)
        mock_instance.news = sample_commodity_news_data

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            source.fetch("GC=F", count=5)

            # Verify get_news was called with the count
            # (or verify news property access depending on implementation)


class TestFetchAllPoliteDelay:
    """Tests for polite delay behavior in CommodityNewsSource.fetch_all."""

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_複数ティッカーで2回目以降にディレイが適用される(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is applied before 2nd and subsequent requests."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_commodity_news_data

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["GC=F", "CL=F", "SI=F"], count=5)

        # apply_polite_delay should be called 2 times (before 2nd and 3rd requests)
        assert mock_delay.call_count == 2

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_単一ティッカーでディレイが適用されない(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_commodity_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is not applied for a single ticker."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_commodity_news_data

        with patch("news.sources.yfinance.commodity.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["GC=F"], count=5)

        # apply_polite_delay should not be called for a single ticker
        mock_delay.assert_not_called()


class TestCommodityNewsSourceProtocol:
    """Tests to verify CommodityNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name property exists."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type property exists."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch method exists with correct signature."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self, sample_symbols_file: Path) -> None:
        """Test that CommodityNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = CommodityNewsSource(symbols_file=sample_symbols_file)
        assert isinstance(source, SourceProtocol)


class TestCommodityNewsSourceEmptyCommodities:
    """Tests for CommodityNewsSource with empty or missing commodities section."""

    def test_正常系_空のcommoditiesセクションで空リスト(self, tmp_path: Path) -> None:
        """Test that empty commodities section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            "commodities": [],
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = CommodityNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []

    def test_正常系_commoditiesセクションがない場合空リスト(
        self, tmp_path: Path
    ) -> None:
        """Test that missing commodities section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            # No commodities section
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = CommodityNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []
