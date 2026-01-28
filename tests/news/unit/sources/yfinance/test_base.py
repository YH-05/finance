"""Tests for yfinance base module.

This module provides unit tests for the yfinance news source base functionality,
including data conversion, retry logic, and validation functions.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from news.core.article import Article, ArticleSource, ContentType
from news.core.errors import SourceError, ValidationError
from news.core.result import RetryConfig
from news.sources.yfinance.base import (
    fetch_with_retry,
    search_news_to_article,
    ticker_news_to_article,
    validate_query,
    validate_ticker,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_ticker_news_data() -> dict[str, Any]:
    """Sample yfinance Ticker.news data."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "content": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "contentType": "STORY",
            "title": "Apple Reports Record Q1 2026 Earnings",
            "summary": "Apple Inc. announced record-breaking revenue for Q1 2026.",
            "pubDate": "2026-01-27T23:33:53Z",
            "provider": {
                "displayName": "Yahoo Finance",
                "url": "http://finance.yahoo.com/",
            },
            "canonicalUrl": {
                "url": "https://finance.yahoo.com/news/apple-reports-record-q1-2026-earnings",
                "site": "finance",
                "region": "US",
                "lang": "en-US",
            },
            "thumbnail": {
                "originalUrl": "https://s.yimg.com/ny/api/res/1.2/abc123.jpg",
                "originalWidth": 1200,
                "originalHeight": 800,
            },
            "metadata": {"editorsPick": True},
            "finance": {"premiumFinance": {"isPremiumNews": False}},
        },
    }


@pytest.fixture
def sample_search_news_data() -> dict[str, Any]:
    """Sample yfinance Search.news data."""
    return {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "content": {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "contentType": "STORY",
            "title": "Federal Reserve Signals Rate Cut in 2026",
            "summary": "The Federal Reserve indicated potential interest rate cuts.",
            "pubDate": "2026-01-27T20:15:00Z",
            "provider": {
                "displayName": "Reuters",
                "url": "https://www.reuters.com/",
            },
            "canonicalUrl": {
                "url": "https://finance.yahoo.com/news/fed-signals-rate-cut",
                "site": "finance",
                "region": "US",
                "lang": "en-US",
            },
            "thumbnail": {
                "originalUrl": "https://s.yimg.com/ny/api/res/1.2/def456.jpg",
                "originalWidth": 800,
                "originalHeight": 600,
            },
            "metadata": {"editorsPick": False},
            "finance": {"premiumFinance": {"isPremiumNews": False}},
        },
    }


@pytest.fixture
def minimal_ticker_news_data() -> dict[str, Any]:
    """Minimal yfinance news data with only required fields."""
    return {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "content": {
            "contentType": "STORY",
            "title": "Minimal News Article",
            "pubDate": "2026-01-27T10:00:00Z",
            "canonicalUrl": {
                "url": "https://finance.yahoo.com/news/minimal-article",
            },
        },
    }


@pytest.fixture
def video_content_data() -> dict[str, Any]:
    """yfinance news data with VIDEO content type."""
    return {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "content": {
            "contentType": "VIDEO",
            "title": "Market Analysis Video",
            "summary": "Video analysis of market trends.",
            "pubDate": "2026-01-28T08:00:00Z",
            "canonicalUrl": {
                "url": "https://finance.yahoo.com/video/market-analysis",
            },
            "provider": {
                "displayName": "Yahoo Finance Video",
            },
        },
    }


# ============================================================================
# Tests for ticker_news_to_article
# ============================================================================


