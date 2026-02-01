"""Unit tests for SourceProtocol in the news package.

Tests for the SourceProtocol that defines the interface for news data sources.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Protocol

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.result import FetchResult
from news.core.source import SourceProtocol


class TestSourceProtocolDefinition:
    """Test SourceProtocol definition and structure."""

    def test_正常系_Protocolクラスとして定義されている(self) -> None:
        """SourceProtocolがProtocolクラスとして定義されていることを確認。"""
        assert issubclass(SourceProtocol, Protocol)

    def test_正常系_runtime_checkableである(self) -> None:
        """SourceProtocolがruntime_checkableであることを確認。"""
        # runtime_checkable デコレータが適用されていればisinstanceチェックが可能
        assert hasattr(SourceProtocol, "_is_protocol")
        assert SourceProtocol._is_protocol is True


class TestSourceProtocolProperties:
    """Test SourceProtocol required properties."""

    def test_正常系_source_nameプロパティが必須(self) -> None:
        """source_nameプロパティが定義されていることを確認。"""
        # Protocol のメソッド/プロパティを確認
        assert "source_name" in dir(SourceProtocol)

    def test_正常系_source_typeプロパティが必須(self) -> None:
        """source_typeプロパティが定義されていることを確認。"""
        assert "source_type" in dir(SourceProtocol)


class TestSourceProtocolMethods:
    """Test SourceProtocol required methods."""

    def test_正常系_fetchメソッドが必須(self) -> None:
        """fetchメソッドが定義されていることを確認。"""
        assert "fetch" in dir(SourceProtocol)
        assert callable(getattr(SourceProtocol, "fetch", None))

    def test_正常系_fetch_allメソッドが必須(self) -> None:
        """fetch_allメソッドが定義されていることを確認。"""
        assert "fetch_all" in dir(SourceProtocol)
        assert callable(getattr(SourceProtocol, "fetch_all", None))


class MockSourceImpl:
    """SourceProtocolを実装するモッククラス。"""

    def __init__(self, sample_article: Article) -> None:
        """Initialize with sample article."""
        self._sample_article = sample_article

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "mock_source"

    @property
    def source_type(self) -> ArticleSource:
        """Return source type."""
        return ArticleSource.YFINANCE_TICKER

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch articles for a single identifier."""
        return FetchResult(
            articles=[self._sample_article],
            success=True,
            ticker=identifier,
        )

    def fetch_all(
        self,
        identifiers: list[str],
        count: int = 10,
    ) -> list[FetchResult]:
        """Fetch articles for multiple identifiers."""
        return [
            FetchResult(
                articles=[self._sample_article],
                success=True,
                ticker=ident,
            )
            for ident in identifiers
        ]


