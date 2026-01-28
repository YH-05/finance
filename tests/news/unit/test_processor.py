"""Unit tests for ProcessorProtocol in the news package.

Tests for the ProcessorProtocol that defines the interface for AI processing
(summarization, classification, tagging, etc.).
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.processor import ProcessorProtocol, ProcessorType


class TestProcessorTypeEnum:
    """Test ProcessorType enumeration."""

    def test_正常系_ProcessorTypeがEnumである(self) -> None:
        """ProcessorTypeがEnumとして定義されていることを確認。"""
        assert issubclass(ProcessorType, Enum)

    def test_正常系_ProcessorTypeがstrEnumである(self) -> None:
        """ProcessorTypeがstr, Enumを継承していることを確認。"""
        assert issubclass(ProcessorType, str)
        assert issubclass(ProcessorType, Enum)

    def test_正常系_SUMMARIZER値が存在する(self) -> None:
        """ProcessorType.SUMMARIZERが定義されていることを確認。"""
        assert hasattr(ProcessorType, "SUMMARIZER")
        assert ProcessorType.SUMMARIZER.value == "summarizer"

    def test_正常系_CLASSIFIER値が存在する(self) -> None:
        """ProcessorType.CLASSIFIERが定義されていることを確認。"""
        assert hasattr(ProcessorType, "CLASSIFIER")
        assert ProcessorType.CLASSIFIER.value == "classifier"

    def test_正常系_TAGGER値が存在する(self) -> None:
        """ProcessorType.TAGGERが定義されていることを確認。"""
        assert hasattr(ProcessorType, "TAGGER")
        assert ProcessorType.TAGGER.value == "tagger"


class TestProcessorProtocolDefinition:
    """Test ProcessorProtocol definition and structure."""

    def test_正常系_Protocolクラスとして定義されている(self) -> None:
        """ProcessorProtocolがProtocolクラスとして定義されていることを確認。"""
        assert issubclass(ProcessorProtocol, Protocol)

    def test_正常系_runtime_checkableである(self) -> None:
        """ProcessorProtocolがruntime_checkableであることを確認。"""
        # runtime_checkable デコレータが適用されていればisinstanceチェックが可能
        assert hasattr(ProcessorProtocol, "_is_protocol")
        assert ProcessorProtocol._is_protocol is True


class TestProcessorProtocolProperties:
    """Test ProcessorProtocol required properties."""

    def test_正常系_processor_nameプロパティが必須(self) -> None:
        """processor_nameプロパティが定義されていることを確認。"""
        assert "processor_name" in dir(ProcessorProtocol)

    def test_正常系_processor_typeプロパティが必須(self) -> None:
        """processor_typeプロパティが定義されていることを確認。"""
        assert "processor_type" in dir(ProcessorProtocol)


class TestProcessorProtocolMethods:
    """Test ProcessorProtocol required methods."""

    def test_正常系_processメソッドが必須(self) -> None:
        """processメソッドが定義されていることを確認。"""
        assert "process" in dir(ProcessorProtocol)
        assert callable(getattr(ProcessorProtocol, "process", None))

    def test_正常系_process_batchメソッドが必須(self) -> None:
        """process_batchメソッドが定義されていることを確認。"""
        assert "process_batch" in dir(ProcessorProtocol)
        assert callable(getattr(ProcessorProtocol, "process_batch", None))


class MockProcessorImpl:
    """ProcessorProtocolを実装するモッククラス。"""

    def __init__(self) -> None:
        """Initialize mock processor."""
        self._processed_count: int = 0

    @property
    def processor_name(self) -> str:
        """Return processor name."""
        return "mock_processor"

    @property
    def processor_type(self) -> ProcessorType:
        """Return processor type."""
        return ProcessorType.SUMMARIZER

    def process(self, article: Article) -> Article:
        """Process a single article."""
        self._processed_count += 1
        # 要約を追加（モック処理）
        return article.model_copy(update={"summary_ja": f"要約: {article.title}"})

    def process_batch(self, articles: list[Article]) -> list[Article]:
        """Process multiple articles."""
        return [self.process(article) for article in articles]


class TestProcessorProtocolImplementation:
    """Test ProcessorProtocol with a concrete implementation."""

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
    def mock_processor(self) -> MockProcessorImpl:
        """テスト用のモックプロセッサを提供するフィクスチャ。"""
        return MockProcessorImpl()

    def test_正常系_実装クラスがProtocolに準拠する(
        self,
        mock_processor: MockProcessorImpl,
    ) -> None:
        """実装クラスがProcessorProtocolに準拠することを確認。"""
        # isinstance チェックが可能（runtime_checkable の場合）
        assert isinstance(mock_processor, ProcessorProtocol)

    def test_正常系_processor_nameが文字列を返す(
        self,
        mock_processor: MockProcessorImpl,
    ) -> None:
        """processor_nameが文字列を返すことを確認。"""
        assert isinstance(mock_processor.processor_name, str)
        assert mock_processor.processor_name == "mock_processor"

    def test_正常系_processor_typeがProcessorTypeを返す(
        self,
        mock_processor: MockProcessorImpl,
    ) -> None:
        """processor_typeがProcessorTypeを返すことを確認。"""
        assert isinstance(mock_processor.processor_type, ProcessorType)
        assert mock_processor.processor_type == ProcessorType.SUMMARIZER

    def test_正常系_processがArticleを返す(
        self,
        mock_processor: MockProcessorImpl,
        sample_article: Article,
    ) -> None:
        """processがArticleを返すことを確認。"""
        result = mock_processor.process(sample_article)

        assert isinstance(result, Article)
        assert result.summary_ja is not None
        assert "要約:" in result.summary_ja

    def test_正常系_processで記事が処理される(
        self,
        mock_processor: MockProcessorImpl,
        sample_article: Article,
    ) -> None:
        """processで記事が正しく処理されることを確認。"""
        result = mock_processor.process(sample_article)

        assert result.title == sample_article.title
        assert str(result.url) == str(sample_article.url)
        assert mock_processor._processed_count == 1

    def test_正常系_process_batchがArticleリストを返す(
        self,
        mock_processor: MockProcessorImpl,
        sample_article: Article,
    ) -> None:
        """process_batchがArticleのリストを返すことを確認。"""
        articles = [sample_article, sample_article, sample_article]
        results = mock_processor.process_batch(articles)

        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(r, Article) for r in results)
        assert all(r.summary_ja is not None for r in results)

    def test_正常系_process_batchで全記事が処理される(
        self,
        mock_processor: MockProcessorImpl,
        sample_article: Article,
    ) -> None:
        """process_batchで全ての記事が処理されることを確認。"""
        articles = [sample_article, sample_article]
        mock_processor.process_batch(articles)

        assert mock_processor._processed_count == 2


class TestProcessorProtocolEdgeCases:
    """Test ProcessorProtocol edge cases."""

    @pytest.fixture
    def sample_article(self) -> Article:
        """テスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url=HttpUrl("https://finance.yahoo.com/news/test"),
            title="Test Article",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
        )

    def test_エッジケース_空のarticlesでprocess_batch(self) -> None:
        """空のarticlesリストでprocess_batchを呼んだ場合の動作を確認。"""

        class EmptyMockProcessor:
            @property
            def processor_name(self) -> str:
                return "empty_mock"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def process(self, article: Article) -> Article:
                return article

            def process_batch(self, articles: list[Article]) -> list[Article]:
                return [self.process(a) for a in articles]

        processor = EmptyMockProcessor()
        results = processor.process_batch([])

        assert results == []

    def test_エッジケース_既に要約がある記事をprocess(
        self,
        sample_article: Article,
    ) -> None:
        """既に要約がある記事をprocessした場合の動作を確認。"""

        class OverwriteMockProcessor:
            @property
            def processor_name(self) -> str:
                return "overwrite_mock"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def process(self, article: Article) -> Article:
                # 既存の要約を上書き
                return article.model_copy(update={"summary_ja": "新しい要約"})

            def process_batch(self, articles: list[Article]) -> list[Article]:
                return [self.process(a) for a in articles]

        # 既に要約がある記事を作成
        article_with_summary = sample_article.model_copy(
            update={"summary_ja": "元の要約"}
        )

        processor = OverwriteMockProcessor()
        result = processor.process(article_with_summary)

        assert result.summary_ja == "新しい要約"