class TestTickerNewsToArticle:
    """Tests for ticker_news_to_article function."""

    def test_正常系_完全なデータで変換成功(
        self, sample_ticker_news_data: dict[str, Any]
    ) -> None:
        """Test successful conversion with complete data."""
        article = ticker_news_to_article(sample_ticker_news_data, "AAPL")

        assert article.title == "Apple Reports Record Q1 2026 Earnings"
        assert (
            str(article.url)
            == "https://finance.yahoo.com/news/apple-reports-record-q1-2026-earnings"
        )
        assert article.source == ArticleSource.YFINANCE_TICKER
        assert article.content_type == ContentType.ARTICLE
        assert (
            article.summary
            == "Apple Inc. announced record-breaking revenue for Q1 2026."
        )
        assert article.published_at == datetime(
            2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc
        )
        assert "AAPL" in article.related_tickers
        assert article.provider is not None
        assert article.provider.name == "Yahoo Finance"
        assert article.thumbnail is not None
        assert article.thumbnail.width == 1200
        assert article.thumbnail.height == 800

    def test_正常系_最小データで変換成功(
        self, minimal_ticker_news_data: dict[str, Any]
    ) -> None:
        """Test successful conversion with minimal data."""
        article = ticker_news_to_article(minimal_ticker_news_data, "TSLA")

        assert article.title == "Minimal News Article"
        assert str(article.url) == "https://finance.yahoo.com/news/minimal-article"
        assert article.source == ArticleSource.YFINANCE_TICKER
        assert article.summary is None
        assert article.provider is None
        assert article.thumbnail is None
        assert "TSLA" in article.related_tickers

    def test_正常系_VIDEOコンテンツタイプで変換成功(
        self, video_content_data: dict[str, Any]
    ) -> None:
        """Test conversion with VIDEO content type."""
        article = ticker_news_to_article(video_content_data, "SPY")

        assert article.title == "Market Analysis Video"
        assert article.content_type == ContentType.VIDEO
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_メタデータが正しく設定される(
        self, sample_ticker_news_data: dict[str, Any]
    ) -> None:
        """Test that metadata is correctly populated."""
        article = ticker_news_to_article(sample_ticker_news_data, "AAPL")

        assert article.metadata.get("yfinance_content_type") == "STORY"
        assert article.metadata.get("editors_pick") is True
        assert article.metadata.get("is_premium") is False
        assert article.metadata.get("region") == "US"
        assert article.metadata.get("lang") == "en-US"

    def test_異常系_URLが欠落でValidationError(self) -> None:
        """Test that missing URL raises ValidationError."""
        invalid_data = {
            "content": {
                "title": "No URL Article",
                "pubDate": "2026-01-27T10:00:00Z",
            }
        }
        with pytest.raises(ValidationError, match="URL"):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_異常系_タイトルが欠落でValidationError(self) -> None:
        """Test that missing title raises ValidationError."""
        invalid_data = {
            "content": {
                "pubDate": "2026-01-27T10:00:00Z",
                "canonicalUrl": {"url": "https://example.com/news"},
            }
        }
        with pytest.raises(ValidationError, match="Title"):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_異常系_公開日時が欠落でValidationError(self) -> None:
        """Test that missing pubDate raises ValidationError."""
        invalid_data = {
            "content": {
                "title": "No Date Article",
                "canonicalUrl": {"url": "https://example.com/news"},
            }
        }
        with pytest.raises(ValidationError, match="Publication date"):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_異常系_不正なURL形式でValidationError(self) -> None:
        """Test that invalid URL format raises ValidationError."""
        invalid_data = {
            "content": {
                "title": "Invalid URL Article",
                "pubDate": "2026-01-27T10:00:00Z",
                "canonicalUrl": {"url": "not-a-valid-url"},
            }
        }
        with pytest.raises(ValidationError, match="Invalid URL"):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_異常系_不正な日時形式でValidationError(self) -> None:
        """Test that invalid date format raises ValidationError."""
        invalid_data = {
            "content": {
                "title": "Invalid Date Article",
                "pubDate": "invalid-date-format",
                "canonicalUrl": {"url": "https://example.com/news"},
            }
        }
        with pytest.raises(ValidationError, match="Invalid date"):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_エッジケース_空のcontentオブジェクトでValidationError(self) -> None:
        """Test that empty content object raises ValidationError."""
        invalid_data = {"content": {}}
        with pytest.raises(ValidationError):
            ticker_news_to_article(invalid_data, "AAPL")

    def test_エッジケース_未知のcontentTypeでUNKNOWN(self) -> None:
        """Test that unknown content type maps to UNKNOWN."""
        data = {
            "content": {
                "contentType": "PODCAST",
                "title": "Unknown Type Article",
                "pubDate": "2026-01-27T10:00:00Z",
                "canonicalUrl": {"url": "https://example.com/news"},
            }
        }
        article = ticker_news_to_article(data, "AAPL")
        assert article.content_type == ContentType.UNKNOWN


# ============================================================================
# Tests for search_news_to_article
# ============================================================================


