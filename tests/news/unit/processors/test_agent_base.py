"""Unit tests for AgentProcessor in the news package.

Tests for the AgentProcessor base class that integrates with Claude Agent SDK
for AI processing (summarization, classification, tagging, etc.).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl

from news.core.article import Article, ArticleSource
from news.core.errors import NewsError
from news.core.processor import ProcessorProtocol, ProcessorType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
def sample_article() -> Article:
    """テスト用の Article を提供するフィクスチャ。"""
    return Article(
        url=HttpUrl("https://finance.yahoo.com/news/test-article"),
        title="Test Article Title",
        published_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
        source=ArticleSource.YFINANCE_TICKER,
        summary="This is a test article summary in English.",
    )


@pytest.fixture
def sample_articles(sample_article: Article) -> list[Article]:
    """テスト用の複数 Article を提供するフィクスチャ。"""
    articles = []
    for i in range(3):
        articles.append(
            Article(
                url=HttpUrl(f"https://finance.yahoo.com/news/test-article-{i}"),
                title=f"Test Article Title {i}",
                published_at=datetime(2026, 1, 28, 12, i, 0, tzinfo=timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
                summary=f"This is test article {i} summary in English.",
            )
        )
    return articles


@pytest.fixture
def mock_agent_response() -> dict[str, Any]:
    """Claude Agent SDK のモックレスポンスを提供するフィクスチャ。"""
    return {
        "summary_ja": "これはテスト記事の日本語要約です。",
        "category": "finance",
        "sentiment": 0.5,
    }


class TestAgentProcessorImports:
    """Test AgentProcessor module imports."""

    def test_正常系_AgentProcessorがインポートできる(self) -> None:
        """AgentProcessor がインポートできることを確認。"""
        from news.processors.agent_base import AgentProcessor

        assert AgentProcessor is not None

    def test_正常系_AgentProcessorErrorがインポートできる(self) -> None:
        """AgentProcessorError がインポートできることを確認。"""
        from news.processors.agent_base import AgentProcessorError

        assert AgentProcessorError is not None
        assert issubclass(AgentProcessorError, NewsError)

    def test_正常系_SDKNotInstalledErrorがインポートできる(self) -> None:
        """SDKNotInstalledError がインポートできることを確認。"""
        from news.processors.agent_base import SDKNotInstalledError

        assert SDKNotInstalledError is not None


class TestAgentProcessorProtocolCompliance:
    """Test AgentProcessor complies with ProcessorProtocol."""

    def test_正常系_AgentProcessorがProcessorProtocolを満たす(self) -> None:
        """AgentProcessor が ProcessorProtocol を満たすことを確認。"""
        from news.processors.agent_base import AgentProcessor

        # 具象クラスを定義（AgentProcessor は抽象基底クラスの場合）
        class ConcreteAgentProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_agent"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = ConcreteAgentProcessor()
        assert isinstance(processor, ProcessorProtocol)

    def test_正常系_processor_nameプロパティが存在する(self) -> None:
        """processor_name プロパティが存在することを確認。"""
        from news.processors.agent_base import AgentProcessor

        assert hasattr(AgentProcessor, "processor_name")

    def test_正常系_processor_typeプロパティが存在する(self) -> None:
        """processor_type プロパティが存在することを確認。"""
        from news.processors.agent_base import AgentProcessor

        assert hasattr(AgentProcessor, "processor_type")

    def test_正常系_processメソッドが存在する(self) -> None:
        """process メソッドが存在することを確認。"""
        from news.processors.agent_base import AgentProcessor

        assert hasattr(AgentProcessor, "process")
        assert callable(getattr(AgentProcessor, "process", None))

    def test_正常系_process_batchメソッドが存在する(self) -> None:
        """process_batch メソッドが存在することを確認。"""
        from news.processors.agent_base import AgentProcessor

        assert hasattr(AgentProcessor, "process_batch")
        assert callable(getattr(AgentProcessor, "process_batch", None))


class TestAgentProcessorJSONDataPassing:
    """Test JSON data passing to/from Claude Agent SDK."""

    def test_正常系_ArticleをJSON形式に変換できる(
        self,
        sample_article: Article,
    ) -> None:
        """Article を JSON 形式に変換できることを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_json"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = TestProcessor()
        json_data = processor._article_to_json(sample_article)

        # JSON としてパースできる
        parsed = json.loads(json_data)
        assert "url" in parsed
        assert "title" in parsed
        assert parsed["title"] == "Test Article Title"

    def test_正常系_JSONレスポンスをパースできる(
        self,
        sample_article: Article,
        mock_agent_response: dict[str, Any],
    ) -> None:
        """JSON レスポンスをパースして Article を更新できることを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_parse"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()
        response_json = json.dumps(mock_agent_response)
        updates = processor._parse_response(response_json, sample_article)

        assert updates["summary_ja"] == "これはテスト記事の日本語要約です。"
        assert updates["category"] == "finance"

    def test_異常系_不正なJSONレスポンスでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """不正な JSON レスポンスでエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessor, AgentProcessorError

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_invalid_json"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                try:
                    return json.loads(response)
                except json.JSONDecodeError as e:
                    raise AgentProcessorError(
                        f"Invalid JSON response: {e}",
                        processor_name=self.processor_name,
                    ) from e

        processor = TestProcessor()

        with pytest.raises(AgentProcessorError, match="Invalid JSON"):
            processor._parse_response("invalid json {", sample_article)


