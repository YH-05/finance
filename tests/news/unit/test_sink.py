"""Unit tests for SinkProtocol in the news package.

Tests for the SinkProtocol that defines the interface for news output destinations.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.result import FetchResult
from news.core.sink import SinkProtocol, SinkType


class TestSinkTypeEnum:
    """Test SinkType enumeration."""

    def test_正常系_SinkTypeがEnumである(self) -> None:
        """SinkTypeがEnumとして定義されていることを確認。"""
        assert issubclass(SinkType, Enum)

    def test_正常系_SinkTypeがstrEnumである(self) -> None:
        """SinkTypeがstr, Enumを継承していることを確認。"""
        assert issubclass(SinkType, str)
        assert issubclass(SinkType, Enum)

    def test_正常系_FILE値が存在する(self) -> None:
        """SinkType.FILEが定義されていることを確認。"""
        assert hasattr(SinkType, "FILE")
        assert SinkType.FILE.value == "file"

    def test_正常系_GITHUB値が存在する(self) -> None:
        """SinkType.GITHUBが定義されていることを確認。"""
        assert hasattr(SinkType, "GITHUB")
        assert SinkType.GITHUB.value == "github"

    def test_正常系_REPORT値が存在する(self) -> None:
        """SinkType.REPORTが定義されていることを確認。"""
        assert hasattr(SinkType, "REPORT")
        assert SinkType.REPORT.value == "report"


class TestSinkProtocolDefinition:
    """Test SinkProtocol definition and structure."""

    def test_正常系_Protocolクラスとして定義されている(self) -> None:
        """SinkProtocolがProtocolクラスとして定義されていることを確認。"""
        assert issubclass(SinkProtocol, Protocol)

    def test_正常系_runtime_checkableである(self) -> None:
        """SinkProtocolがruntime_checkableであることを確認。"""
        # runtime_checkable デコレータが適用されていればisinstanceチェックが可能
        assert hasattr(SinkProtocol, "_is_protocol")
        assert SinkProtocol._is_protocol is True


class TestSinkProtocolProperties:
    """Test SinkProtocol required properties."""

    def test_正常系_sink_nameプロパティが必須(self) -> None:
        """sink_nameプロパティが定義されていることを確認。"""
        assert "sink_name" in dir(SinkProtocol)

    def test_正常系_sink_typeプロパティが必須(self) -> None:
        """sink_typeプロパティが定義されていることを確認。"""
        assert "sink_type" in dir(SinkProtocol)


class TestSinkProtocolMethods:
    """Test SinkProtocol required methods."""

    def test_正常系_writeメソッドが必須(self) -> None:
        """writeメソッドが定義されていることを確認。"""
        assert "write" in dir(SinkProtocol)
        assert callable(getattr(SinkProtocol, "write", None))

    def test_正常系_write_batchメソッドが必須(self) -> None:
        """write_batchメソッドが定義されていることを確認。"""
        assert "write_batch" in dir(SinkProtocol)
        assert callable(getattr(SinkProtocol, "write_batch", None))


class MockSinkImpl:
    """SinkProtocolを実装するモッククラス。"""

    def __init__(self) -> None:
        """Initialize mock sink."""
        self._written_articles: list[Article] = []
        self._written_results: list[FetchResult] = []

    @property
    def sink_name(self) -> str:
        """Return sink name."""
        return "mock_sink"

    @property
    def sink_type(self) -> SinkType:
        """Return sink type."""
        return SinkType.FILE

    def write(
        self,
        articles: list[Article],
        metadata: dict | None = None,
    ) -> bool:
        """Write articles to the mock sink."""
        self._written_articles.extend(articles)
        return True

    def write_batch(self, results: list[FetchResult]) -> bool:
        """Write batch of FetchResults to the mock sink."""
        self._written_results.extend(results)
        for result in results:
            self._written_articles.extend(result.articles)
        return True


class TestSinkProtocolImplementation:
    """Test SinkProtocol with a concrete implementation."""

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
    def sample_fetch_result(self, sample_article: Article) -> FetchResult:
        """テスト用のFetchResultを提供するフィクスチャ。"""
        return FetchResult(
            articles=[sample_article],
            success=True,
            ticker="AAPL",
        )

    @pytest.fixture
    def mock_sink(self) -> MockSinkImpl:
        """テスト用のモックシンクを提供するフィクスチャ。"""
        return MockSinkImpl()

    def test_正常系_実装クラスがProtocolに準拠する(
        self,
        mock_sink: MockSinkImpl,
    ) -> None:
        """実装クラスがSinkProtocolに準拠することを確認。"""
        # isinstance チェックが可能（runtime_checkable の場合）
        assert isinstance(mock_sink, SinkProtocol)

    def test_正常系_sink_nameが文字列を返す(
        self,
        mock_sink: MockSinkImpl,
    ) -> None:
        """sink_nameが文字列を返すことを確認。"""
        assert isinstance(mock_sink.sink_name, str)
        assert mock_sink.sink_name == "mock_sink"

    def test_正常系_sink_typeがSinkTypeを返す(
        self,
        mock_sink: MockSinkImpl,
    ) -> None:
        """sink_typeがSinkTypeを返すことを確認。"""
        assert isinstance(mock_sink.sink_type, SinkType)
        assert mock_sink.sink_type == SinkType.FILE

    def test_正常系_writeがboolを返す(
        self,
        mock_sink: MockSinkImpl,
        sample_article: Article,
    ) -> None:
        """writeがboolを返すことを確認。"""
        result = mock_sink.write([sample_article])

        assert isinstance(result, bool)
        assert result is True

    def test_正常系_writeでmetadataを指定できる(
        self,
        mock_sink: MockSinkImpl,
        sample_article: Article,
    ) -> None:
        """writeでmetadata引数を指定できることを確認。"""
        metadata = {"source": "test", "timestamp": "2026-01-28"}
        result = mock_sink.write([sample_article], metadata=metadata)

        assert isinstance(result, bool)
        assert result is True

    def test_正常系_write_batchがboolを返す(
        self,
        mock_sink: MockSinkImpl,
        sample_fetch_result: FetchResult,
    ) -> None:
        """write_batchがboolを返すことを確認。"""
        result = mock_sink.write_batch([sample_fetch_result])

        assert isinstance(result, bool)
        assert result is True

    def test_正常系_write_batchで複数のFetchResultを処理できる(
        self,
        mock_sink: MockSinkImpl,
        sample_article: Article,
    ) -> None:
        """write_batchで複数のFetchResultを処理できることを確認。"""
        results = [
            FetchResult(articles=[sample_article], success=True, ticker="AAPL"),
            FetchResult(articles=[sample_article], success=True, ticker="GOOGL"),
            FetchResult(articles=[sample_article], success=True, ticker="MSFT"),
        ]
        result = mock_sink.write_batch(results)

        assert result is True
        assert len(mock_sink._written_results) == 3


class TestSinkProtocolEdgeCases:
    """Test SinkProtocol edge cases."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    def test_エッジケース_空のarticlesでwrite(self) -> None:
        """空のarticlesリストでwriteを呼んだ場合の動作を確認。"""

        class EmptyMockSink:
            @property
            def sink_name(self) -> str:
                return "empty_mock"

            @property
            def sink_type(self) -> SinkType:
                return SinkType.FILE

            def write(
                self,
                articles: list[Article],
                metadata: dict | None = None,
            ) -> bool:
                return True

            def write_batch(self, results: list[FetchResult]) -> bool:
                return True

        sink = EmptyMockSink()
        result = sink.write([])

        assert result is True

    def test_エッジケース_空のresultsでwrite_batch(self) -> None:
        """空のresultsリストでwrite_batchを呼んだ場合の動作を確認。"""

        class EmptyMockSink:
            @property
            def sink_name(self) -> str:
                return "empty_mock"

            @property
            def sink_type(self) -> SinkType:
                return SinkType.FILE

            def write(
                self,
                articles: list[Article],
                metadata: dict | None = None,
            ) -> bool:
                return True

            def write_batch(self, results: list[FetchResult]) -> bool:
                return True

        sink = EmptyMockSink()
        result = sink.write_batch([])

        assert result is True

    def test_エッジケース_metadataがNoneでwrite(
        self,
        sample_article: Article,
    ) -> None:
        """metadata=Noneでwriteを呼んだ場合の動作を確認。"""

        class NoneMetadataMockSink:
            @property
            def sink_name(self) -> str:
                return "none_metadata_mock"

            @property
            def sink_type(self) -> SinkType:
                return SinkType.FILE

            def write(
                self,
                articles: list[Article],
                metadata: dict | None = None,
            ) -> bool:
                return metadata is None

            def write_batch(self, results: list[FetchResult]) -> bool:
                return True

        sink = NoneMetadataMockSink()
        result = sink.write([sample_article], metadata=None)

        assert result is True