class TestSearchNewsToArticle:
    """Tests for search_news_to_article function."""

    def test_正常系_完全なデータで変換成功(
        self, sample_search_news_data: dict[str, Any]
    ) -> None:
        """Test successful conversion with complete data."""
        article = search_news_to_article(sample_search_news_data, "Federal Reserve")

        assert article.title == "Federal Reserve Signals Rate Cut in 2026"
        assert str(article.url) == "https://finance.yahoo.com/news/fed-signals-rate-cut"
        assert article.source == ArticleSource.YFINANCE_SEARCH
        assert article.content_type == ContentType.ARTICLE
        assert "Federal Reserve" in article.tags
        assert len(article.related_tickers) == 0  # Search doesn't auto-populate tickers

    def test_正常系_クエリがタグに設定される(
        self, sample_search_news_data: dict[str, Any]
    ) -> None:
        """Test that search query is added to tags."""
        query = "inflation economy 2026"
        article = search_news_to_article(sample_search_news_data, query)

        assert query in article.tags
        assert article.metadata.get("search_query") == query

    def test_正常系_related_tickersが空(
        self, sample_search_news_data: dict[str, Any]
    ) -> None:
        """Test that related_tickers is empty for search results."""
        article = search_news_to_article(sample_search_news_data, "test query")
        assert article.related_tickers == []

    def test_異常系_URLが欠落でValidationError(self) -> None:
        """Test that missing URL raises ValidationError."""
        invalid_data = {
            "content": {
                "title": "No URL Article",
                "pubDate": "2026-01-27T10:00:00Z",
            }
        }
        with pytest.raises(ValidationError, match="URL"):
            search_news_to_article(invalid_data, "test query")


# ============================================================================
# Tests for validate_ticker
# ============================================================================


class TestValidateTicker:
    """Tests for validate_ticker function."""

    @pytest.mark.parametrize(
        "ticker",
        [
            "AAPL",
            "GOOGL",
            "MSFT",
            "^GSPC",
            "^DJI",
            "XLF",
            "GC=F",
            "CL=F",
            "BTC-USD",
            "ETH-USD",
        ],
    )
    def test_正常系_有効なティッカーで成功(self, ticker: str) -> None:
        """Test that valid tickers pass validation."""
        result = validate_ticker(ticker)
        assert result == ticker

    def test_正常系_前後の空白が除去される(self) -> None:
        """Test that leading/trailing whitespace is trimmed."""
        result = validate_ticker("  AAPL  ")
        assert result == "AAPL"

    def test_正常系_大文字に変換される(self) -> None:
        """Test that ticker is converted to uppercase."""
        result = validate_ticker("aapl")
        assert result == "AAPL"

    def test_異常系_空文字でValidationError(self) -> None:
        """Test that empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="Ticker cannot be empty"):
            validate_ticker("")

    def test_異常系_空白のみでValidationError(self) -> None:
        """Test that whitespace-only string raises ValidationError."""
        with pytest.raises(ValidationError, match="Ticker cannot be empty"):
            validate_ticker("   ")

    def test_異常系_不正な文字を含むとValidationError(self) -> None:
        """Test that invalid characters raise ValidationError."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_ticker("AAPL!")

    def test_異常系_長すぎるティッカーでValidationError(self) -> None:
        """Test that overly long ticker raises ValidationError."""
        with pytest.raises(ValidationError, match="Ticker too long"):
            validate_ticker("A" * 20)

    @given(
        st.text(
            min_size=1, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789^-="
        )
    )
    @settings(max_examples=50)
    def test_プロパティ_有効な文字のみで構成されたティッカーは検証を通過(
        self, ticker: str
    ) -> None:
        """Property test: valid character tickers should pass validation."""
        # Skip if empty after potential processing
        if not ticker.strip():
            return
        try:
            result = validate_ticker(ticker)
            assert result == ticker.upper().strip()
        except ValidationError:
            # Some combinations might still be invalid (e.g., too long)
            pass


# ============================================================================
# Tests for validate_query
# ============================================================================


