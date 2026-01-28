"""Tests for yfinance search news source module.

This module provides unit tests for the SearchNewsSource class that fetches
theme-based news using yfinance Search API with keyword-based queries.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig
from news.sources.yfinance.search import SearchNewsSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_search_news_data() -> list[dict[str, Any]]:
    """Sample yfinance Search.news data for keyword search."""
    return [
        {
            "id": "aaa00000-e29b-41d4-a716-000000000001",
            "content": {
                "contentType": "STORY",
                "title": "AI Stocks Surge on New Chip Breakthrough",
                "summary": "AI-related stocks rally as new chip technology is announced.",
                "pubDate": "2026-01-28T15:00:00Z",
                "provider": {
                    "displayName": "Reuters",
                    "url": "http://reuters.com/",
                },
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/ai-stocks-surge",
                    "region": "US",
                    "lang": "en-US",
                },
            },
        },
        {
            "id": "bbb00000-e29b-41d4-a716-000000000002",
            "content": {
                "contentType": "STORY",
                "title": "Semiconductor Shortage Worsens in Q1",
                "summary": "Global semiconductor supply chain faces further disruptions.",
                "pubDate": "2026-01-28T14:00:00Z",
                "canonicalUrl": {
                    "url": "https://finance.yahoo.com/news/semiconductor-shortage",
                },
            },
        },
    ]


@pytest.fixture
def mock_keywords_data() -> dict[str, Any]:
    """Mock keywords YAML data structure with multiple categories."""
    return {
        "version": "1.0",
        "search_keywords": {
            "tech": [
                "AI stocks",
                "semiconductor shortage",
                "cloud computing",
            ],
            "energy": [
                "EV market",
                "solar energy",
            ],
            "biotech": [
                "gene therapy",
                "biotech IPO",
            ],
        },
        "search_config": {
            "max_results_per_query": 20,
            "combination_method": "single",
        },
    }


@pytest.fixture
def sample_keywords_file(tmp_path: Path, mock_keywords_data: dict[str, Any]) -> Path:
    """Create a temporary keywords YAML file."""
    import yaml

    keywords_file = tmp_path / "search_keywords.yaml"
    keywords_file.write_text(
        yaml.dump(mock_keywords_data, allow_unicode=True), encoding="utf-8"
    )
    return keywords_file


# ============================================================================
# Tests for SearchNewsSource (direct keywords)
# ============================================================================


class TestSearchNewsSourceDirect:
    """Tests for SearchNewsSource with direct keyword list."""

    def test_正常系_直接キーワードリストで初期化(self) -> None:
        """Test initialization with direct keyword list."""
        source = SearchNewsSource(keywords=["AI stocks", "semiconductor shortage"])
        keywords = source.get_keywords()

        assert len(keywords) == 2
        assert "AI stocks" in keywords
        assert "semiconductor shortage" in keywords

    def test_正常系_source_nameが正しく設定される(self) -> None:
        """Test that source_name is correctly set."""
        source = SearchNewsSource(keywords=["AI stocks"])
        assert source.source_name == "yfinance_search"

    def test_正常系_source_typeが正しく設定される(self) -> None:
        """Test that source_type is correctly set."""
        source = SearchNewsSource(keywords=["AI stocks"])
        assert source.source_type == ArticleSource.YFINANCE_SEARCH

    def test_正常系_単一クエリでニュース取得(
        self,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for a single search query."""
        source = SearchNewsSource(keywords=["AI stocks"])

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search
            result = source.fetch("AI stocks", count=10)

        assert result.success is True
        assert result.query == "AI stocks"
        assert result.article_count == 2
        assert all(isinstance(a, Article) for a in result.articles)
        assert result.articles[0].source == ArticleSource.YFINANCE_SEARCH

    def test_正常系_複数クエリでニュース取得(
        self,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test fetching news for multiple search queries."""
        source = SearchNewsSource(
            keywords=["AI stocks", "semiconductor shortage", "cloud computing"]
        )

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search
            results = source.fetch_all(
                ["AI stocks", "semiconductor shortage", "cloud computing"],
                count=5,
            )

        assert len(results) == 3
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].query == "AI stocks"
        assert results[1].query == "semiconductor shortage"
        assert results[2].query == "cloud computing"

    def test_正常系_空の結果で成功(self) -> None:
        """Test successful fetch returning empty results."""
        source = SearchNewsSource(keywords=["AI stocks"])

        mock_search = MagicMock()
        mock_search.news = []

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search
            result = source.fetch("AI stocks", count=10)

        assert result.success is True
        assert result.is_empty is True
        assert result.query == "AI stocks"

    def test_正常系_エラー時は次のクエリへ継続(
        self,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that fetch_all continues to next query on error."""
        source = SearchNewsSource(
            keywords=["AI stocks", "semiconductor shortage", "cloud computing"]
        )

        def mock_search_factory(query: str, **kwargs: Any) -> MagicMock:
            mock = MagicMock()
            if query == "AI stocks":
                type(mock).news = property(
                    lambda self: (_ for _ in ()).throw(Exception("API Error"))
                )
            else:
                mock.news = sample_search_news_data
            return mock

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.side_effect = mock_search_factory
            results = source.fetch_all(
                ["AI stocks", "semiconductor shortage", "cloud computing"],
                count=5,
            )

        assert len(results) == 3
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 2

    def test_正常系_fetch_allで空のリストを渡すと空のリストを返す(self) -> None:
        """Test that fetch_all with empty list returns empty list."""
        source = SearchNewsSource(keywords=["AI stocks"])
        results = source.fetch_all([], count=10)
        assert results == []

    def test_正常系_fetchでエラー時はsuccess_falseの結果を返す(self) -> None:
        """Test that fetch returns success=False when an error occurs."""
        source = SearchNewsSource(keywords=["AI stocks"])
        source._retry_config = RetryConfig(max_attempts=1, initial_delay=0.01)

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.side_effect = Exception("Connection error")
            result = source.fetch("AI stocks", count=10)

        assert result.success is False
        assert result.error is not None

    def test_正常系_countパラメータがyfinance_Searchに渡される(
        self,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that count parameter is passed to yfinance Search."""
        source = SearchNewsSource(keywords=["AI stocks"])

        mock_search = MagicMock()
        mock_search.news = sample_search_news_data

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search
            source.fetch("AI stocks", count=5)
            mock_yf.Search.assert_called_once_with("AI stocks", news_count=5)

    def test_正常系_カスタムリトライ設定が適用される(self) -> None:
        """Test that custom retry config is applied."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = SearchNewsSource(
            keywords=["AI stocks"],
            retry_config=custom_retry,
        )
        assert source._retry_config.max_attempts == 5
        assert source._retry_config.initial_delay == 0.5

    def test_正常系_デフォルトリトライ設定が適用される(self) -> None:
        """Test that default retry config is used when not specified."""
        source = SearchNewsSource(keywords=["AI stocks"])
        assert source._retry_config.max_attempts == 3
        assert source._retry_config.initial_delay == 1.0

    def test_正常系_get_keywordsはコピーを返す(self) -> None:
        """Test that get_keywords returns a copy of the keywords list."""
        keywords = ["AI stocks", "semiconductor shortage"]
        source = SearchNewsSource(keywords=keywords)
        returned = source.get_keywords()

        # Modifying the returned list should not affect the source
        returned.append("extra")
        assert len(source.get_keywords()) == 2

    def test_異常系_空のキーワードリストで初期化(self) -> None:
        """Test initialization with empty keyword list."""
        source = SearchNewsSource(keywords=[])
        assert source.get_keywords() == []


# ============================================================================
# Tests for SearchNewsSource.from_config
# ============================================================================


class TestSearchNewsSourceFromConfig:
    """Tests for SearchNewsSource.from_config class method."""

    def test_正常系_設定ファイルから全カテゴリのキーワードを読み込む(
        self, sample_keywords_file: Path
    ) -> None:
        """Test loading all categories from config file."""
        source = SearchNewsSource.from_config(
            sample_keywords_file,
            section="search_keywords",
        )
        keywords = source.get_keywords()

        assert "AI stocks" in keywords
        assert "semiconductor shortage" in keywords
        assert "cloud computing" in keywords
        assert "EV market" in keywords
        assert "solar energy" in keywords
        assert "gene therapy" in keywords
        assert "biotech IPO" in keywords
        assert len(keywords) == 7

    def test_正常系_カテゴリフィルタでキーワードを絞り込める(
        self, sample_keywords_file: Path
    ) -> None:
        """Test filtering keywords by category."""
        source = SearchNewsSource.from_config(
            sample_keywords_file,
            section="search_keywords",
            category="tech",
        )
        keywords = source.get_keywords()

        assert len(keywords) == 3
        assert "AI stocks" in keywords
        assert "semiconductor shortage" in keywords
        assert "cloud computing" in keywords
        assert "EV market" not in keywords

    def test_正常系_複数カテゴリでフィルタリング(
        self, sample_keywords_file: Path
    ) -> None:
        """Test filtering with multiple categories."""
        source = SearchNewsSource.from_config(
            sample_keywords_file,
            section="search_keywords",
            categories=["tech", "energy"],
        )
        keywords = source.get_keywords()

        assert len(keywords) == 5
        assert "AI stocks" in keywords
        assert "EV market" in keywords
        assert "gene therapy" not in keywords

    def test_異常系_存在しないファイルでFileNotFoundError(self, tmp_path: Path) -> None:
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            SearchNewsSource.from_config(
                tmp_path / "nonexistent.yaml",
                section="search_keywords",
            )

    def test_正常系_空のセクションで空のキーワードリスト(self, tmp_path: Path) -> None:
        """Test empty section returns empty keyword list."""
        import yaml

        data = {
            "version": "1.0",
            "search_keywords": {},
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = SearchNewsSource.from_config(
            keywords_file,
            section="search_keywords",
        )
        assert source.get_keywords() == []

    def test_正常系_存在しないセクションで空のキーワードリスト(
        self, tmp_path: Path
    ) -> None:
        """Test non-existent section returns empty keyword list."""
        import yaml

        data = {
            "version": "1.0",
            "other_section": {"tech": ["AI stocks"]},
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = SearchNewsSource.from_config(
            keywords_file,
            section="search_keywords",
        )
        assert source.get_keywords() == []

    def test_正常系_カスタムリトライ設定が適用される(
        self, sample_keywords_file: Path
    ) -> None:
        """Test custom retry config is applied via from_config."""
        custom_retry = RetryConfig(max_attempts=5, initial_delay=0.5)
        source = SearchNewsSource.from_config(
            sample_keywords_file,
            section="search_keywords",
            retry_config=custom_retry,
        )
        assert source._retry_config.max_attempts == 5

    def test_正常系_カテゴリ内の値がリストでない場合スキップ(
        self, tmp_path: Path
    ) -> None:
        """Test that non-list category values are skipped."""
        import yaml

        data = {
            "version": "1.0",
            "search_keywords": {
                "tech": "not a list",
                "energy": ["EV market"],
            },
        }
        keywords_file = tmp_path / "keywords.yaml"
        keywords_file.write_text(yaml.dump(data), encoding="utf-8")

        source = SearchNewsSource.from_config(
            keywords_file,
            section="search_keywords",
        )
        keywords = source.get_keywords()

        assert len(keywords) == 1
        assert "EV market" in keywords


# ============================================================================
# Tests for SourceProtocol compliance
# ============================================================================


class TestSearchNewsSourceProtocol:
    """Tests to verify SearchNewsSource implements SourceProtocol."""

    def test_プロトコル準拠_source_nameプロパティが存在(self) -> None:
        """Test that source_name property exists."""
        source = SearchNewsSource(keywords=["test"])
        assert hasattr(source, "source_name")
        assert isinstance(source.source_name, str)

    def test_プロトコル準拠_source_typeプロパティが存在(self) -> None:
        """Test that source_type property exists."""
        source = SearchNewsSource(keywords=["test"])
        assert hasattr(source, "source_type")
        assert isinstance(source.source_type, ArticleSource)

    def test_プロトコル準拠_fetchメソッドが存在(self) -> None:
        """Test that fetch method exists with correct signature."""
        source = SearchNewsSource(keywords=["test"])
        assert hasattr(source, "fetch")
        assert callable(source.fetch)

    def test_プロトコル準拠_fetch_allメソッドが存在(self) -> None:
        """Test that fetch_all method exists with correct signature."""
        source = SearchNewsSource(keywords=["test"])
        assert hasattr(source, "fetch_all")
        assert callable(source.fetch_all)

    def test_プロトコル準拠_isinstance_check(self) -> None:
        """Test that SearchNewsSource passes SourceProtocol isinstance check."""
        from news.core.source import SourceProtocol

        source = SearchNewsSource(keywords=["test"])
        assert isinstance(source, SourceProtocol)


# ============================================================================
# Tests for search_news_to_article integration
# ============================================================================


class TestSearchNewsToArticleIntegration:
    """Tests for search_news_to_article conversion within SearchNewsSource."""

    def test_正常系_検索クエリがタグに追加される(
        self,
        sample_search_news_data: list[dict[str, Any]],
    ) -> None:
        """Test that search query is added as a tag."""
        from news.sources.yfinance.base import search_news_to_article

        article = search_news_to_article(sample_search_news_data[0], "AI stocks")
        assert "AI stocks" in article.tags
        assert article.source == ArticleSource.YFINANCE_SEARCH

    def test_正常系_変換失敗した記事はスキップされる(self) -> None:
        """Test that articles failing conversion are skipped."""
        source = SearchNewsSource(keywords=["AI stocks"])

        # Include one valid and one invalid news item
        news_data = [
            {
                "content": {
                    "title": "Valid Article",
                    "pubDate": "2026-01-28T15:00:00Z",
                    "canonicalUrl": {
                        "url": "https://finance.yahoo.com/news/valid",
                    },
                },
            },
            {
                "content": {
                    # Missing title - should cause conversion failure
                },
            },
        ]

        mock_search = MagicMock()
        mock_search.news = news_data

        with patch("news.sources.yfinance.search.yf") as mock_yf:
            mock_yf.Search.return_value = mock_search
            result = source.fetch("AI stocks", count=10)

        assert result.success is True
        assert result.article_count == 1
        assert result.articles[0].title == "Valid Article"