class TestSDKNotInstalledError:
    """Test error handling when Claude Agent SDK is not installed."""

    def test_異常系_SDKが未インストールでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """Claude Agent SDK が未インストールの場合にエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessor, SDKNotInstalledError

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_sdk_error"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = TestProcessor()

        # claude_agent_sdk のインポートをモックして ImportError を発生させる
        with (
            patch.dict("sys.modules", {"claude_agent_sdk": None}),
            pytest.raises(SDKNotInstalledError),
        ):
            processor.process(sample_article)

    def test_正常系_SDKNotInstalledErrorにヒントメッセージが含まれる(self) -> None:
        """SDKNotInstalledError に解決策のヒントが含まれることを確認。"""
        from news.processors.agent_base import SDKNotInstalledError

        error = SDKNotInstalledError()
        error_message = str(error)

        # インストール方法のヒントが含まれる
        assert (
            "claude-agent-sdk" in error_message.lower()
            or "install" in error_message.lower()
        )


class TestAgentExecutionError:
    """Test error handling during agent execution."""

    def test_異常系_エージェント実行失敗でエラー(
        self,
        sample_article: Article,
    ) -> None:
        """エージェント実行が失敗した場合にエラーが発生することを確認。"""
        from news.processors.agent_base import AgentProcessor, AgentProcessorError

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_exec_error"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = TestProcessor()

        # Claude Agent SDK のモックを作成（実行時にエラーを発生）
        mock_sdk = MagicMock()
        mock_sdk.query = AsyncMock(side_effect=Exception("Agent execution failed"))

        with (
            patch.object(processor, "_get_sdk", return_value=mock_sdk),
            pytest.raises(AgentProcessorError, match="execution failed"),
        ):
            processor.process(sample_article)

    def test_異常系_タイムアウトでエラー(
        self,
        sample_article: Article,
    ) -> None:
        """エージェント実行がタイムアウトした場合にエラーが発生することを確認。"""
        import asyncio

        from news.processors.agent_base import AgentProcessor, AgentProcessorError

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_timeout"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = TestProcessor()

        # タイムアウトエラーをシミュレート（async iterator として動作するようにする）
        async def mock_query_with_timeout(
            *args: Any, **kwargs: Any
        ) -> AsyncIterator[Any]:
            raise asyncio.TimeoutError("Timeout")
            yield  # Make this an async generator

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_with_timeout

        with (
            patch.object(processor, "_get_sdk", return_value=mock_sdk),
            pytest.raises(AgentProcessorError, match=r"[Tt]imeout"),
        ):
            processor.process(sample_article)


class TestAgentProcessorProcess:
    """Test AgentProcessor.process method."""

    def test_正常系_processが新しいArticleを返す(
        self,
        sample_article: Article,
        mock_agent_response: dict[str, Any],
    ) -> None:
        """process が新しい Article を返すことを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_process"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        # Claude Agent SDK をモック
        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_agent_response)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(
            processor,
            "_get_sdk",
            return_value=mock_sdk,
        ):
            result = processor.process(sample_article)

        # 新しい Article が返される
        assert isinstance(result, Article)
        # 元の記事は変更されない
        assert sample_article.summary_ja is None
        # 新しい記事には要約が追加される
        assert result.summary_ja == mock_agent_response["summary_ja"]

    def test_正常系_processで元のArticleのフィールドが保持される(
        self,
        sample_article: Article,
        mock_agent_response: dict[str, Any],
    ) -> None:
        """process で元の Article のフィールドが保持されることを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_preserve"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_agent_response)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(
            processor,
            "_get_sdk",
            return_value=mock_sdk,
        ):
            result = processor.process(sample_article)

        # 元のフィールドが保持される
        assert str(result.url) == str(sample_article.url)
        assert result.title == sample_article.title
        assert result.published_at == sample_article.published_at
        assert result.source == sample_article.source
        assert result.summary == sample_article.summary


class TestAgentProcessorProcessBatch:
    """Test AgentProcessor.process_batch method."""

    def test_正常系_process_batchがArticleリストを返す(
        self,
        sample_articles: list[Article],
        mock_agent_response: dict[str, Any],
    ) -> None:
        """process_batch が Article のリストを返すことを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_batch"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_agent_response)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(
            processor,
            "_get_sdk",
            return_value=mock_sdk,
        ):
            results = processor.process_batch(sample_articles)

        assert isinstance(results, list)
        assert len(results) == len(sample_articles)
        assert all(isinstance(r, Article) for r in results)

    def test_正常系_process_batchが入力と同じ順序で結果を返す(
        self,
        sample_articles: list[Article],
        mock_agent_response: dict[str, Any],
    ) -> None:
        """process_batch が入力と同じ順序で結果を返すことを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_order"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_agent_response)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with patch.object(
            processor,
            "_get_sdk",
            return_value=mock_sdk,
        ):
            results = processor.process_batch(sample_articles)

        # 入力と同じ順序で返される
        for original, result in zip(sample_articles, results, strict=True):
            assert str(result.url) == str(original.url)
            assert result.title == original.title

    def test_エッジケース_空のリストでprocess_batch(self) -> None:
        """空のリストで process_batch を呼んだ場合、空のリストが返ることを確認。"""
        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_empty"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return {"summary_ja": response}

        processor = TestProcessor()
        results = processor.process_batch([])

        assert results == []


class TestConcreteSummarizerProcessor:
    """Test a concrete implementation of AgentProcessor for summarization."""

    def test_正常系_SummarizerProcessorがProcessorProtocolを満たす(self) -> None:
        """具象 SummarizerProcessor が ProcessorProtocol を満たすことを確認。"""
        from news.processors.agent_base import AgentProcessor

        class SummarizerProcessor(AgentProcessor):
            """要約を生成する AgentProcessor の具象実装。"""

            @property
            def processor_name(self) -> str:
                return "claude_summarizer"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"""以下の記事を日本語で要約してください。

