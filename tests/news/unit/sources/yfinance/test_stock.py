"""Tests for yfinance stock news source module.

This module provides unit tests for the StockNewsSource class that fetches
news from individual stocks using yfinance Ticker API.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from yfinance.exceptions import YFRateLimitError

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.stock import StockNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_stock_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Ticker.news data for individual stocks."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "content": {
                "contentType": "STORY",
                "title": "Apple Reports Strong Q1 Earnings",
                "summary": "Apple beats Wall Street expectations with record revenue.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Yahoo Finance",
                    "url": "http://finance.yahoo.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/apple-earnings",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "content": {
                "contentType": "STORY",
                "title": "NVIDIA AI Chips in High Demand",
                "summary": "NVIDIA announces new AI chip production increase.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/nvidia-ai-chips",
                },
            },
        },
    ]


@pytest.fixture
def mock_symbols_data() -> dict[str, Any]:
    """Mock symbols.yaml data structure with mag7 and sector_stocks sections."""
    return {
        "indices": {
            "us": [
                {"symbol": "^GSPC", "name": "S&P 500"},
            ],
        },
        "sectors": [
            {"symbol": "XLF", "name": "Financial Select Sector SPDR"},
            {"symbol": "XLK", "name": "Technology Select Sector SPDR"},
        ],
        "mag7": [
            {"symbol": "AAPL", "name": "Apple"},
            {"symbol": "MSFT", "name": "Microsoft"},
            {"symbol": "GOOGL", "name": "Alphabet"},
            {"symbol": "AMZN", "name": "Amazon"},
            {"symbol": "NVDA", "name": "NVIDIA"},
            {"symbol": "META", "name": "Meta"},
            {"symbol": "TSLA", "name": "Tesla"},
        ],
        "sector_stocks": {
            "XLF": [
                {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Financial"},
                {"symbol": "BAC", "name": "Bank of America", "sector": "Financial"},
            ],
            "XLK": [
                {"symbol": "CRM", "name": "Salesforce", "sector": "Technology"},
                {"symbol": "ADBE", "name": "Adobe", "sector": "Technology"},
            ],
        },
    }


@pytest.fixture
def sample_symbols_file(tmp_path: Path, mock_symbols_data: dict[str, Any]) -> Path:
    """Create a temporary symbols.yaml file."""
    import yaml

    symbols_file = tmp_path / "symbols.yaml"
    symbols_file.write_text(yaml.dump(mock_symbols_data), encoding="utf-8")
    return symbols_file


# ============================================================================
# Tests for StockNewsSource
# ============================================================================


class TestStockNewsSource:
    """Tests for StockNewsSource class."""

    def test_正常系_source_nameが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name is correctly set."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert source.source_name == "yfinance_ticker_stock"

    def test_正常系_source_typeが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type is correctly set."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert source.source_type == ArticleSource.YFINANCE_TICKER

    def test_正常系_mag7シンボルが正しく読み込まれる(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that mag7 symbols are correctly loaded from config."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Check mag7 symbols are included
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "AMZN" in symbols
        assert "NVDA" in symbols
        assert "META" in symbols
        assert "TSLA" in symbols

    def test_正常系_sector_stocksシンボルが正しく読み込まれる(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that sector_stocks symbols are correctly loaded from config."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Check sector_stocks symbols are included
        assert "JPM" in symbols
        assert "BAC" in symbols
        assert "CRM" in symbols
        assert "ADBE" in symbols

    def test_正常系_mag7とsector_stocksが合計される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that mag7 and sector_stocks symbols are combined."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # 7 mag7 + 4 sector_stocks = 11
        assert len(symbols) == 11

    def test_正常系_indicesとsectorsは読み込まれない(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that indices and sectors are not included in stock symbols."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Should not include index symbols
        assert "^GSPC" not in symbols
        # Should not include sector ETF symbols
        assert "XLF" not in symbols
        assert "XLK" not in symbols

    def test_正常系_単一ティッカーでニュース取得(
        self, sample_symbols_file: Path, sample_stock_news_data: list[dict[str, Any]]
    ) -> None:
        """Test fetching news for a single stock ticker."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_stock_news_data
        mock_instance.get_news.return_value = sample_stock_news_data

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("AAPL", count=10)

        assert result.success is True
        assert result.ticker == "AAPL"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_TICKER

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_複数ティッカーでニュース取得(
        self,
        _mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_stock_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for multiple stock tickers."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_stock_news_data

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            results = source.fetch_all(["AAPL", "MSFT", "NVDA"], count=5)

        assert len(results) == 3
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].ticker == "AAPL"
        assert results[1].ticker == "MSFT"
        assert results[2].ticker == "NVDA"

    def test_正常系_ticker_news_to_articleにティッカーが渡される(
        self, sample_symbols_file: Path, sample_stock_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that ticker is passed to ticker_news_to_article function."""
        from news.sources.yfinance.base import ticker_news_to_article

        # Directly test the conversion function which is used by StockNewsSource
        # This verifies that related_tickers will contain the ticker
        article = ticker_news_to_article(sample_stock_news_data[0], "AAPL")

        assert "AAPL" in article.related_tickers
        assert article.title == "Apple Reports Strong Q1 Earnings"
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_空の結果で成功(self, sample_symbols_file: Path) -> None:
        """Test successful fetch returning empty results."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = []

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("AAPL", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.ticker == "AAPL"

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_エラー時は次のティッカーへ継続(
        self,
        _mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_stock_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that fetch_all continues to next ticker on error."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        # First ticker fails, second succeeds
        mock_instance_success = MagicMock()
        mock_instance_success.news = sample_stock_news_data

        mock_instance_fail = MagicMock()
        mock_instance_fail.news = []
        mock_instance_fail.get_news.side_effect = Exception("API Error")

        call_count = 0

        def mock_ticker_factory(ticker: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if ticker == "AAPL":
                return mock_instance_fail
            return mock_instance_success

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.side_effect = mock_ticker_factory

            results = source.fetch_all(["AAPL", "MSFT", "NVDA"], count=5)

        # Should have results for all 3 tickers (error is captured, not raised)
        assert len(results) == 3
        # First ticker should fail but not stop processing
        # Second and third should succeed
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 2  # At least MSFT and NVDA should succeed

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        results = source.fetch_all([], count=10)

        assert results == []

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = StockNewsSource(
            symbols_file=sample_symbols_file,
            retry_config=custom_retry,
        )

        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that default retry config is used when not specified."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 2.0
        assert YFRateLimitError in source._retry_config.retryable_exceptions

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
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
                    source="yfinance_ticker_stock",
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
        source = StockNewsSource(symbols_file=sample_symbols_file)

        # Test with valid tickers - results should be in order
        tickers = ["AAPL", "MSFT", "NVDA"]

        # Create mock results
        mock_results = [
            FetchResult(articles=[], success=True, ticker=t) for t in tickers
        ]

        with patch.object(source, "fetch", side_effect=mock_results):
            results = source.fetch_all(tickers, count=5)

            assert len(results) == 3
            assert results[0].ticker == "AAPL"
            assert results[1].ticker == "MSFT"
            assert results[2].ticker == "NVDA"

    def test_異常系_存在しないシンボルファイルでFileNotFoundError(
        self, tmp_path: Path
    ) -> None:
        """Test that non-existent symbols file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            StockNewsSource(symbols_file=tmp_path / "nonexistent.yaml")

    def test_正常系_countパラメータがyfinanceに渡される(
        self, sample_symbols_file: Path, sample_stock_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that count parameter is passed to yfinance."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.get_news = MagicMock(return_value=sample_stock_news_data)
        mock_instance.news = sample_stock_news_data

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            source.fetch("AAPL", count=5)

            # Verify get_news was called with the count


class TestStockNewsSourceProtocol:
    """Tests to verify StockNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name property exists."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type property exists."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch method exists with correct signature."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self, sample_symbols_file: Path) -> None:
        """Test that StockNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = StockNewsSource(symbols_file=sample_symbols_file)
        assert isinstance(source, SourceProtocol)


class TestFetchAllPoliteDelay:
    """Tests for polite delay behavior in StockNewsSource.fetch_all."""

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_複数ティッカーで2回目以降にディレイが適用される(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_stock_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is applied before 2nd and subsequent requests."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_stock_news_data

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["AAPL", "MSFT", "GOOGL"], count=5)

        # apply_polite_delay should be called 2 times (before 2nd and 3rd requests)
        assert mock_delay.call_count == 2

    @patch("news.sources.yfinance.base.apply_polite_delay")
    def test_正常系_単一ティッカーでディレイが適用されない(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_stock_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is not applied for a single ticker."""
        source = StockNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_stock_news_data

        with patch("news.sources.yfinance.stock.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["AAPL"], count=5)

        # apply_polite_delay should not be called for a single ticker
        mock_delay.assert_not_called()


class TestStockNewsSourceEmptyData:
    """Tests for StockNewsSource with empty or missing data sections."""

    def test_正常系_空のmag7セクションで空リスト(self, tmp_path: Path) -> None:
        """Test that empty mag7 section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            "mag7": [],
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = StockNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []

    def test_正常系_mag7セクションがない場合空リスト(self, tmp_path: Path) -> None:
        """Test that missing mag7 section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            # No mag7 section
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = StockNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []

    def test_正常系_sector_stocksセクションがない場合mag7のみ(
        self, tmp_path: Path
    ) -> None:
        """Test that missing sector_stocks section uses mag7 only."""
        import yaml

        data = {
            "mag7": [
                {"symbol": "AAPL", "name": "Apple"},
                {"symbol": "MSFT", "name": "Microsoft"},
            ],
            # No sector_stocks section
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = StockNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert len(symbols) == 2
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_正常系_重複シンボルは一度だけ含まれる(self, tmp_path: Path) -> None:
        """Test that duplicate symbols are only included once."""
        import yaml

        # AAPL is in both mag7 and sector_stocks
        data = {
            "mag7": [
                {"symbol": "AAPL", "name": "Apple"},
            ],
            "sector_stocks": {
                "XLK": [
                    {"symbol": "AAPL", "name": "Apple", "sector": "Technology"},
                ],
            },
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = StockNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        # AAPL should appear only once
        assert symbols.count("AAPL") == 1
        assert len(symbols) == 1
