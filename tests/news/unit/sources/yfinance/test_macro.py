"""Tests for yfinance macro economics news source module.

This module provides unit tests for the MacroNewsSource class that fetches
macro economics news using yfinance Search API with keyword-based queries.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.macro import MacroNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_search_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Search.news data for macro economics keywords."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "content": {
                "contentType": "STORY",
                "title": "Federal Reserve Holds Interest Rates Steady",
                "summary": "The Fed keeps rates unchanged as inflation shows signs of cooling.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Reuters",
                    "url": "http://reuters.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/fed-holds-rates",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "content": {
                "contentType": "STORY",
                "title": "FOMC Minutes Reveal Debate on Rate Cuts",
                "summary": "Minutes show committee members divided on timing of rate cuts.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/fomc-minutes-debate",
                },
            },
        },
    ]


@pytest.fixture
def mock_keywords_data() -> dict[str, Any]:
    """Mock news_search_keywords.yaml data structure."""
    return {
        "version": "1.0",
        "macro_keywords": {
            "monetary_policy": [
                "Federal Reserve",
                "Fed interest rate",
                "FOMC",
            ],
            "economic_indicators": [
                "GDP growth",
                "inflation CPI",
                "unemployment rate",
            ],
            "trade": [
                "trade war",
                "tariffs",
            ],
            "global": [
                "ECB monetary policy",
                "Bank of Japan",
            ],
            "market_sentiment": [
                "VIX volatility",
                "market correction",
            ],
        },
        "search_config": {
            "max_results_per_query": 20,
            "combination_method": "single",
            "priority_categories": [
                "monetary_policy",
                "economic_indicators",
                "global",
                "trade",
                "market_sentiment",
            ],
        },
    }


@pytest.fixture
def sample_keywords_file(tmp_path: Path, mock_keywords_data: dict[str, Any]) -> Path:
    """Create a temporary news_search_keywords.yaml file."""
    import yaml

    keywords_file = tmp_path / "news_search_keywords.yaml"
    keywords_file.write_text(
        yaml.dump(mock_keywords_data, allow_unicode=True), encoding="utf-8"
    )
    return keywords_file


# ============================================================================
# Tests for MacroNewsSource
# ============================================================================


class TestMacroNewsSource:
    """Tests for MacroNewsSource class."""

    def test_正常系_source_nameが正しく設定される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that source_name is correctly set."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert source.source_name == "yfinance_search_macro"

    def test_正常系_source_typeが正しく設定される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that source_type is correctly set."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert source.source_type == ArticleSource.YFINANCE_SEARCH

    def test_正常系_キーワードが正しく読み込まれる(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that keywords are correctly loaded from config."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        keywords = source.get_keywords()

        # Should include keywords from all categories
        assert "Federal Reserve" in keywords
        assert "GDP growth" in keywords
        assert "trade war" in keywords
        assert "ECB monetary policy" in keywords
        assert "VIX volatility" in keywords

    def test_正常系_全カテゴリのキーワードが合計される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that keywords from all categories are combined."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        keywords = source.get_keywords()

        # 3 + 3 + 2 + 2 + 2 = 12
        assert len(keywords) == 12

    def test_正常系_カテゴリフィルタでキーワードを絞り込める(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that categories parameter filters keywords."""
        source = MacroNewsSource(
            keywords_file=sample_keywords_file,
            categories=["monetary_policy"],
        )
        keywords = source.get_keywords()

        assert len(keywords) == 3
        assert "Federal Reserve" in keywords
        assert "Fed interest rate" in keywords
        assert "FOMC" in keywords
        # Other categories should not be included
        assert "GDP growth" not in keywords

    def test_正常系_複数カテゴリでフィルタリング(
        self, sample_keywords_file: Path
    ) -> None:
        """Test filtering with multiple categories."""
        source = MacroNewsSource(
            keywords_file=sample_keywords_file,
            categories=["monetary_policy", "trade"],
        )
        keywords = source.get_keywords()

        assert len(keywords) == 5
        assert "Federal Reserve" in keywords
        assert "trade war" in keywords

    def test_正常系_単一クエリでニュース取得(
        self,
        sample_keywords_file: Path,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for a single search query."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search

            result = source.fetch("Federal Reserve", count=10)

        assert result.success is True
        assert result.query == "Federal Reserve"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_SEARCH

    def test_正常系_複数クエリでニュース取得(
        self,
        sample_keywords_file: Path,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for multiple search queries."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search

            results = source.fetch_all(
                ["Federal Reserve", "GDP growth", "trade war"], count=5
            )

        assert len(results) == 3
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].query == "Federal Reserve"
        assert results[1].query == "GDP growth"
        assert results[2].query == "trade war"

    def test_正常系_search_news_to_articleにクエリが渡される(
        self, sample_search_news_data: list[dict[str, Any]]
    ) -> None:
        """Test that query is passed to search_news_to_article function."""
        from news.sources.yfinance.base import search_news_to_article

        article = search_news_to_article(sample_search_news_data[0], "Federal Reserve")

        assert "Federal Reserve" in article.tags
        assert article.title == "Federal Reserve Holds Interest Rates Steady"
        assert article.source == ArticleSource.YFINANCE_SEARCH

    def test_正常系_空の結果で成功(self, sample_keywords_file: Path) -> None:
        """Test successful fetch returning empty results."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        mock_search = MagicMock()
        mock_search.news = []

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search

            result = source.fetch("Federal Reserve", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.query == "Federal Reserve"

    def test_正常系_エラー時は次のクエリへ継続(
        self,
        sample_keywords_file: Path,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that fetch_all continues to next query on error."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        call_count = 0

        def mock_search_factory(query: str, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if query == "Federal Reserve":
                # Simulate error by raising exception when accessing .news
                type(mock).news = property(
                    lambda self: (_ for _ in ()).throw(Exception("API Error"))
                )
            else:
                mock.news = sample_search_news_data
            return mock

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.side_effect = mock_search_factory

            results = source.fetch_all(
                ["Federal Reserve", "GDP growth", "trade war"], count=5
            )

        # Should have results for all 3 queries
        assert len(results) == 3
        # First query should fail but not stop processing
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 2

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        results = source.fetch_all([], count=10)

        assert results == []

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = MacroNewsSource(
            keywords_file=sample_keywords_file,
            retry_config=custom_retry,
        )

        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that default retry config is used when not specified."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 1.0

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        source._retry_config = RetryConfig(max_attempts=1, initial_delay=0.01)

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.side_effect = Exception("Connection error")

            result = source.fetch("Federal Reserve", count=10)

        assert result.success is False
        assert result.error is not None

    def test_正常系_fetch_allは各クエリの結果を順番に返す(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that fetch_all returns results in order."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        queries = ["Federal Reserve", "GDP growth", "trade war"]
        mock_results = [
            FetchResult(articles=[], success=True, query=q) for q in queries
        ]

        with patch.object(source, "fetch", side_effect=mock_results):
            results = source.fetch_all(queries, count=5)

        assert len(results) == 3
        assert results[0].query == "Federal Reserve"
        assert results[1].query == "GDP growth"
        assert results[2].query == "trade war"

    def test_正常系_countパラメータがyfinance_Searchに渡される(
        self,
        sample_keywords_file: Path,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that count parameter is passed to yfinance Search."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.macro.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search

            source.fetch("Federal Reserve", count=5)

            # Verify Search was called with news_count
            mock_yf.Search.assert_called_once_with("Federal Reserve", news_count=5)


class TestMacroNewsSourceProtocol:
    """Tests to verify MacroNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that source_name property exists."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that source_type property exists."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that fetch method exists with correct signature."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(
        self, sample_keywords_file: Path
    ) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self, sample_keywords_file: Path) -> None:
        """Test that MacroNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = MacroNewsSource(keywords_file=sample_keywords_file)
        assert isinstance(source, SourceProtocol)


class TestMacroNewsSourceEmptyData:
    """Tests for MacroNewsSource with empty or missing data sections."""

    def test_正常系_空のmacro_keywordsセクションで空リスト(
        self, tmp_path: Path
    ) -> None:
        """Test that empty macro_keywords section returns empty list."""
        import yaml

        data = {
            "version": "1.0",
            "macro_keywords": {},
            "search_config": {
                "max_results_per_query": 20,
                "combination_method": "single",
            },
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = MacroNewsSource(keywords_file=keywords_file)
        keywords = source.get_keywords()

        assert keywords == []

    def test_正常系_macro_keywordsセクションがない場合空リスト(
        self, tmp_path: Path
    ) -> None:
        """Test that missing macro_keywords section returns empty list."""
        import yaml

        data = {
            "version": "1.0",
            "search_config": {
                "max_results_per_query": 20,
            },
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = MacroNewsSource(keywords_file=keywords_file)
        keywords = source.get_keywords()

        assert keywords == []

    def test_正常系_特定カテゴリのみのキーワードが読み込まれる(
        self, tmp_path: Path
    ) -> None:
        """Test loading keywords from a single category."""
        import yaml

        data = {
            "version": "1.0",
            "macro_keywords": {
                "monetary_policy": [
                    "Federal Reserve",
                    "FOMC",
                ],
            },
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = MacroNewsSource(keywords_file=keywords_file)
        keywords = source.get_keywords()

        assert len(keywords) == 2
        assert "Federal Reserve" in keywords
        assert "FOMC" in keywords

    def test_異常系_存在しないキーワードファイルでFileNotFoundError(
        self, tmp_path: Path
    ) -> None:
        """Test that non-existent keywords file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            MacroNewsSource(keywords_file=tmp_path / "nonexistent.yaml")

    def test_正常系_カテゴリ内の値がリストでない場合スキップ(
        self, tmp_path: Path
    ) -> None:
        """Test that non-list category values are skipped."""
        import yaml

        data = {
            "version": "1.0",
            "macro_keywords": {
                "monetary_policy": "not a list",
                "trade": [
                    "trade war",
                ],
            },
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = MacroNewsSource(keywords_file=keywords_file)
        keywords = source.get_keywords()

        # Only "trade" category should contribute
        assert len(keywords) == 1
        assert "trade war" in keywords