class TestProcessorProtocolTypeAnnotations:
    """Test ProcessorProtocol type annotations."""

    def test_正常系_processの戻り値型がArticle(self) -> None:
        """processメソッドの戻り値型がArticleであることを確認。"""
        hints = inspect.get_annotations(ProcessorProtocol.process)
        assert hints.get("return") == Article

    def test_正常系_process_batchの戻り値型がlist_Article(self) -> None:
        """process_batchメソッドの戻り値型がlist[Article]であることを確認。"""
        hints = inspect.get_annotations(ProcessorProtocol.process_batch)
        return_hint = hints.get("return")
        # list[Article] をチェック
        assert return_hint is not None
        assert hasattr(return_hint, "__origin__")
        assert return_hint.__origin__ is list
        assert return_hint.__args__ == (Article,)

    def test_正常系_processor_nameの戻り値型がstr(self) -> None:
        """processor_nameプロパティの戻り値型がstrであることを確認。"""
        processor_name_prop = getattr(ProcessorProtocol, "processor_name", None)
        assert processor_name_prop is not None
        assert hasattr(processor_name_prop, "fget")
        assert processor_name_prop.fget is not None
        hints = inspect.get_annotations(processor_name_prop.fget)
        assert hints.get("return") is str

    def test_正常系_processor_typeの戻り値型がProcessorType(self) -> None:
        """processor_typeプロパティの戻り値型がProcessorTypeであることを確認。"""
        processor_type_prop = getattr(ProcessorProtocol, "processor_type", None)
        assert processor_type_prop is not None
        assert hasattr(processor_type_prop, "fget")
        assert processor_type_prop.fget is not None
        hints = inspect.get_annotations(processor_type_prop.fget)
        assert hints.get("return") is ProcessorType


class TestProcessorTypeUsage:
    """Test ProcessorType enum usage scenarios."""

    @pytest.mark.parametrize(
        "processor_type",
        [
            ProcessorType.SUMMARIZER,
            ProcessorType.CLASSIFIER,
            ProcessorType.TAGGER,
        ],
    )
    def test_パラメトライズ_全てのProcessorTypeが文字列として使用できる(
        self,
        processor_type: ProcessorType,
    ) -> None:
        """全てのProcessorTypeが文字列として使用できることを確認。"""
        # str として使用できる
        assert isinstance(processor_type, str)
        assert isinstance(processor_type.value, str)
        # 文字列比較ができる
        assert processor_type == processor_type.value
