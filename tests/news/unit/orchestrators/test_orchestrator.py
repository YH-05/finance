"""Unit tests for the NewsWorkflowOrchestrator class.

Tests for the orchestrator that integrates:
Collector -> Extractor -> Summarizer -> Publisher pipeline.

Following TDD approach: Red -> Green -> Refactor
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.config.workflow import NewsWorkflowConfig, SummarizationConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    FailureRecord,
    PublicationStatus,
    PublishedArticle,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
    WorkflowResult,
)

# Fixtures


@pytest.fixture
def sample_config() -> NewsWorkflowConfig:
    """Create a sample NewsWorkflowConfig for testing."""
    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index", "tech": "ai", "finance": "finance"},
        github_status_ids={
            "index": "test-index-id",
            "ai": "test-ai-id",
            "finance": "test-finance-id",
        },
        rss={"presets_file": "data/config/rss-presets.json"},  # type: ignore[arg-type]
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
def sample_source_market() -> ArticleSource:
    """Create a sample ArticleSource with market category."""
    return ArticleSource(
        source_type=SourceType.RSS,
        source_name="CNBC Markets",
        category="market",
    )


@pytest.fixture
def sample_source_tech() -> ArticleSource:
    """Create a sample ArticleSource with tech category."""
    return ArticleSource(
        source_type=SourceType.RSS,
        source_name="Tech News",
        category="tech",
    )


@pytest.fixture
def sample_collected_article(sample_source_market: ArticleSource) -> CollectedArticle:
    """Create a sample CollectedArticle."""
    return CollectedArticle(
        url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
        title="Market Update: S&P 500 Rallies",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="Stocks rose on positive earnings reports.",
        source=sample_source_market,
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_collected_articles(
    sample_source_market: ArticleSource,
    sample_source_tech: ArticleSource,
) -> list[CollectedArticle]:
    """Create multiple sample CollectedArticles."""
    return [
        CollectedArticle(
            url="https://www.cnbc.com/article/1",  # type: ignore[arg-type]
            title="Market Update 1",
            published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            raw_summary="Summary 1",
            source=sample_source_market,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        ),
        CollectedArticle(
            url="https://www.cnbc.com/article/2",  # type: ignore[arg-type]
            title="Market Update 2",
            published=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            raw_summary="Summary 2",
            source=sample_source_market,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        ),
        CollectedArticle(
            url="https://tech.example.com/article/3",  # type: ignore[arg-type]
            title="Tech Update 3",
            published=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            raw_summary="Summary 3",
            source=sample_source_tech,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_extracted_article(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create a sample ExtractedArticle with success status."""
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
def sample_summarized_article(
    sample_extracted_article: ExtractedArticle,
    sample_summary: StructuredSummary,
) -> SummarizedArticle:
    """Create a sample SummarizedArticle with success status."""
    return SummarizedArticle(
        extracted=sample_extracted_article,
        summary=sample_summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def sample_published_article(
    sample_summarized_article: SummarizedArticle,
) -> PublishedArticle:
    """Create a sample PublishedArticle with success status."""
    return PublishedArticle(
        summarized=sample_summarized_article,
        issue_number=123,
        issue_url="https://github.com/YH-05/finance/issues/123",
        publication_status=PublicationStatus.SUCCESS,
    )


# Tests


class TestOrchestratorInit:
    """Tests for NewsWorkflowOrchestrator initialization."""

    def test_正常系_コンストラクタで設定を受け取る(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Orchestrator should accept NewsWorkflowConfig in constructor."""
        from news.orchestrator import NewsWorkflowOrchestrator

        orchestrator = NewsWorkflowOrchestrator(config=sample_config)

        assert orchestrator._config is sample_config

    def test_正常系_各コンポーネントが初期化される(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Orchestrator should initialize all pipeline components."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor,
            patch("news.orchestrator.Summarizer") as mock_summarizer,
            patch("news.orchestrator.Publisher") as mock_publisher,
        ):
            orchestrator = NewsWorkflowOrchestrator(config=sample_config)

            mock_collector.assert_called_once_with(sample_config)
            mock_extractor.assert_called_once_with(
                min_body_length=sample_config.extraction.min_body_length,
                max_retries=sample_config.extraction.max_retries,
                timeout_seconds=sample_config.extraction.timeout_seconds,
            )
            mock_summarizer.assert_called_once_with(sample_config)
            mock_publisher.assert_called_once_with(sample_config)


class TestOrchestratorRun:
    """Tests for run() method."""

    def test_正常系_runメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Orchestrator should have a run() method."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector"),
            patch("news.orchestrator.TrafilaturaExtractor"),
            patch("news.orchestrator.Summarizer"),
            patch("news.orchestrator.Publisher"),
        ):
            orchestrator = NewsWorkflowOrchestrator(config=sample_config)

            assert hasattr(orchestrator, "run")
            assert callable(orchestrator.run)

    @pytest.mark.asyncio
    async def test_正常系_runがWorkflowResultを返す(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """run() should return WorkflowResult."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=[])
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            assert isinstance(result, WorkflowResult)

    @pytest.mark.asyncio
    async def test_正常系_runが各ステージを順番に実行(
        self,
        sample_config: NewsWorkflowConfig,
        sample_collected_article: CollectedArticle,
        sample_extracted_article: ExtractedArticle,
        sample_summarized_article: SummarizedArticle,
        sample_published_article: PublishedArticle,
    ) -> None:
        """run() should execute all pipeline stages in order."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[sample_collected_article])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=sample_extracted_article)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(
                return_value=[sample_summarized_article]
            )
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(
                return_value=[sample_published_article]
            )
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Verify each stage was called
            mock_collector.collect.assert_called_once()
            mock_extractor.extract.assert_called()
            mock_summarizer.summarize_batch.assert_called_once()
            mock_publisher.publish_batch.assert_called_once()

            # Verify result counts
            assert result.total_collected == 1
            assert result.total_extracted == 1
            assert result.total_summarized == 1
            assert result.total_published == 1


class TestOrchestratorStatusFilter:
    """Tests for status filtering in run()."""

    @pytest.mark.asyncio
    async def test_正常系_statusesでフィルタリング(
        self,
        sample_config: NewsWorkflowConfig,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """run() should filter articles by statuses parameter."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=sample_collected_articles)
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(
                side_effect=lambda a: ExtractedArticle(
                    collected=a,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method="trafilatura",
                )
            )
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            # Filter to only "index" status (market category maps to index)
            result = await orchestrator.run(statuses=["index"])

            # Should only process market articles (2 of 3)
            assert mock_extractor.extract.call_count == 2


class TestOrchestratorMaxArticles:
    """Tests for max_articles limit in run()."""

    @pytest.mark.asyncio
    async def test_正常系_max_articlesで件数制限(
        self,
        sample_config: NewsWorkflowConfig,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """run() should limit articles to max_articles parameter."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=sample_collected_articles)
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(
                side_effect=lambda a: ExtractedArticle(
                    collected=a,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method="trafilatura",
                )
            )
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            # Limit to 2 articles
            result = await orchestrator.run(max_articles=2)

            # Should only process 2 articles
            assert mock_extractor.extract.call_count == 2


class TestOrchestratorDryRun:
    """Tests for dry_run mode in run()."""

    @pytest.mark.asyncio
    async def test_正常系_dry_runがPublisherに渡される(
        self,
        sample_config: NewsWorkflowConfig,
        sample_collected_article: CollectedArticle,
        sample_extracted_article: ExtractedArticle,
        sample_summarized_article: SummarizedArticle,
    ) -> None:
        """run() should pass dry_run parameter to publisher."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[sample_collected_article])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=sample_extracted_article)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(
                return_value=[sample_summarized_article]
            )
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            await orchestrator.run(dry_run=True)

            # Verify dry_run was passed to publisher
            mock_publisher.publish_batch.assert_called_once()
            call_kwargs = mock_publisher.publish_batch.call_args.kwargs
            assert call_kwargs.get("dry_run") is True


class TestOrchestratorSuccessFiltering:
    """Tests for filtering only successful articles at each stage."""

    @pytest.mark.asyncio
    async def test_正常系_抽出失敗の記事は要約に渡されない(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source_market: ArticleSource,
    ) -> None:
        """Only successfully extracted articles should be passed to summarizer."""
        from news.orchestrator import NewsWorkflowOrchestrator

        # Create articles
        collected1 = CollectedArticle(
            url="https://example.com/1",  # type: ignore[arg-type]
            title="Article 1",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )
        collected2 = CollectedArticle(
            url="https://example.com/2",  # type: ignore[arg-type]
            title="Article 2",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )

        # One success, one failure
        extracted_success = ExtractedArticle(
            collected=collected1,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        extracted_fail = ExtractedArticle(
            collected=collected2,
            body_text=None,
            extraction_status=ExtractionStatus.FAILED,
            extraction_method="trafilatura",
            error_message="Failed",
        )

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[collected1, collected2])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(
                side_effect=[extracted_success, extracted_fail]
            )
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Summarizer should only receive successful extractions
            call_args = mock_summarizer.summarize_batch.call_args
            passed_articles = call_args[0][0]
            assert len(passed_articles) == 1
            assert passed_articles[0].extraction_status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_正常系_要約失敗の記事は公開に渡されない(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source_market: ArticleSource,
    ) -> None:
        """Only successfully summarized articles should be passed to publisher."""
        from news.orchestrator import NewsWorkflowOrchestrator

        # Create articles
        collected = CollectedArticle(
            url="https://example.com/1",  # type: ignore[arg-type]
            title="Article 1",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        # One success, one failure
        summary = StructuredSummary(
            overview="Test",
            key_points=["Point"],
            market_impact="Impact",
        )
        summarized_success = SummarizedArticle(
            extracted=extracted,
            summary=summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )
        summarized_fail = SummarizedArticle(
            extracted=extracted,
            summary=None,
            summarization_status=SummarizationStatus.FAILED,
            error_message="Failed",
        )

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[collected, collected])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=extracted)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(
                return_value=[summarized_success, summarized_fail]
            )
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Publisher should only receive successful summaries
            call_args = mock_publisher.publish_batch.call_args
            passed_articles = call_args[0][0]
            assert len(passed_articles) == 1
            assert (
                passed_articles[0].summarization_status == SummarizationStatus.SUCCESS
            )


class TestOrchestratorWorkflowResult:
    """Tests for WorkflowResult construction."""

    @pytest.mark.asyncio
    async def test_正常系_WorkflowResultに正しい統計が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source_market: ArticleSource,
    ) -> None:
        """WorkflowResult should contain correct statistics."""
        from news.orchestrator import NewsWorkflowOrchestrator

        # Create test data
        collected = CollectedArticle(
            url="https://example.com/1",  # type: ignore[arg-type]
            title="Article 1",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        summary = StructuredSummary(
            overview="Test",
            key_points=["Point"],
            market_impact="Impact",
        )
        summarized = SummarizedArticle(
            extracted=extracted,
            summary=summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )
        published = PublishedArticle(
            summarized=summarized,
            issue_number=123,
            issue_url="https://github.com/YH-05/finance/issues/123",
            publication_status=PublicationStatus.SUCCESS,
        )

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[collected])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=extracted)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[summarized])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[published])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Verify statistics
            assert result.total_collected == 1
            assert result.total_extracted == 1
            assert result.total_summarized == 1
            assert result.total_published == 1
            assert len(result.published_articles) == 1
            assert result.published_articles[0] is published

    @pytest.mark.asyncio
    async def test_正常系_WorkflowResultに失敗レコードが含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source_market: ArticleSource,
    ) -> None:
        """WorkflowResult should contain failure records."""
        from news.orchestrator import NewsWorkflowOrchestrator

        # Create test data with failures
        collected = CollectedArticle(
            url="https://example.com/1",  # type: ignore[arg-type]
            title="Article 1",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )
        extracted_fail = ExtractedArticle(
            collected=collected,
            body_text=None,
            extraction_status=ExtractionStatus.FAILED,
            extraction_method="trafilatura",
            error_message="Extraction failed",
        )

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[collected])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=extracted_fail)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Verify failure records
            assert len(result.extraction_failures) == 1
            assert result.extraction_failures[0].stage == "extraction"
            assert result.extraction_failures[0].url == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_正常系_WorkflowResultに重複数が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source_market: ArticleSource,
    ) -> None:
        """WorkflowResult should contain duplicate count."""
        from news.orchestrator import NewsWorkflowOrchestrator

        # Create test data
        collected = CollectedArticle(
            url="https://example.com/1",  # type: ignore[arg-type]
            title="Article 1",
            source=sample_source_market,
            collected_at=datetime.now(tz=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        summary = StructuredSummary(
            overview="Test",
            key_points=["Point"],
            market_impact="Impact",
        )
        summarized = SummarizedArticle(
            extracted=extracted,
            summary=summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )
        published_dup = PublishedArticle(
            summarized=summarized,
            issue_number=None,
            issue_url=None,
            publication_status=PublicationStatus.DUPLICATE,
        )

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[collected])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor.extract = AsyncMock(return_value=extracted)
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[summarized])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[published_dup])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Verify duplicate count
            assert result.total_duplicates == 1
            assert result.total_published == 0

    @pytest.mark.asyncio
    async def test_正常系_WorkflowResultにタイムスタンプが含まれる(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """WorkflowResult should contain timestamps."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            result = await orchestrator.run()

            # Verify timestamps
            assert result.started_at is not None
            assert result.finished_at is not None
            assert result.started_at <= result.finished_at
            assert result.elapsed_seconds >= 0


class TestOrchestratorLogging:
    """Tests for logging at each stage."""

    @pytest.mark.asyncio
    async def test_正常系_各ステージでログが出力される(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """run() should log progress at each stage."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector") as mock_collector_cls,
            patch("news.orchestrator.TrafilaturaExtractor") as mock_extractor_cls,
            patch("news.orchestrator.Summarizer") as mock_summarizer_cls,
            patch("news.orchestrator.Publisher") as mock_publisher_cls,
            patch("news.orchestrator.logger") as mock_logger,
        ):
            # Setup mocks
            mock_collector = MagicMock()
            mock_collector.collect = AsyncMock(return_value=[])
            mock_collector_cls.return_value = mock_collector

            mock_extractor = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            mock_summarizer = MagicMock()
            mock_summarizer.summarize_batch = AsyncMock(return_value=[])
            mock_summarizer_cls.return_value = mock_summarizer

            mock_publisher = MagicMock()
            mock_publisher.publish_batch = AsyncMock(return_value=[])
            mock_publisher_cls.return_value = mock_publisher

            orchestrator = NewsWorkflowOrchestrator(config=sample_config)
            await orchestrator.run()

            # Verify logging calls exist
            info_calls = mock_logger.info.call_args_list
            assert len(info_calls) >= 4  # At least one per stage

            # Check for stage-specific logs
            log_messages = [str(call) for call in info_calls]
            assert any("Workflow started" in msg for msg in log_messages)
            assert any("Collect" in msg or "collect" in msg for msg in log_messages)