class TestSourceProtocolImplementation:
    """Test SourceProtocol with a concrete implementation."""

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
    def mock_source(self, sample_article: Article) -> MockSourceImpl:
        """テスト用のモックソースを提供するフィクスチャ。"""
        return MockSourceImpl(sample_article)

    def test_正常系_実装クラスがProtocolに準拠する(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """実装クラスがSourceProtocolに準拠することを確認。"""
        # isinstance チェックが可能（runtime_checkable の場合）
        assert isinstance(mock_source, SourceProtocol)

    def test_正常系_source_nameが文字列を返す(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """source_nameが文字列を返すことを確認。"""
        assert isinstance(mock_source.source_name, str)
        assert mock_source.source_name == "mock_source"

    def test_正常系_source_typeがArticleSourceを返す(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """source_typeがArticleSourceを返すことを確認。"""
        assert isinstance(mock_source.source_type, ArticleSource)
        assert mock_source.source_type == ArticleSource.YFINANCE_TICKER

    def test_正常系_fetchがFetchResultを返す(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """fetchがFetchResultを返すことを確認。"""
        result = mock_source.fetch("AAPL")

        assert isinstance(result, FetchResult)
        assert result.success is True
        assert result.ticker == "AAPL"
        assert len(result.articles) == 1

    def test_正常系_fetchでcountを指定できる(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """fetchでcount引数を指定できることを確認。"""
        result = mock_source.fetch("AAPL", count=5)

        assert isinstance(result, FetchResult)
        assert result.success is True

    def test_正常系_fetch_allがFetchResultリストを返す(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """fetch_allがFetchResultのリストを返すことを確認。"""
        results = mock_source.fetch_all(["AAPL", "GOOGL", "MSFT"])

        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].ticker == "AAPL"
        assert results[1].ticker == "GOOGL"
        assert results[2].ticker == "MSFT"

    def test_正常系_fetch_allでcountを指定できる(
        self,
        mock_source: MockSourceImpl,
    ) -> None:
        """fetch_allでcount引数を指定できることを確認。"""
        results = mock_source.fetch_all(["AAPL", "GOOGL"], count=5)

        assert isinstance(results, list)
        assert len(results) == 2


class TestSourceProtocolEdgeCases:
    """Test SourceProtocol edge cases."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    def test_エッジケース_空のidentifiersでfetch_all(
        self,
        sample_article: Article,
    ) -> None:
        """空のidentifiersリストでfetch_allを呼んだ場合の動作を確認。"""

        class EmptyMockSource:
            @property
            def source_name(self) -> str:
                return "empty_mock"

            @property
            def source_type(self) -> ArticleSource:
                return ArticleSource.YFINANCE_TICKER

            def fetch(self, identifier: str, count: int = 10) -> FetchResult:
                return FetchResult(articles=[], success=True, ticker=identifier)

            def fetch_all(
                self,
                identifiers: list[str],
                count: int = 10,
            ) -> list[FetchResult]:
                return [
                    FetchResult(articles=[], success=True, ticker=ident)
                    for ident in identifiers
                ]

        source = EmptyMockSource()
        results = source.fetch_all([])

        assert results == []

    def test_エッジケース_count0でfetch(
        self,
        sample_article: Article,
    ) -> None:
        """count=0でfetchを呼んだ場合の動作を確認。"""

        class ZeroCountMockSource:
            @property
            def source_name(self) -> str:
                return "zero_count_mock"

            @property
            def source_type(self) -> ArticleSource:
                return ArticleSource.YFINANCE_TICKER

            def fetch(self, identifier: str, count: int = 10) -> FetchResult:
                # count=0 の場合は空の結果を返す
                if count == 0:
                    return FetchResult(articles=[], success=True, ticker=identifier)
                return FetchResult(
                    articles=[sample_article],
                    success=True,
                    ticker=identifier,
                )

            def fetch_all(
                self,
                identifiers: list[str],
                count: int = 10,
            ) -> list[FetchResult]:
                return [self.fetch(ident, count) for ident in identifiers]

        source = ZeroCountMockSource()
        result = source.fetch("AAPL", count=0)

        assert result.is_empty is True
        assert result.article_count == 0


class TestSourceProtocolTypeAnnotations:
    """Test SourceProtocol type annotations."""

    def test_正常系_fetchの戻り値型がFetchResult(self) -> None:
        """fetchメソッドの戻り値型がFetchResultであることを確認。"""
        hints = inspect.get_annotations(SourceProtocol.fetch)
        assert hints.get("return") == FetchResult

    def test_正常系_fetch_allの戻り値型がlist_FetchResult(self) -> None:
        """fetch_allメソッドの戻り値型がlist[FetchResult]であることを確認。"""
        hints = inspect.get_annotations(SourceProtocol.fetch_all)
        return_hint = hints.get("return")
        # list[FetchResult] をチェック
        assert return_hint is not None
        assert hasattr(return_hint, "__origin__")
        assert return_hint.__origin__ is list
        assert return_hint.__args__ == (FetchResult,)

    def test_正常系_source_nameの戻り値型がstr(self) -> None:
        """source_nameプロパティの戻り値型がstrであることを確認。"""
        # プロパティの fget を取得
        source_name_prop = getattr(SourceProtocol, "source_name", None)
        assert source_name_prop is not None
        assert hasattr(source_name_prop, "fget")
        assert source_name_prop.fget is not None
        hints = inspect.get_annotations(source_name_prop.fget)
        assert hints.get("return") is str

    def test_正常系_source_typeの戻り値型がArticleSource(self) -> None:
        """source_typeプロパティの戻り値型がArticleSourceであることを確認。"""
        source_type_prop = getattr(SourceProtocol, "source_type", None)
        assert source_type_prop is not None
        assert hasattr(source_type_prop, "fget")
        assert source_type_prop.fget is not None
        hints = inspect.get_annotations(source_type_prop.fget)
        assert hints.get("return") is ArticleSource
