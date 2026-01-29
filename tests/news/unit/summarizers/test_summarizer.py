"""Unit tests for the Summarizer class.

Tests for the basic Summarizer class structure including:
- Constructor initialization with NewsWorkflowConfig
- summarize() method signature and behavior with no body text
- summarize_batch() method signature
- Claude SDK integration (P4-002)

Following TDD approach: Red -> Green -> Refactor
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from news.config.workflow import NewsWorkflowConfig, SummarizationConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
)

# Fixtures


@pytest.fixture
def sample_config() -> NewsWorkflowConfig:
    """Create a sample NewsWorkflowConfig for testing."""
    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index"},
        github_status_ids={"index": "test-id"},
        rss={"presets_file": "test.json"},  # type: ignore[arg-type]
        summarization=SummarizationConfig(
            prompt_template="Summarize this article in Japanese: {body}",
        ),
        github={  # type: ignore[arg-type]
            "project_number": 15,
            "project_id": "PVT_test",
            "status_field_id": "PVTSSF_test",
            "published_date_field_id": "PVTF_test",
            "repository": "owner/repo",
        },
        output={"result_dir": "data/exports"},  # type: ignore[arg-type]
    )


@pytest.fixture
def sample_source() -> ArticleSource:
    """Create a sample ArticleSource."""
    return ArticleSource(
        source_type=SourceType.RSS,
        source_name="CNBC Markets",
        category="market",
    )


@pytest.fixture
def sample_collected_article(sample_source: ArticleSource) -> CollectedArticle:
    """Create a sample CollectedArticle."""
    return CollectedArticle(
        url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
        title="Market Update: S&P 500 Rallies",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="Stocks rose on positive earnings reports.",
        source=sample_source,
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def extracted_article_with_body(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create an ExtractedArticle with body text."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text="Full article content about the S&P 500 rally...",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )


@pytest.fixture
def extracted_article_no_body(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create an ExtractedArticle without body text (extraction failed)."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text=None,
        extraction_status=ExtractionStatus.FAILED,
        extraction_method="trafilatura",
        error_message="Failed to extract body text",
    )


# Tests


class TestSummarizer:
    """Tests for the Summarizer class."""

    def test_正常系_コンストラクタで設定を受け取る(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should accept NewsWorkflowConfig in constructor."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        assert summarizer._config is sample_config
        assert (
            summarizer._prompt_template == sample_config.summarization.prompt_template
        )

    def test_正常系_summarizeメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should have a summarize() method."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Check method exists and is callable
        assert hasattr(summarizer, "summarize")
        assert callable(summarizer.summarize)

    def test_正常系_summarize_batchメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should have a summarize_batch() method."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Check method exists and is callable
        assert hasattr(summarizer, "summarize_batch")
        assert callable(summarizer.summarize_batch)


class TestSummarizeNoBodyText:
    """Tests for summarize() when article has no body text."""

    @pytest.mark.asyncio
    async def test_正常系_本文なしでSKIPPEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_no_body: ExtractedArticle,
    ) -> None:
        """summarize() should return SKIPPED status when body_text is None."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        result = await summarizer.summarize(extracted_article_no_body)

        assert result.summarization_status == SummarizationStatus.SKIPPED
        assert result.summary is None
        assert result.error_message == "No body text available"
        assert result.extracted is extracted_article_no_body

    @pytest.mark.asyncio
    async def test_正常系_本文ありで処理継続(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize() should not immediately return SKIPPED when body_text exists.

        Note: This test only verifies the basic flow. Actual Claude SDK integration
        is handled in P4-002.
        """
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # For P4-001, we just verify the method doesn't return SKIPPED for valid body
        # The actual implementation will be completed in P4-002
        result = await summarizer.summarize(extracted_article_with_body)

        # Should not be SKIPPED since body_text is present
        assert result.summarization_status != SummarizationStatus.SKIPPED


class TestSummarizeBatch:
    """Tests for summarize_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_空リストで空リストを返す(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """summarize_batch() should return empty list for empty input."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        result = await summarizer.summarize_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_正常系_複数記事を処理できる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_no_body: ExtractedArticle,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize_batch() should process multiple articles."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        articles = [extracted_article_no_body, extracted_article_with_body]

        result = await summarizer.summarize_batch(articles, concurrency=2)

        assert len(result) == 2
        # First article (no body) should be SKIPPED
        assert result[0].summarization_status == SummarizationStatus.SKIPPED


class TestSummarizerClaudeIntegration:
    """Tests for Claude SDK integration (P4-002)."""

    def test_正常系_Anthropicクライアントを使用している(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Summarizer should use Anthropic client."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)

            # Verify Anthropic client was instantiated
            mock_anthropic.assert_called_once()
            assert summarizer._client is mock_client

    def test_正常系_プロンプトテンプレートが設定から読み込まれる(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Prompt template should be loaded from config."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic"):
            summarizer = Summarizer(config=sample_config)

            # Verify prompt template is loaded from config
            assert (
                summarizer._prompt_template
                == sample_config.summarization.prompt_template
            )

    @pytest.mark.asyncio
    async def test_正常系_記事情報がプロンプトに含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Article info (title, source, published, body) should be included in prompt."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            # Setup mock response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = '{"overview": "Test", "key_points": ["Point 1"], "market_impact": "Impact", "related_info": null}'
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)
            await summarizer.summarize(extracted_article_with_body)

            # Verify messages.create was called
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args.kwargs
            prompt_content = call_kwargs["messages"][0]["content"]

            # Verify article info is in the prompt
            article = extracted_article_with_body.collected
            assert article.title in prompt_content
            assert article.source.source_name in prompt_content
            assert extracted_article_with_body.body_text in prompt_content

    @pytest.mark.asyncio
    async def test_正常系_Claudeのレスポンスが取得できる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Claude response should be parsed into StructuredSummary."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            # Setup mock response with valid JSON
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = """{
                "overview": "S&P 500が上昇した。",
                "key_points": ["ポイント1", "ポイント2"],
                "market_impact": "市場への影響",
                "related_info": "関連情報"
            }"""
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)
            result = await summarizer.summarize(extracted_article_with_body)

            # Verify result
            assert result.summarization_status == SummarizationStatus.SUCCESS
            assert result.summary is not None
            assert isinstance(result.summary, StructuredSummary)
            assert result.summary.overview == "S&P 500が上昇した。"
            assert result.summary.key_points == ["ポイント1", "ポイント2"]
            assert result.summary.market_impact == "市場への影響"
            assert result.summary.related_info == "関連情報"

    @pytest.mark.asyncio
    async def test_正常系_モデルとmax_tokensが正しく設定される(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Model and max_tokens should be properly configured."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            # Setup mock response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = '{"overview": "Test", "key_points": ["Point 1"], "market_impact": "Impact", "related_info": null}'
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)
            await summarizer.summarize(extracted_article_with_body)

            # Verify model and max_tokens
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 1024

    @pytest.mark.asyncio
    async def test_異常系_APIエラーでFAILEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """API error should result in FAILED status."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            # Setup mock to raise exception
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)
            result = await summarizer.summarize(extracted_article_with_body)

            assert result.summarization_status == SummarizationStatus.FAILED
            assert result.summary is None
            assert result.error_message is not None
            assert "API Error" in result.error_message

    @pytest.mark.asyncio
    async def test_異常系_JSONパースエラーでFAILEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """JSON parse error should result in FAILED status."""
        from news.summarizer import Summarizer

        with patch("news.summarizer.Anthropic") as mock_anthropic:
            # Setup mock response with invalid JSON
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "This is not valid JSON"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            summarizer = Summarizer(config=sample_config)
            result = await summarizer.summarize(extracted_article_with_body)

            assert result.summarization_status == SummarizationStatus.FAILED
            assert result.summary is None
            assert result.error_message is not None
