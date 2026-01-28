"""Unit tests for SummarizerProcessor in the news package.

Tests for the SummarizerProcessor that generates Japanese summaries
of English news articles using Claude Agent SDK.
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
def mock_summary_response() -> dict[str, Any]:
    """Claude Agent SDK の要約レスポンスを提供するフィクスチャ。"""
    return {
        "summary_ja": "Appleは四半期決算で過去最高の業績を発表。"
        "iPhoneの販売好調とサービス収益が牽引した。"
    }


class TestSummarizerProcessorImports:
    """Test SummarizerProcessor module imports."""

    def test_正常系_SummarizerProcessorがインポートできる(self) -> None:
        """SummarizerProcessor がインポートできることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        assert SummarizerProcessor is not None

    def test_正常系_processorsパッケージからインポートできる(self) -> None:
        """processors パッケージから SummarizerProcessor をインポートできることを確認。"""
        from news.processors import SummarizerProcessor

        assert SummarizerProcessor is not None


class TestSummarizerProcessorProtocolCompliance:
    """Test SummarizerProcessor complies with ProcessorProtocol."""

    def test_正常系_SummarizerProcessorがProcessorProtocolを満たす(self) -> None:
        """SummarizerProcessor が ProcessorProtocol を満たすことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        assert isinstance(processor, ProcessorProtocol)

    def test_正常系_processor_nameが正しい値を返す(self) -> None:
        """processor_name が正しい値を返すことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        assert processor.processor_name == "claude_summarizer"

    def test_正常系_processor_typeがSUMMARIZERを返す(self) -> None:
        """processor_type が ProcessorType.SUMMARIZER を返すことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        assert processor.processor_type == ProcessorType.SUMMARIZER


class TestSummarizerProcessorAgentProcessorInheritance:
    """Test SummarizerProcessor inherits from AgentProcessor."""

    def test_正常系_SummarizerProcessorがAgentProcessorを継承する(self) -> None:
        """SummarizerProcessor が AgentProcessor を継承することを確認。"""
        from news.processors.agent_base import AgentProcessor
        from news.processors.summarizer import SummarizerProcessor

        assert issubclass(SummarizerProcessor, AgentProcessor)

    def test_正常系_processメソッドが使用可能(self) -> None:
        """process メソッドが使用可能であることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        assert hasattr(processor, "process")
        assert callable(processor.process)

    def test_正常系_process_batchメソッドが使用可能(self) -> None:
        """process_batch メソッドが使用可能であることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        assert hasattr(processor, "process_batch")
        assert callable(processor.process_batch)


class TestSummarizerProcessorPromptBuilding:
    """Test SummarizerProcessor prompt building."""

    def test_正常系_プロンプトにタイトルが含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でタイトルがプロンプトに含まれることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        prompt = processor._build_prompt(sample_article)

        assert sample_article.title in prompt

    def test_正常系_プロンプトにサマリーが含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt でサマリーがプロンプトに含まれることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        prompt = processor._build_prompt(sample_article)

        assert sample_article.summary is not None
        assert sample_article.summary in prompt

    def test_正常系_プロンプトに日本語要約の指示が含まれる(
        self,
        sample_article: Article,
    ) -> None:
        """_build_prompt で日本語要約の指示が含まれることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        prompt = processor._build_prompt(sample_article)

        # 日本語で要約するよう指示が含まれる
        assert "日本語" in prompt or "Japanese" in prompt

    def test_エッジケース_サマリーがNoneでもプロンプトが生成される(self) -> None:
        """サマリーが None の場合でもプロンプトが正常に生成されることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        article = Article(
            url=HttpUrl("https://finance.yahoo.com/news/no-summary"),
            title="Article Without Summary",
            published_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary=None,
        )

        processor = SummarizerProcessor()
        prompt = processor._build_prompt(article)

        # プロンプトが生成される（エラーなし）
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert article.title in prompt


class TestSummarizerProcessorResponseParsing:
    """Test SummarizerProcessor response parsing."""

    def test_正常系_JSONレスポンスをパースできる(
        self,
        sample_article: Article,
        mock_summary_response: dict[str, Any],
    ) -> None:
        """JSON レスポンスを正しくパースできることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        response_json = json.dumps(mock_summary_response, ensure_ascii=False)
        updates = processor._parse_response(response_json, sample_article)

        assert "summary_ja" in updates
        assert updates["summary_ja"] == mock_summary_response["summary_ja"]

    def test_異常系_不正なJSONでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """不正な JSON レスポンスでエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

        with pytest.raises(AgentProcessorError, match=r"parse|JSON"):
            processor._parse_response("invalid json {", sample_article)

    def test_異常系_summary_jaフィールドがないJSONでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """summary_ja フィールドがない JSON でエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessorError
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        invalid_response = json.dumps({"category": "finance"})

        with pytest.raises(AgentProcessorError, match="summary_ja"):
            processor._parse_response(invalid_response, sample_article)


