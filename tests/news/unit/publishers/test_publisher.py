"""Unit tests for the Publisher class.

Tests for the basic Publisher class structure including:
- Constructor initialization with NewsWorkflowConfig
- publish() method signature and behavior with no summary
- publish_batch() method signature

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
    PublicationStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
)

# Fixtures


@pytest.fixture
def sample_config() -> NewsWorkflowConfig:
    """Create a sample NewsWorkflowConfig for testing."""
    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index", "tech": "ai"},
        github_status_ids={"index": "test-index-id", "ai": "test-ai-id"},
        rss={"presets_file": "test.json"},  # type: ignore[arg-type]
        summarization=SummarizationConfig(
            prompt_template="Summarize this article in Japanese: {body}",
        ),
        github={  # type: ignore[arg-type]
            "project_number": 15,
            "project_id": "PVT_test",
            "status_field_id": "PVTSSF_test",
            "published_date_field_id": "PVTF_test",
            "repository": "YH-05/finance",
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
def sample_extracted_article(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create a sample ExtractedArticle with body text."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text="Full article content about the S&P 500 rally...",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )


@pytest.fixture
def sample_summary() -> StructuredSummary:
    """Create a sample StructuredSummary."""
    return StructuredSummary(
        overview="S&P 500が上昇した。",
        key_points=["ポイント1", "ポイント2"],
        market_impact="市場への影響",
        related_info="関連情報",
    )


@pytest.fixture
def summarized_article_with_summary(
    sample_extracted_article: ExtractedArticle,
    sample_summary: StructuredSummary,
) -> SummarizedArticle:
    """Create a SummarizedArticle with summary."""
    return SummarizedArticle(
        extracted=sample_extracted_article,
        summary=sample_summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def summarized_article_no_summary(
    sample_extracted_article: ExtractedArticle,
) -> SummarizedArticle:
    """Create a SummarizedArticle without summary (summarization failed)."""
    return SummarizedArticle(
        extracted=sample_extracted_article,
        summary=None,
        summarization_status=SummarizationStatus.SKIPPED,
        error_message="No body text available",
    )


# Tests


class TestPublisher:
    """Tests for the Publisher class basic structure."""

    def test_正常系_コンストラクタで設定を受け取る(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should accept NewsWorkflowConfig in constructor."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        assert publisher._config is sample_config
        assert publisher._repo == sample_config.github.repository
        assert publisher._project_id == sample_config.github.project_id
        assert publisher._project_number == sample_config.github.project_number
        assert publisher._status_field_id == sample_config.github.status_field_id
        assert (
            publisher._published_date_field_id
            == sample_config.github.published_date_field_id
        )

    def test_正常系_status_mappingが設定される(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should store status_mapping from config."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        assert publisher._status_mapping == sample_config.status_mapping
        assert publisher._status_ids == sample_config.github_status_ids

    def test_正常系_publishメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should have a publish() method."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Check method exists and is callable
        assert hasattr(publisher, "publish")
        assert callable(publisher.publish)

    def test_正常系_publish_batchメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should have a publish_batch() method."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Check method exists and is callable
        assert hasattr(publisher, "publish_batch")
        assert callable(publisher.publish_batch)


class TestPublishNoSummary:
    """Tests for publish() when article has no summary."""

    @pytest.mark.asyncio
    async def test_正常系_要約なしでSKIPPEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_no_summary: SummarizedArticle,
    ) -> None:
        """publish() should return SKIPPED status when summary is None."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        result = await publisher.publish(summarized_article_no_summary)

        assert result.publication_status == PublicationStatus.SKIPPED
        assert result.issue_number is None
        assert result.issue_url is None
        assert result.error_message == "No summary available"
        assert result.summarized is summarized_article_no_summary


class TestPublishBatch:
    """Tests for publish_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_空リストで空リストを返す(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """publish_batch() should return empty list for empty input."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        result = await publisher.publish_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_正常系_dry_runパラメータが受け付けられる(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_no_summary: SummarizedArticle,
    ) -> None:
        """publish_batch() should accept dry_run parameter."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Should not raise with dry_run parameter
        result = await publisher.publish_batch(
            [summarized_article_no_summary], dry_run=True
        )

        assert len(result) == 1
        # No summary -> SKIPPED regardless of dry_run
        assert result[0].publication_status == PublicationStatus.SKIPPED
