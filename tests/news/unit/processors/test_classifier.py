"""Unit tests for ClassifierProcessor in the news package.

Tests for the ClassifierProcessor that classifies news articles into categories
and extracts tags using Claude Agent SDK.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.processor import ProcessorProtocol, ProcessorType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
def sample_article() -> Article:
    """テスト用の Article を提供するフィクスチャ。"""
    return Article(
        url=HttpUrl("https://finance.yahoo.com/news/test-article"),
        title="Apple Reports Record Q1 Earnings",
        published_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
        source=ArticleSource.YFINANCE_TICKER,
        summary="Apple Inc. reported record quarterly earnings, "
        "driven by strong iPhone sales and services revenue.",
    )


@pytest.fixture
def sample_articles() -> list[Article]:
    """テスト用の複数 Article を提供するフィクスチャ。"""
    return [
        Article(
            url=HttpUrl(f"https://finance.yahoo.com/news/test-article-{i}"),
            title=f"Test Article Title {i}",
            published_at=datetime(2026, 1, 28, 12, i, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary=f"This is test article {i} summary in English.",
        )
        for i in range(3)
    ]


@pytest.fixture
def mock_classification_response() -> dict[str, Any]:
    """Claude Agent SDK の分類レスポンスを提供するフィクスチャ。"""
    return {
        "category": "finance",
        "tags": ["earnings", "apple", "technology", "quarterly_report"],
    }


class TestClassifierProcessorImports:
    """Test ClassifierProcessor module imports."""

    def test_正常系_ClassifierProcessorがインポートできる(self) -> None:
        """ClassifierProcessor がインポートできることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        assert ClassifierProcessor is not None

    def test_正常系_processorsパッケージからインポートできる(self) -> None:
        """processors パッケージから ClassifierProcessor をインポートできることを確認。"""
        from news.processors import ClassifierProcessor

        assert ClassifierProcessor is not None


class TestClassifierProcessorProtocolCompliance:
    """Test ClassifierProcessor complies with ProcessorProtocol."""

    def test_正常系_ClassifierProcessorがProcessorProtocolを満たす(self) -> None:
        """ClassifierProcessor が ProcessorProtocol を満たすことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        assert isinstance(processor, ProcessorProtocol)

    def test_正常系_processor_nameが正しい値を返す(self) -> None:
        """processor_name が正しい値を返すことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        assert processor.processor_name == "claude_classifier"

    def test_正常系_processor_typeがCLASSIFIERを返す(self) -> None:
        """processor_type が ProcessorType.CLASSIFIER を返すことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        assert processor.processor_type == ProcessorType.CLASSIFIER


class TestClassifierProcessorAgentProcessorInheritance:
    """Test ClassifierProcessor inherits from AgentProcessor."""

    def test_正常系_ClassifierProcessorがAgentProcessorを継承する(self) -> None:
        """ClassifierProcessor が AgentProcessor を継承することを確認。"""
        from news.processors.agent_base import AgentProcessor
        from news.processors.classifier import ClassifierProcessor

        assert issubclass(ClassifierProcessor, AgentProcessor)

    def test_正常系_processメソッドが使用可能(self) -> None:
        """process メソッドが使用可能であることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        assert hasattr(processor, "process")
        assert callable(processor.process)

    def test_正常系_process_batchメソッドが使用可能(self) -> None:
        """process_batch メソッドが使用可能であることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        assert hasattr(processor, "process_batch")
        assert callable(processor.process_batch)


class TestClassifierProcessorPromptBuilding:
    """Test ClassifierProcessor prompt building."""

    def test_正常系_プロンプトにタイトルが含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でタイトルがプロンプトに含まれることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        prompt = processor._build_prompt(sample_article)

        assert sample_article.title in prompt

    def test_正常系_プロンプトにサマリーが含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でサマリーがプロンプトに含まれることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        prompt = processor._build_prompt(sample_article)

        assert sample_article.summary is not None
        assert sample_article.summary in prompt

    def test_正常系_プロンプトにカテゴリ分類の指示が含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でカテゴリ分類の指示が含まれることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        prompt = processor._build_prompt(sample_article)

        # カテゴリ分類の指示が含まれる
        assert "カテゴリ" in prompt or "category" in prompt.lower()

    def test_正常系_プロンプトにタグ抽出の指示が含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でタグ抽出の指示が含まれることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        prompt = processor._build_prompt(sample_article)

        # タグ抽出の指示が含まれる
        assert "タグ" in prompt or "tags" in prompt.lower()

    def test_エッジケース_サマリーがNoneでもプロンプトが生成される(self) -> None:
        """サマリーが None の場合でもプロンプトが正常に生成されることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/no-summary"),
            title="Article Without Summary",
            published_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary=None,
        )

        processor = ClassifierProcessor()
        prompt = processor._build_prompt(article)

        # プロンプトが生成される（エラーなし）
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert article.title in prompt