class TestSummarizerProcessorProcess:
    """Test SummarizerProcessor.process method."""

    def test_正常系_processがsummary_jaを含むArticleを返す(
        self,
        sample_article: Article,
        mock_summary_response: dict[str, Any],
    ) -> None:
        """process が summary_ja を含む新しい Article を返すことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_summary_response, ensure_ascii=False)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            result = processor.process(sample_article)

        assert result.summary_ja == mock_summary_response["summary_ja"]

    def test_正常系_processで元のArticleが変更されない(
        self,
        sample_article: Article,
        mock_summary_response: dict[str, Any],
    ) -> None:
        """process で元の Article が変更されないことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        original_summary_ja = sample_article.summary_ja

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_summary_response, ensure_ascii=False)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            processor.process(sample_article)

        # 元の Article は変更されない
        assert sample_article.summary_ja == original_summary_ja

    def test_正常系_processで元のフィールドが保持される(
        self,
        sample_article: Article,
        mock_summary_response: dict[str, Any],
    ) -> None:
        """process で元の Article のフィールドが保持されることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_summary_response, ensure_ascii=False)
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


class TestSummarizerProcessorProcessBatch:
    """Test SummarizerProcessor.process_batch method."""

    def test_正常系_process_batchがArticleリストを返す(
        self,
        sample_articles: list[Article],
        mock_summary_response: dict[str, Any],
    ) -> None:
        """process_batch が Article のリストを返すことを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_summary_response, ensure_ascii=False)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(processor, "_get_sdk", return_value=mock_sdk):
            results = processor.process_batch(sample_articles)

        assert isinstance(results, list)
        assert len(results) == len(sample_articles)
        assert all(isinstance(r, Article) for r in results)
        assert all(r.summary_ja is not None for r in results)

    def test_エッジケース_空のリストでprocess_batch(self) -> None:
        """空のリストで process_batch を呼んだ場合、空のリストが返ることを確認。"""
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()
        results = processor.process_batch([])

        assert results == []


class TestSummarizerProcessorSDKErrors:
    """Test SummarizerProcessor SDK error handling."""

    def test_異常系_SDKが未インストールでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """Claude Agent SDK が未インストールの場合にエラーが発生することを確認。"""
        from news.processors.agent_base import SDKNotInstalledError
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

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
        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

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


class TestSummarizerProcessorLogging:
    """Test SummarizerProcessor logging."""

    def test_正常系_処理時にログが出力される(
        self,
        sample_article: Article,
        mock_summary_response: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """処理時にログが出力されることを確認。"""
        import logging

        from news.processors.summarizer import SummarizerProcessor

        processor = SummarizerProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_summary_response, ensure_ascii=False)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with (
            caplog.at_level(logging.DEBUG, logger="news.processors.agent_base"),
            patch.object(processor, "_get_sdk", return_value=mock_sdk),
        ):
            processor.process(sample_article)

        # structlog の出力先に応じて capsys または caplog で確認
        captured = capsys.readouterr()
        log_text = captured.out + caplog.text
        assert (
            "claude_summarizer" in log_text
            or "Processing" in log_text
            or "processed" in log_text.lower()
        )
