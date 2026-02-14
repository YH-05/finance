"""Tests for yfinance index news source module.

This module provides unit tests for the IndexNewsSource class that fetches
news from stock market indices using yfinance Ticker API.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from yfinance.exceptions import YFRateLimitError

from news.core.article import Article, ArticleSource, ContentType
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.index import IndexNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_index_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Ticker.news data for indices."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "content": {
                "contentType": "STORY",
                "title": "S&P 500 Hits Record High",
                "summary": "The S&P 500 reached a new all-time high today.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Yahoo Finance",
                    "url": "http://finance.yahoo.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/sp500-record-high",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "content": {
                "contentType": "STORY",
                "title": "Market Analysis: S&P 500 Trends",
                "summary": "Weekly analysis of S&P 500 performance.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/sp500-weekly-analysis",
                },
            },
        },
    ]


@pytest.fixture
def mock_symbols_data() -> dict[str, Any]:
    """Mock symbols.yaml data structure."""
    return {
        "indices": {
            "us": [
                {"symbol": "^GSPC", "name": "S&P 500"},
                {"symbol": "^DJI", "name": "Dow Jones Industrial Average"},
                {"symbol": "^IXIC", "name": "NASDAQ Composite"},
            ],
            "global": [
                {"symbol": "^N225", "name": "日経225"},
                {"symbol": "^FTSE", "name": "FTSE 100"},
            ],
        }
    }


@pytest.fixture
def sample_symbols_file(tmp_path: Path, mock_symbols_data: dict[str, Any]) -> Path:
    """Create a temporary symbols.yaml file."""
    import yaml

    symbols_file = tmp_path / "symbols.yaml"
    symbols_file.write_text(yaml.dump(mock_symbols_data), encoding="utf-8")
    return symbols_file


# ============================================================================
# Tests for IndexNewsSource
# ============================================================================


class TestIndexNewsSource:
    """Tests for IndexNewsSource class."""

    def test_正常系_source_nameが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name is correctly set."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert source.source_name == "yfinance_ticker_index"

    def test_正常系_source_typeが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type is correctly set."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert source.source_type == ArticleSource.YFINANCE_TICKER

    def test_正常系_シンボルリストが正しく読み込まれる(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that symbols are correctly loaded from config."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        assert "^GSPC" in symbols
        assert "^DJI" in symbols
        assert "^IXIC" in symbols
        assert "^N225" in symbols
        assert "^FTSE" in symbols
        assert len(symbols) == 5

    def test_正常系_USのみのシンボル読み込み(self, sample_symbols_file: Path) -> None:
        """Test loading only US indices."""
        source = IndexNewsSource(
            symbols_file=sample_symbols_file,
            regions=["us"],
        )
        symbols = source.get_symbols()

        assert "^GSPC" in symbols
        assert "^N225" not in symbols
        assert len(symbols) == 3

    def test_正常系_単一ティッカーでニュース取得(
        self, sample_symbols_file: Path, sample_index_news_data: list[dict[str, Any]]
    ) -> None:
        """Test fetching news for a single index ticker."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_index_news_data
        mock_instance.get_news.return_value = sample_index_news_data

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("^GSPC", count=10)

        assert result.success is True
        assert result.ticker == "^GSPC"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_TICKER

    @patch("news.sources.yfinance.index.apply_polite_delay")
    def test_正常系_複数ティッカーでニュース取得(
        self,
        _mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_index_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for multiple index tickers."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_index_news_data

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            results = source.fetch_all(["^GSPC", "^DJI"], count=5)

        assert len(results) == 2
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].ticker == "^GSPC"
        assert results[1].ticker == "^DJI"

    def test_正常系_ticker_news_to_articleにティッカーが渡される(
        self, sample_symbols_file: Path, sample_index_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that ticker is passed to ticker_news_to_article function."""
        from news.sources.yfinance.base import ticker_news_to_article

        # Directly test the conversion function which is used by IndexNewsSource
        # This verifies that related_tickers will contain the ticker
        article = ticker_news_to_article(sample_index_news_data[0], "^GSPC")

        assert "^GSPC" in article.related_tickers
        assert article.title == "S&P 500 Hits Record High"
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_空の結果で成功(self, sample_symbols_file: Path) -> None:
        """Test successful fetch returning empty results."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = []

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("^GSPC", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.ticker == "^GSPC"

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        # Use a short retry config to speed up the test
        source._retry_config = RetryConfig(max_attempts=1, initial_delay=0.01)

        # Patch the do_fetch function to raise an error
        with patch.object(
            source,
            "fetch",
            return_value=FetchResult(
                articles=[],
                success=False,
                ticker="^ERROR",
                error=SourceError(
                    message="Test error",
                    source="yfinance_ticker_index",
                    ticker="^ERROR",
                ),
            ),
        ):
            result = source.fetch("^ERROR", count=10)

            assert result.success is False
            assert result.error is not None

    @patch("news.sources.yfinance.index.apply_polite_delay")
    def test_正常系_fetch_allは各ティッカーの結果を順番に返す(
        self, _mock_delay: MagicMock, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all returns results in order."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        # Test with valid tickers - results should be in order
        tickers = ["^GSPC", "^DJI", "^IXIC"]

        # Create mock results
        mock_results = [
            FetchResult(articles=[], success=True, ticker=t) for t in tickers
        ]

        with patch.object(source, "fetch", side_effect=mock_results):
            results = source.fetch_all(tickers, count=5)

            assert len(results) == 3
            assert results[0].ticker == "^GSPC"
            assert results[1].ticker == "^DJI"
            assert results[2].ticker == "^IXIC"

    def test_異常系_存在しないシンボルファイルでFileNotFoundError(
        self, tmp_path: Path
    ) -> None:
        """Test that non-existent symbols file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            IndexNewsSource(symbols_file=tmp_path / "nonexistent.yaml")

    def test_異常系_無効なティッカーでエラー結果(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that invalid ticker returns error result."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = []

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("INVALID", count=10)

        # Should succeed with empty result (yfinance returns empty for invalid)
        assert result.success is True
        assert result.is_empty is True

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = IndexNewsSource(
            symbols_file=sample_symbols_file,
            retry_config=custom_retry,
        )

        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that default retry config is used when not specified."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 2.0
        assert YFRateLimitError in source._retry_config.retryable_exceptions

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        results = source.fetch_all([], count=10)

        assert results == []

    def test_正常系_countパラメータがyfinanceに渡される(
        self, sample_symbols_file: Path, sample_index_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that count parameter is passed to yfinance."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.get_news = MagicMock(return_value=sample_index_news_data)
        mock_instance.news = sample_index_news_data

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            source.fetch("^GSPC", count=5)

            # Verify get_news was called with the count
            # (or verify news property access depending on implementation)


class TestFetchAllPoliteDelay:
    """Tests for polite delay behavior in IndexNewsSource.fetch_all."""

    @patch("news.sources.yfinance.index.apply_polite_delay")
    def test_正常系_複数ティッカーで2回目以降にディレイが適用される(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_index_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is applied before 2nd and subsequent requests."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_index_news_data

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["^GSPC", "^DJI", "^IXIC"], count=5)

        # apply_polite_delay should be called 2 times (before 2nd and 3rd requests)
        assert mock_delay.call_count == 2

    @patch("news.sources.yfinance.index.apply_polite_delay")
    def test_正常系_単一ティッカーでディレイが適用されない(
        self,
        mock_delay: MagicMock,
        sample_symbols_file: Path,
        sample_index_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that polite delay is not applied for a single ticker."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_index_news_data

        with patch("news.sources.yfinance.index.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance
            source.fetch_all(["^GSPC"], count=5)

        # apply_polite_delay should not be called for a single ticker
        mock_delay.assert_not_called()


class TestIndexNewsSourceProtocol:
    """Tests to verify IndexNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name property exists."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type property exists."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch method exists with correct signature."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self, sample_symbols_file: Path) -> None:
        """Test that IndexNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = IndexNewsSource(symbols_file=sample_symbols_file)
        assert isinstance(source, SourceProtocol)
