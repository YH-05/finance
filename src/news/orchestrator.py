"""Workflow orchestrator for news collection pipeline.

This module provides the NewsWorkflowOrchestrator class that integrates
all pipeline components: Collector -> Extractor -> Summarizer -> Publisher.

The orchestrator manages the workflow execution, filtering only successful
articles at each stage, and constructing comprehensive WorkflowResult.

Examples
--------
>>> from news.orchestrator import NewsWorkflowOrchestrator
>>> from news.config.workflow import load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> orchestrator = NewsWorkflowOrchestrator(config=config)
>>> result = await orchestrator.run(statuses=["index"], max_articles=10, dry_run=True)
>>> result.total_published
5
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from news.collectors.rss import RSSCollector
from news.extractors.trafilatura import TrafilaturaExtractor
from news.models import (
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    FailureRecord,
    PublicationStatus,
    PublishedArticle,
    SummarizationStatus,
    SummarizedArticle,
    WorkflowResult,
)
from news.publisher import Publisher
from news.summarizer import Summarizer
from news.utils.logging_config import get_logger

if TYPE_CHECKING:
    from news.config.workflow import NewsWorkflowConfig

logger = get_logger(__name__, module="orchestrator")


class NewsWorkflowOrchestrator:
    """Orchestrator for the news collection workflow pipeline.

    Integrates Collector -> Extractor -> Summarizer -> Publisher components
    into a unified workflow that processes articles through each stage.

    Parameters
    ----------
    config : NewsWorkflowConfig
        Workflow configuration containing settings for all components.

    Attributes
    ----------
    _config : NewsWorkflowConfig
        The workflow configuration.
    _collector : RSSCollector
        RSS feed collector component.
    _extractor : TrafilaturaExtractor
        Article body extractor component.
    _summarizer : Summarizer
        AI summarization component.
    _publisher : Publisher
        GitHub Issue publisher component.

    Examples
    --------
    >>> from news.orchestrator import NewsWorkflowOrchestrator
    >>> from news.config.workflow import load_config
    >>> config = load_config("config.yaml")
    >>> orchestrator = NewsWorkflowOrchestrator(config=config)
    >>> result = await orchestrator.run(dry_run=True)
    >>> result.total_published
    10

    Notes
    -----
    - Each stage only passes successful articles to the next stage
    - Failures are tracked in WorkflowResult failure records
    - Supports status filtering and max_articles limit
    - dry_run mode skips actual Issue creation
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        """Initialize the orchestrator with configuration.

        Parameters
        ----------
        config : NewsWorkflowConfig
            Workflow configuration for all components.
        """
        self._config = config
        self._collector = RSSCollector(config)
        self._extractor = TrafilaturaExtractor(
            min_body_length=config.extraction.min_body_length,
            max_retries=config.extraction.max_retries,
            timeout_seconds=config.extraction.timeout_seconds,
        )
        self._summarizer = Summarizer(config)
        self._publisher = Publisher(config)

        logger.debug(
            "NewsWorkflowOrchestrator initialized",
            extraction_concurrency=config.extraction.concurrency,
            summarization_concurrency=config.summarization.concurrency,
        )

    async def run(
        self,
        statuses: list[str] | None = None,
        max_articles: int | None = None,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """Execute the workflow pipeline.

        Runs the complete workflow: collect -> extract -> summarize -> publish.
        Each stage filters only successful articles to the next stage.

        Parameters
        ----------
        statuses : list[str] | None, optional
            Filter articles by status (GitHub Project status).
            Uses status_mapping to convert category to status.
            None means no filtering (process all).
        max_articles : int | None, optional
            Maximum number of articles to process.
            Applied after status filtering.
            None means no limit.
        dry_run : bool, optional
            If True, skip actual Issue creation.
            Default is False.

        Returns
        -------
        WorkflowResult
            Comprehensive result containing statistics, failure records,
            timestamps, and published articles.

        Examples
        --------
        >>> result = await orchestrator.run(statuses=["index"], max_articles=5)
        >>> print(f"Published: {result.total_published}/{result.total_collected}")

        >>> result = await orchestrator.run(dry_run=True)
        >>> print(f"Would publish: {result.total_summarized} articles")
        """
        started_at = datetime.now(timezone.utc)
        logger.info(
            "Workflow started",
            statuses=statuses,
            max_articles=max_articles,
            dry_run=dry_run,
        )

        # 1. Collect articles from RSS feeds
        logger.info("Collecting articles from RSS feeds...")
        collected = await self._collector.collect(
            max_age_hours=self._config.filtering.max_age_hours
        )
        logger.info("Collected articles", count=len(collected))

        # Apply status filtering
        if statuses:
            collected = self._filter_by_status(collected, statuses)
            logger.info("Filtered by status", count=len(collected), statuses=statuses)

        # Apply max_articles limit
        if max_articles:
            collected = collected[:max_articles]
            logger.info("Applied max_articles limit", count=len(collected))

        # 2. Extract body text from articles
        logger.info("Extracting article body text...")
        extracted = await self._extract_batch(collected)
        extracted_success = [
            e for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS
        ]
        logger.info(
            "Extracted articles",
            success=len(extracted_success),
            total=len(extracted),
        )

        # 3. Summarize articles with AI
        logger.info("Summarizing articles with AI...")
        summarized = await self._summarizer.summarize_batch(
            extracted_success,
            concurrency=self._config.summarization.concurrency,
        )
        summarized_success = [
            s
            for s in summarized
            if s.summarization_status == SummarizationStatus.SUCCESS
        ]
        logger.info(
            "Summarized articles",
            success=len(summarized_success),
            total=len(summarized),
        )

        # 4. Publish articles to GitHub Issues
        logger.info("Publishing articles to GitHub Issues...")
        published = await self._publisher.publish_batch(
            summarized_success,
            dry_run=dry_run,
        )
        logger.info(
            "Published articles",
            success=sum(
                1
                for p in published
                if p.publication_status == PublicationStatus.SUCCESS
            ),
            total=len(published),
        )

        finished_at = datetime.now(timezone.utc)

        # Build and return result
        result = self._build_result(
            collected=collected,
            extracted=extracted,
            summarized=summarized,
            published=published,
            started_at=started_at,
            finished_at=finished_at,
        )

        logger.info(
            "Workflow completed",
            total_collected=result.total_collected,
            total_extracted=result.total_extracted,
            total_summarized=result.total_summarized,
            total_published=result.total_published,
            total_duplicates=result.total_duplicates,
            elapsed_seconds=result.elapsed_seconds,
        )

        return result

    def _filter_by_status(
        self,
        articles: list[CollectedArticle],
        statuses: list[str],
    ) -> list[CollectedArticle]:
        """Filter articles by their mapped status.

        Parameters
        ----------
        articles : list[CollectedArticle]
            Articles to filter.
        statuses : list[str]
            Status values to include.

        Returns
        -------
        list[CollectedArticle]
            Filtered articles.
        """
        result = []
        for article in articles:
            category = article.source.category
            # Get the status from category mapping
            status = self._config.status_mapping.get(category, "finance")
            if status in statuses:
                result.append(article)
        return result

    async def _extract_batch(
        self,
        articles: list[CollectedArticle],
    ) -> list[ExtractedArticle]:
        """Extract body text from a batch of articles.

        Parameters
        ----------
        articles : list[CollectedArticle]
            Articles to extract.

        Returns
        -------
        list[ExtractedArticle]
            Extraction results.
        """
        results: list[ExtractedArticle] = []
        for article in articles:
            result = await self._extractor.extract(article)
            results.append(result)
        return results

    def _build_result(
        self,
        collected: list[CollectedArticle],
        extracted: list[ExtractedArticle],
        summarized: list[SummarizedArticle],
        published: list[PublishedArticle],
        started_at: datetime,
        finished_at: datetime,
    ) -> WorkflowResult:
        """Build WorkflowResult from pipeline outputs.

        Parameters
        ----------
        collected : list[CollectedArticle]
            Articles collected from RSS feeds.
        extracted : list[ExtractedArticle]
            Extraction results.
        summarized : list[SummarizedArticle]
            Summarization results.
        published : list[PublishedArticle]
            Publication results.
        started_at : datetime
            Workflow start timestamp.
        finished_at : datetime
            Workflow end timestamp.

        Returns
        -------
        WorkflowResult
            Comprehensive workflow result.
        """
        # Count successful at each stage
        total_extracted = sum(
            1 for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS
        )
        total_summarized = sum(
            1
            for s in summarized
            if s.summarization_status == SummarizationStatus.SUCCESS
        )
        total_published = sum(
            1 for p in published if p.publication_status == PublicationStatus.SUCCESS
        )
        total_duplicates = sum(
            1 for p in published if p.publication_status == PublicationStatus.DUPLICATE
        )

        # Build failure records
        extraction_failures = [
            FailureRecord(
                url=str(e.collected.url),
                title=e.collected.title,
                stage="extraction",
                error=e.error_message or "Unknown error",
            )
            for e in extracted
            if e.extraction_status != ExtractionStatus.SUCCESS
        ]

        summarization_failures = [
            FailureRecord(
                url=str(s.extracted.collected.url),
                title=s.extracted.collected.title,
                stage="summarization",
                error=s.error_message or "Unknown error",
            )
            for s in summarized
            if s.summarization_status != SummarizationStatus.SUCCESS
        ]

        publication_failures = [
            FailureRecord(
                url=str(p.summarized.extracted.collected.url),
                title=p.summarized.extracted.collected.title,
                stage="publication",
                error=p.error_message or "Unknown error",
            )
            for p in published
            if p.publication_status == PublicationStatus.FAILED
        ]

        # Get successfully published articles
        published_articles = [
            p for p in published if p.publication_status == PublicationStatus.SUCCESS
        ]

        elapsed_seconds = (finished_at - started_at).total_seconds()

        return WorkflowResult(
            total_collected=len(collected),
            total_extracted=total_extracted,
            total_summarized=total_summarized,
            total_published=total_published,
            total_duplicates=total_duplicates,
            extraction_failures=extraction_failures,
            summarization_failures=summarization_failures,
            publication_failures=publication_failures,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
            published_articles=published_articles,
        )


__all__ = [
    "NewsWorkflowOrchestrator",
]
