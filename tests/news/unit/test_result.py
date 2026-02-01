"""Unit tests for FetchResult and RetryConfig in the news package."""

from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.errors import SourceError
from news.core.result import FetchResult, RetryConfig


class TestRetryConfig:
    """Test RetryConfig dataclass."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """RetryConfigをデフォルト値で作成できることを確認。"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == (ConnectionError, TimeoutError)

    def test_正常系_カスタム値で作成できる(self) -> None:
        """RetryConfigをカスタム値で作成できることを確認。"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=(ConnectionError,),
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == (ConnectionError,)

    def test_正常系_イミュータブルである(self) -> None:
        """RetryConfigがイミュータブル（frozen）であることを確認。"""
        config = RetryConfig()

        with pytest.raises(AttributeError, match="cannot assign"):
            config.max_attempts = 10

    def test_正常系_複数の例外タイプを設定できる(self) -> None:
        """RetryConfigに複数の例外タイプを設定できることを確認。"""
        config = RetryConfig(
            retryable_exceptions=(ConnectionError, TimeoutError, OSError),
        )

        assert len(config.retryable_exceptions) == 3
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
        assert OSError in config.retryable_exceptions


class TestFetchResult:
    """Test FetchResult dataclass."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    @pytest.fixture
    def sample_articles(self, sample_article: Article) -> list[Article]:
        """テスト用の複数Articleを提供するフィクスチャ。"""
        return [
            sample_article,
            Article(
                url=HttpUrl("https://finance.yahoo.com/news/test2"),
                title="Test Article 2",
                published_at=datetime(2026, 1, 27, 22, 0, 0, tzinfo=timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            ),
        ]

    def test_正常系_成功結果をtickerで作成できる(
        self,
        sample_articles: list[Article],
    ) -> None:
        """FetchResultを成功結果（ticker）で作成できることを確認。"""
        result = FetchResult(
            articles=sample_articles,
            success=True,
            ticker="AAPL",
        )

        assert result.articles == sample_articles
        assert result.success is True
        assert result.ticker == "AAPL"
        assert result.query is None
        assert result.error is None
        assert result.retry_count == 0

    def test_正常系_成功結果をqueryで作成できる(
        self,
        sample_articles: list[Article],
    ) -> None:
        """FetchResultを成功結果（query）で作成できることを確認。"""
        result = FetchResult(
            articles=sample_articles,
            success=True,
            query="Federal Reserve",
        )

        assert result.articles == sample_articles
        assert result.success is True
        assert result.ticker is None
        assert result.query == "Federal Reserve"
        assert result.error is None
        assert result.retry_count == 0

    def test_正常系_失敗結果を作成できる(self) -> None:
        """FetchResultを失敗結果で作成できることを確認。"""
        error = SourceError(
            message="Connection timeout",
            source="yfinance",
            ticker="AAPL",
            retryable=True,
        )
        result = FetchResult(
            articles=[],
            success=False,
            ticker="AAPL",
            error=error,
            retry_count=3,
        )

        assert result.articles == []
        assert result.success is False
        assert result.ticker == "AAPL"
        assert result.error is error
        assert result.retry_count == 3

    def test_正常系_fetched_atが自動設定される(
        self,
        sample_articles: list[Article],
    ) -> None:
        """fetched_atが自動的に現在時刻に設定されることを確認。"""
        before = datetime.now(timezone.utc)
        result = FetchResult(
            articles=sample_articles,
            success=True,
            ticker="AAPL",
        )
        after = datetime.now(timezone.utc)

        assert result.fetched_at is not None
        # fetched_at が before と after の間にあることを確認
        fetched_at_utc = (
            result.fetched_at.replace(tzinfo=timezone.utc)
            if result.fetched_at.tzinfo is None
            else result.fetched_at
        )
        assert before <= fetched_at_utc <= after


class TestFetchResultProperties:
    """Test FetchResult computed properties."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    def test_正常系_article_countが正しく計算される(
        self,
        sample_article: Article,
    ) -> None:
        """article_countが正しく計算されることを確認。"""
        result = FetchResult(
            articles=[sample_article, sample_article],
            success=True,
            ticker="AAPL",
        )

        assert result.article_count == 2

    def test_正常系_空の場合article_countは0(self) -> None:
        """空の場合article_countが0であることを確認。"""
        result = FetchResult(
            articles=[],
            success=True,
            ticker="AAPL",
        )

        assert result.article_count == 0

    def test_正常系_is_emptyが正しく判定される(
        self,
        sample_article: Article,
    ) -> None:
        """is_emptyが正しく判定されることを確認。"""
        result_with_articles = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
        )
        result_empty = FetchResult(
            articles=[],
            success=True,
            ticker="AAPL",
        )

        assert result_with_articles.is_empty is False
        assert result_empty.is_empty is True

    def test_正常系_source_identifierがtickerを返す(
        self,
        sample_article: Article,
    ) -> None:
        """source_identifierがtickerを返すことを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
        )

        assert result.source_identifier == "AAPL"

    def test_正常系_source_identifierがqueryを返す(
        self,
        sample_article: Article,
    ) -> None:
        """source_identifierがqueryを返すことを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
            query="Federal Reserve",
        )

        assert result.source_identifier == "Federal Reserve"

    def test_正常系_source_identifierがtickerを優先する(
        self,
        sample_article: Article,
    ) -> None:
        """tickerとqueryの両方がある場合、tickerを優先することを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
            query="Apple Inc",
        )

        assert result.source_identifier == "AAPL"

    def test_正常系_source_identifierがunknownを返す(
        self,
        sample_article: Article,
    ) -> None:
        """tickerとqueryの両方がない場合、unknownを返すことを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
        )

        assert result.source_identifier == "unknown"


class TestFetchResultEdgeCases:
    """Test FetchResult edge cases."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    def test_エッジケース_大量の記事でも正常動作(
        self,
        sample_article: Article,
    ) -> None:
        """大量の記事を含む場合でも正常に動作することを確認。"""
        many_articles = [sample_article for _ in range(1000)]
        result = FetchResult(
            articles=many_articles,
            success=True,
            ticker="AAPL",
        )

        assert result.article_count == 1000
        assert result.is_empty is False

    def test_エッジケース_retry_countが大きい値でも正常動作(
        self,
        sample_article: Article,
    ) -> None:
        """retry_countが大きい値でも正常に動作することを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
            retry_count=100,
        )

        assert result.retry_count == 100

    def test_エッジケース_空文字のtickerでも正常動作(
        self,
        sample_article: Article,
    ) -> None:
        """空文字のtickerでも正常に動作することを確認。"""
        result = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="",
        )

        # 空文字は falsy なので source_identifier は unknown になる
        assert result.source_identifier == "unknown"

    def test_エッジケース_成功だがエラーありの不整合状態(
        self,
        sample_article: Article,
    ) -> None:
        """success=True だが error がある不整合状態でも作成できることを確認。"""
        # 注: これは不整合な状態だが、dataclass では制約しない
        error = SourceError(message="Test error", source="test")
        result = FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
            error=error,
        )

        assert result.success is True
        assert result.error is not None


class TestRetryConfigEdgeCases:
    """Test RetryConfig edge cases."""

    def test_エッジケース_max_attemptsが0でも作成できる(self) -> None:
        """max_attemptsが0でも作成できることを確認。"""
        config = RetryConfig(max_attempts=0)
        assert config.max_attempts == 0

    def test_エッジケース_delayが0でも作成できる(self) -> None:
        """initial_delayが0でも作成できることを確認。"""
        config = RetryConfig(initial_delay=0.0)
        assert config.initial_delay == 0.0

    def test_エッジケース_空の例外タプルでも作成できる(self) -> None:
        """空の例外タプルでも作成できることを確認。"""
        config = RetryConfig(retryable_exceptions=())
        assert config.retryable_exceptions == ()