class TestOrchestratorBuildResult:
    """Tests for _build_result() helper method."""

    def test_正常系_build_resultが正しくWorkflowResultを生成(
        self,
        sample_config: NewsWorkflowConfig,
        sample_collected_article: CollectedArticle,
        sample_extracted_article: ExtractedArticle,
        sample_summarized_article: SummarizedArticle,
        sample_published_article: PublishedArticle,
    ) -> None:
        """_build_result should correctly construct WorkflowResult."""
        from news.orchestrator import NewsWorkflowOrchestrator

        with (
            patch("news.orchestrator.RSSCollector"),
            patch("news.orchestrator.TrafilaturaExtractor"),
            patch("news.orchestrator.Summarizer"),
            patch("news.orchestrator.Publisher"),
        ):
            orchestrator = NewsWorkflowOrchestrator(config=sample_config)

            started_at = datetime.now(tz=timezone.utc)
            finished_at = datetime.now(tz=timezone.utc)

            result = orchestrator._build_result(
                collected=[sample_collected_article],
                extracted=[sample_extracted_article],
                summarized=[sample_summarized_article],
                published=[sample_published_article],
                started_at=started_at,
                finished_at=finished_at,
            )

            assert isinstance(result, WorkflowResult)
            assert result.total_collected == 1
            assert result.total_extracted == 1
            assert result.total_summarized == 1
            assert result.total_published == 1
            assert result.started_at == started_at
            assert result.finished_at == finished_at
