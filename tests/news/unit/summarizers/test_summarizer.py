"""Unit tests for the Summarizer class.

Tests for the basic Summarizer class structure including:
- Constructor initialization with NewsWorkflowConfig
- summarize() method signature and behavior with no body text
- summarize_batch() method signature

Following TDD approach: Red -> Green -> Refactor
"""

from datetime import datetime, timezone

import pytest

from news.config.workflow import NewsWorkflowConfig, SummarizationConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
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