タイトル: {article.title}
内容: {article.summary or "なし"}

JSON形式で回答してください:
{{"summary_ja": "日本語の要約"}}
"""

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = SummarizerProcessor()

        assert isinstance(processor, ProcessorProtocol)
        assert processor.processor_name == "claude_summarizer"
        assert processor.processor_type == ProcessorType.SUMMARIZER


class TestErrorClasses:
    """Test AgentProcessor error classes."""

    def test_正常系_AgentProcessorErrorがNewsErrorを継承する(self) -> None:
        """AgentProcessorError が NewsError を継承することを確認。"""
        from news.processors.agent_base import AgentProcessorError

        assert issubclass(AgentProcessorError, NewsError)

    def test_正常系_AgentProcessorErrorにprocessor_nameが含まれる(self) -> None:
        """AgentProcessorError に processor_name が含まれることを確認。"""
        from news.processors.agent_base import AgentProcessorError

        error = AgentProcessorError(
            message="Test error",
            processor_name="test_processor",
        )

        assert error.processor_name == "test_processor"
        assert "Test error" in str(error)

    def test_正常系_SDKNotInstalledErrorがAgentProcessorErrorを継承する(self) -> None:
        """SDKNotInstalledError が AgentProcessorError を継承することを確認。"""
        from news.processors.agent_base import AgentProcessorError, SDKNotInstalledError

        assert issubclass(SDKNotInstalledError, AgentProcessorError)


class TestAgentProcessorLogging:
    """Test AgentProcessor logging."""

    def test_正常系_処理開始時にログが出力される(
        self,
        sample_article: Article,
        mock_agent_response: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """処理開始時にログが出力されることを確認。"""
        import logging

        from news.processors.agent_base import AgentProcessor

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_log"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        async def mock_query_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            mock_message = MagicMock()
            mock_message.type = "text"
            mock_message.content = json.dumps(mock_agent_response)
            yield mock_message

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_generator

        with (
            caplog.at_level(logging.DEBUG, logger="news.processors.agent_base"),
            patch.object(
                processor,
                "_get_sdk",
                return_value=mock_sdk,
            ),
        ):
            processor.process(sample_article)

        # structlog の出力先に応じて capsys または caplog で確認
        captured = capsys.readouterr()
        log_text = captured.out + caplog.text
        assert "test_log" in log_text or "Processing article" in log_text

    def test_正常系_エラー時にログが出力される(
        self,
        sample_article: Article,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """エラー発生時にログが出力されることを確認。"""
        import logging

        from news.processors.agent_base import AgentProcessor, AgentProcessorError

        class TestProcessor(AgentProcessor):
            @property
            def processor_name(self) -> str:
                return "test_error_log"

            @property
            def processor_type(self) -> ProcessorType:
                return ProcessorType.SUMMARIZER

            def _build_prompt(self, article: Article) -> str:
                return f"Summarize: {article.title}"

            def _parse_response(
                self, response: str, article: Article
            ) -> dict[str, Any]:
                return json.loads(response)

        processor = TestProcessor()

        # async iterator としてエラーを発生させる
        async def mock_query_with_error(
            *args: Any, **kwargs: Any
        ) -> AsyncIterator[Any]:
            raise Exception("Test error")
            yield  # Make this an async generator

        mock_sdk = MagicMock()
        mock_sdk.query = mock_query_with_error

        with (
            caplog.at_level(logging.DEBUG, logger="news.processors.agent_base"),
            patch.object(processor, "_get_sdk", return_value=mock_sdk),
            pytest.raises(AgentProcessorError),
        ):
            processor.process(sample_article)

        # structlog の出力先に応じて capsys または caplog で確認
        captured = capsys.readouterr()
        log_text = (captured.out + caplog.text).lower()
        assert "error" in log_text or "failed" in log_text