class TestClassifierProcessorResponseParsing:
    """Test ClassifierProcessor response parsing."""

    def test_正常系_JSONレスポンスをパースできる(
        self,
        sample_article: Article,
        mock_classification_response: dict[str, Any],
    ) -> None:
        """JSON レスポンスを正しくパースできることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        response_json = json.dumps(mock_classification_response, ensure_ascii=False)
        updates = processor._parse_response(response_json, sample_article)

        assert "category" in updates
        assert updates["category"] == mock_classification_response["category"]
        assert "tags" in updates
        assert updates["tags"] == mock_classification_response["tags"]

    def test_異常系_不正なJSONでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """不正な JSON レスポンスでエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        with pytest.raises(AgentProcessorError, match=r"parse|JSON"):
            processor._parse_response("invalid json {", sample_article)

    def test_異常系_categoryフィールドがないJSONでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """category フィールドがない JSON でエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        invalid_response = json.dumps({"tags": ["test"]})

        with pytest.raises(AgentProcessorError, match="category"):
            processor._parse_response(invalid_response, sample_article)

    def test_異常系_tagsフィールドがないJSONでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """tags フィールドがない JSON でエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        invalid_response = json.dumps({"category": "finance"})

        with pytest.raises(AgentProcessorError, match="tags"):
            processor._parse_response(invalid_response, sample_article)


class TestClassifierProcessorProcess:
    """Test ClassifierProcessor.process method."""

    def test_正常系_processがcategoryとtagsを含むArticleを返す(
        self,
        sample_article: Article,
        mock_classification_response: dict[str, Any],
    ) -> None:
        """process が category と tags を含む新しい Article を返すことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(
                mock_classification_response, ensure_ascii=False
            )
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            result = processor.process(sample_article)

        assert result.category == mock_classification_response["category"]
        assert result.tags == mock_classification_response["tags"]

    def test_正常系_processで元のArticleが変更されない(
        self,
        sample_article: Article,
        mock_classification_response: dict[str, Any],
    ) -> None:
        """process で元の Article が変更されないことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        original_category = sample_article.category
        original_tags = sample_article.tags.copy()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(
                mock_classification_response, ensure_ascii=False
            )
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            processor.process(sample_article)

        # 元の Article は変更されない
        assert sample_article.category == original_category
        assert sample_article.tags == original_tags

    def test_正常系_processで元のフィールドが保持される(
        self,
        sample_article: Article,
        mock_classification_response: dict[str, Any],
    ) -> None:
        """process で元の Article のフィールドが保持されることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(
                mock_classification_response, ensure_ascii=False
            )
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            result = processor.process(sample_article)

        # 元のフィールドが保持される
        assert str(result.url) == str(sample_article.url)
        assert result.title == sample_article.title
        assert result.published_at == sample_article.published_at
        assert result.source == sample_article.source
        assert result.summary == sample_article.summary


class TestClassifierProcessorProcessBatch:
    """Test ClassifierProcessor.process_batch method."""

    def test_正常系_process_batchがArticleリストを返す(
        self,
        sample_articles: list[Article],
        mock_classification_response: dict[str, Any],
    ) -> None:
        """process_batch が Article のリストを返すことを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(
                mock_classification_response, ensure_ascii=False
            )
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            results = processor.process_batch(sample_articles)

        assert isinstance(results, list)
        assert len(results) == len(sample_articles)
        assert all(isinstance(r, Article) for r in results)
        assert all(r.category is not None for r in results)
        assert all(len(r.tags) > 0 for r in results)

    def test_エッジケース_空のリストでprocess_batch(self) -> None:
        """空のリストで process_batch を呼んだ場合、空のリストが返ることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        results = processor.process_batch([])

        assert results == []


class TestClassifierProcessorSDKErrors:
    """Test ClassifierProcessor SDK error handling."""

    def test_異常系_SDKが未インストールでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """Claude Agent SDK が未インストールの場合にエラーが発生することを確認。"""
        from news.processors.agent_base import SDKNotInstalledError
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        with (
            patch.dict("sys.modules", {"claude_agent_sdk": None}),
            pytest.raises(SDKNotInstalledError),
        ):
            processor.process(sample_article)

    def test_異常系_エージェント実行失敗でエラー(
        self,
        sample_article: Article,
    ) -> None:
        """エージェント実行が失敗した場合にエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        async def mock_query_with_error(
            *args: Any, **kwargs: Any
        ) -> AsyncIterator[Any]:
            raise Exception("Agent execution failed")
            yield  # Make this an async generator

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_with_error

        with (
            patch.object(processor, "_get_sdk", return_value=mock_sdk),
            pytest.raises(AgentProcessorError, match="execution failed"),
        ):
            processor.process(sample_article)


class TestClassifierProcessorCategories:
    """Test ClassifierProcessor category classification."""

    @pytest.mark.parametrize(
        "category",
        [
            "finance",
            "technology",
            "macro_economy",
            "market",
            "company",
            "politics",
            "other",
        ],
    )
    def test_パラメトライズ_様々なカテゴリが返される(
        self,
        sample_article: Article,
        category: str,
    ) -> None:
        """様々なカテゴリが正しく返されることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()
        response = {"category": category, "tags": ["test"]}

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(response, ensure_ascii=False)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            result = processor.process(sample_article)

        assert result.category == category


class TestClassifierProcessorLogging:
    """Test ClassifierProcessor logging."""

    def test_正常系_処理時にログが出力される(
        self,
        sample_article: Article,
        mock_classification_response: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """処理時にログが出力されることを確認。"""
        from news.processors.classifier import ClassifierProcessor

        processor = ClassifierProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(
                mock_classification_response, ensure_ascii=False
            )
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            processor.process(sample_article)

        captured = capsys.readouterr()
        # ログにプロセッサ名や処理に関するメッセージが含まれる
        assert (
            "claude_classifier" in captured.out
            or "Processing" in captured.out
            or "processed" in captured.out.lower()
        )
