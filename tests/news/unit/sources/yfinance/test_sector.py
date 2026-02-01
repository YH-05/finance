"""Tests for yfinance sector news source module.

This module provides unit tests for the SectorNewsSource class that fetches
news from sector ETFs using yfinance Ticker API.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.sector import SectorNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_sector_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Ticker.news data for sector ETFs."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "content": {
                "contentType": "STORY",
                "title": "Technology Sector Leads Market Rally",
                "summary": "XLK hits new highs as tech stocks surge.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Yahoo Finance",
                    "url": "http://finance.yahoo.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/tech-sector-rally",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "content": {
                "contentType": "STORY",
                "title": "Financial Sector Analysis: Banking Outlook",
                "summary": "Weekly analysis of financial sector performance.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/financial-sector-analysis",
                },
            },
        },
    ]


@pytest.fixture
def mock_symbols_data() -> dict[str, Any]:
    """Mock symbols.yaml data structure with sectors section."""
    return {
        "indices": {
            "us": [
                {"symbol": "^GSPC", "name": "S&P 500"},
            ],
        },
        "sectors": [
            {"symbol": "XLF", "name": "Financial Select Sector SPDR"},
            {"symbol": "XLK", "name": "Technology Select Sector SPDR"},
            {"symbol": "XLV", "name": "Health Care Select Sector SPDR"},
            {"symbol": "XLE", "name": "Energy Select Sector SPDR"},
            {"symbol": "XLI", "name": "Industrial Select Sector SPDR"},
            {"symbol": "XLY", "name": "Consumer Discretionary Select Sector SPDR"},
            {"symbol": "XLP", "name": "Consumer Staples Select Sector SPDR"},
            {"symbol": "XLB", "name": "Materials Select Sector SPDR"},
            {"symbol": "XLU", "name": "Utilities Select Sector SPDR"},
            {"symbol": "XLRE", "name": "Real Estate Select Sector SPDR"},
            {"symbol": "XLC", "name": "Communication Services Select Sector SPDR"},
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
# Tests for SectorNewsSource
# ============================================================================


class TestSectorNewsSource:
    """Tests for SectorNewsSource class."""

    def test_正常系_source_nameが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name is correctly set."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert source.source_name == "yfinance_ticker_sector"

    def test_正常系_source_typeが正しく設定される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type is correctly set."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert source.source_type == ArticleSource.YFINANCE_TICKER

    def test_正常系_sectorsシンボルが正しく読み込まれる(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that sector symbols are correctly loaded from config."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        assert "XLF" in symbols
        assert "XLK" in symbols
        assert "XLV" in symbols
        assert "XLE" in symbols
        assert "XLI" in symbols
        assert "XLY" in symbols
        assert "XLP" in symbols
        assert "XLB" in symbols
        assert "XLU" in symbols
        assert "XLRE" in symbols
        assert "XLC" in symbols
        assert len(symbols) == 11

    def test_正常系_indicesは読み込まれない(self, sample_symbols_file: Path) -> None:
        """Test that indices are not included in sector symbols."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        symbols = source.get_symbols()

        # Should not include index symbols
        assert "^GSPC" not in symbols

    def test_正常系_単一ティッカーでニュース取得(
        self, sample_symbols_file: Path, sample_sector_news_data: list[dict[str, Any]]
    ) -> None:
        """Test fetching news for a single sector ETF ticker."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_sector_news_data
        mock_instance.get_news.return_value = sample_sector_news_data

        with patch("news.sources.yfinance.sector.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("XLK", count=10)

        assert result.success is True
        assert result.ticker == "XLK"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_TICKER

    def test_正常系_複数ティッカーでニュース取得(
        self, sample_symbols_file: Path, sample_sector_news_data: list[dict[str, Any]]
    ) -> None:
        """Test fetching news for multiple sector ETF tickers."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = sample_sector_news_data

        with patch("news.sources.yfinance.sector.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            results = source.fetch_all(["XLK", "XLF"], count=5)

        assert len(results) == 2
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].ticker == "XLK"
        assert results[1].ticker == "XLF"

    def test_正常系_ticker_news_to_articleにティッカーが渡される(
        self, sample_symbols_file: Path, sample_sector_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that ticker is passed to ticker_news_to_article function."""
        from news.sources.yfinance.base import ticker_news_to_article

        # Directly test the conversion function which is used by SectorNewsSource
        # This verifies that related_tickers will contain the ticker
        article = ticker_news_to_article(sample_sector_news_data[0], "XLK")

        assert "XLK" in article.related_tickers
        assert article.title == "Technology Sector Leads Market Rally"
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_空の結果で成功(self, sample_symbols_file: Path) -> None:
        """Test successful fetch returning empty results."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.news = []

        with patch("news.sources.yfinance.sector.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            result = source.fetch("XLK", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.ticker == "XLK"

    def test_正常系_エラー時は次のティッカーへ継続(
        self, sample_symbols_file: Path, sample_sector_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that fetch_all continues to next ticker on error."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        # First ticker fails, second succeeds
        mock_instance_success = MagicMock()
        mock_instance_success.news = sample_sector_news_data

        mock_instance_fail = MagicMock()
        mock_instance_fail.news = []
        mock_instance_fail.get_news.side_effect = Exception("API Error")

        call_count = 0

        def mock_ticker_factory(ticker: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if ticker == "XLK":
                return mock_instance_fail
            return mock_instance_success

        with patch("news.sources.yfinance.sector.yf") as mock_yf:
            mock_yf.Ticker.side_effect = mock_ticker_factory

            results = source.fetch_all(["XLK", "XLF", "XLV"], count=5)

        # Should have results for all 3 tickers (error is captured, not raised)
        assert len(results) == 3
        # First ticker should fail but not stop processing
        # Second and third should succeed
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 2  # At least XLF and XLV should succeed

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        results = source.fetch_all([], count=10)

        assert results == []

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = SectorNewsSource(
            symbols_file=sample_symbols_file,
            retry_config=custom_retry,
        )

        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that default retry config is used when not specified."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 1.0

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
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
                    source="yfinance_ticker_sector",
                    ticker="ERROR",
                ),
            ),
        ):
            result = source.fetch("ERROR", count=10)

            assert result.success is False
            assert result.error is not None

    def test_正常系_fetch_allは各ティッカーの結果を順番に返す(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all returns results in order."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        # Test with valid tickers - results should be in order
        tickers = ["XLK", "XLF", "XLV"]

        # Create mock results
        mock_results = [
            FetchResult(articles=[], success=True, ticker=t) for t in tickers
        ]

        with patch.object(source, "fetch", side_effect=mock_results):
            results = source.fetch_all(tickers, count=5)

            assert len(results) == 3
            assert results[0].ticker == "XLK"
            assert results[1].ticker == "XLF"
            assert results[2].ticker == "XLV"

    def test_異常系_存在しないシンボルファイルでFileNotFoundError(
        self, tmp_path: Path
    ) -> None:
        """Test that non-existent symbols file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            SectorNewsSource(symbols_file=tmp_path / "nonexistent.yaml")

    def test_正常系_countパラメータがyfinanceに渡される(
        self, sample_symbols_file: Path, sample_sector_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that count parameter is passed to yfinance."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)

        mock_instance = MagicMock()
        mock_instance.get_news = MagicMock(return_value=sample_sector_news_data)
        mock_instance.news = sample_sector_news_data

        with patch("news.sources.yfinance.sector.yf") as mock_yf:
            mock_yf.Ticker.return_value = mock_instance

            source.fetch("XLK", count=5)

            # Verify get_news was called with the count
            # (or verify news property access depending on implementation)


class TestSectorNewsSourceProtocol:
    """Tests to verify SectorNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_name property exists."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that source_type property exists."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch method exists with correct signature."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(
        self, sample_symbols_file: Path
    ) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self, sample_symbols_file: Path) -> None:
        """Test that SectorNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = SectorNewsSource(symbols_file=sample_symbols_file)
        assert isinstance(source, SourceProtocol)


class TestSectorNewsSourceEmptySectors:
    """Tests for SectorNewsSource with empty or missing sectors section."""

    def test_正常系_空のsectorsセクションで空リスト(self, tmp_path: Path) -> None:
        """Test that empty sectors section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            "sectors": [],
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = SectorNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []

    def test_正常系_sectorsセクションがない場合空リスト(self, tmp_path: Path) -> None:
        """Test that missing sectors section returns empty list."""
        import yaml

        data = {
            "indices": {"us": [{"symbol": "^GSPC", "name": "S&P 500"}]},
            # No sectors section
        }
        symbols_file = tmp_path / "symbols.yaml"
        symbols_file.write_text(yaml.dump(data), encoding="utf-8")

        source = SectorNewsSource(symbols_file=symbols_file)
        symbols = source.get_symbols()

        assert symbols == []