class TestSinkProtocolTypeAnnotations:
    """Test SinkProtocol type annotations."""

    def test_正常系_writeの戻り値型がbool(self) -> None:
        """writeメソッドの戻り値型がboolであることを確認。"""
        hints = inspect.get_annotations(SinkProtocol.write)
        assert hints.get("return") is bool

    def test_正常系_write_batchの戻り値型がbool(self) -> None:
        """write_batchメソッドの戻り値型がboolであることを確認。"""
        hints = inspect.get_annotations(SinkProtocol.write_batch)
        assert hints.get("return") is bool

    def test_正常系_sink_nameの戻り値型がstr(self) -> None:
        """sink_nameプロパティの戻り値型がstrであることを確認。"""
        sink_name_prop = getattr(SinkProtocol, "sink_name", None)
        assert sink_name_prop is not None
        assert hasattr(sink_name_prop, "fget")
        assert sink_name_prop.fget is not None
        hints = inspect.get_annotations(sink_name_prop.fget)
        assert hints.get("return") is str

    def test_正常系_sink_typeの戻り値型がSinkType(self) -> None:
        """sink_typeプロパティの戻り値型がSinkTypeであることを確認。"""
        sink_type_prop = getattr(SinkProtocol, "sink_type", None)
        assert sink_type_prop is not None
        assert hasattr(sink_type_prop, "fget")
        assert sink_type_prop.fget is not None
        hints = inspect.get_annotations(sink_type_prop.fget)
        assert hints.get("return") is SinkType