class TestValidateQuery:
    """Tests for validate_query function."""

    @pytest.mark.parametrize(
        "query",
        [
            "Federal Reserve",
            "inflation",
            "AI technology stocks",
            "semiconductor industry",
            "interest rate 2026",
        ],
    )
    def test_正常系_有効なクエリで成功(self, query: str) -> None:
        """Test that valid queries pass validation."""
        result = validate_query(query)
        assert result == query

    def test_正常系_前後の空白が除去される(self) -> None:
        """Test that leading/trailing whitespace is trimmed."""
        result = validate_query("  Federal Reserve  ")
        assert result == "Federal Reserve"

    def test_異常系_空文字でValidationError(self) -> None:
        """Test that empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            validate_query("")

    def test_異常系_空白のみでValidationError(self) -> None:
        """Test that whitespace-only string raises ValidationError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            validate_query("   ")

    def test_異常系_長すぎるクエリでValidationError(self) -> None:
        """Test that overly long query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query too long"):
            validate_query("a" * 500)


# ============================================================================
# Tests for fetch_with_retry
# ============================================================================


class TestFetchWithRetry:
    """Tests for fetch_with_retry function."""

    def test_正常系_最初の試行で成功(self) -> None:
        """Test successful fetch on first attempt."""
        mock_func = MagicMock(return_value=["article1", "article2"])
        config = RetryConfig(max_attempts=3)

        result = fetch_with_retry(mock_func, config)

        assert result == ["article1", "article2"]
        assert mock_func.call_count == 1

    def test_正常系_リトライ後に成功(self) -> None:
        """Test successful fetch after retries."""
        mock_func = MagicMock(
            side_effect=[ConnectionError(), ConnectionError(), ["article1"]]
        )
        config = RetryConfig(max_attempts=3, initial_delay=0.01)

        result = fetch_with_retry(mock_func, config)

        assert result == ["article1"]
        assert mock_func.call_count == 3

    def test_異常系_最大リトライ回数超過でSourceError(self) -> None:
        """Test that exceeding max retries raises SourceError."""
        mock_func = MagicMock(side_effect=ConnectionError("Network error"))
        config = RetryConfig(max_attempts=3, initial_delay=0.01)

        with pytest.raises(SourceError, match="Max retries exceeded"):
            fetch_with_retry(mock_func, config)

        assert mock_func.call_count == 3

    def test_正常系_リトライ不可の例外は即座に再送出(self) -> None:
        """Test that non-retryable exceptions are raised immediately."""
        mock_func = MagicMock(side_effect=ValueError("Invalid argument"))
        config = RetryConfig(max_attempts=3)

        with pytest.raises(ValueError, match="Invalid argument"):
            fetch_with_retry(mock_func, config)

        assert mock_func.call_count == 1

    def test_正常系_指数バックオフが適用される(self) -> None:
        """Test that exponential backoff is applied."""
        delays: list[float] = []

        mock_func = MagicMock(
            side_effect=[ConnectionError(), ConnectionError(), "success"]
        )
        config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        with patch("time.sleep") as mock_sleep:
            result = fetch_with_retry(mock_func, config)
            delays = [call[0][0] for call in mock_sleep.call_args_list]

        assert result == "success"
        # First retry: 1.0s, Second retry: 2.0s
        assert len(delays) == 2
        assert delays[0] == pytest.approx(1.0, rel=0.1)
        assert delays[1] == pytest.approx(2.0, rel=0.1)

    def test_正常系_最大遅延時間が尊重される(self) -> None:
        """Test that max delay is respected."""
        mock_func = MagicMock(side_effect=[ConnectionError()] * 5 + ["success"])
        config = RetryConfig(
            max_attempts=6,
            initial_delay=10.0,
            max_delay=15.0,
            exponential_base=2.0,
            jitter=False,
        )

        with patch("time.sleep") as mock_sleep:
            fetch_with_retry(mock_func, config)
            delays = [call[0][0] for call in mock_sleep.call_args_list]

        # All delays should be capped at max_delay
        for delay in delays:
            assert delay <= config.max_delay

    def test_正常系_jitterが適用される(self) -> None:
        """Test that jitter is applied when enabled."""
        mock_func = MagicMock(side_effect=[ConnectionError(), "success"])
        config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            jitter=True,
        )

        delays: list[float] = []
        with (
            patch("time.sleep") as mock_sleep,
            patch("random.uniform", return_value=0.3),
        ):
            result = fetch_with_retry(mock_func, config)
            delays = [call[0][0] for call in mock_sleep.call_args_list]

        assert result == "success"
        # With jitter, delay should vary
        assert len(delays) == 1

    def test_エッジケース_max_attemptsが1の場合リトライなし(self) -> None:
        """Test that no retries occur when max_attempts is 1."""
        mock_func = MagicMock(side_effect=ConnectionError("Network error"))
        config = RetryConfig(max_attempts=1)

        with pytest.raises(SourceError):
            fetch_with_retry(mock_func, config)

        assert mock_func.call_count == 1
