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
from pathlib import Path
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

    def _log_stage_start(self, stage: str, description: str) -> None:
        """Log the start of a workflow stage with visual separator."""
        print(f"\n{'=' * 60}")
        print(f"[{stage}] {description}")
        print(f"{'=' * 60}")

    def _log_progress(
        self, current: int, total: int, message: str, *, is_error: bool = False
    ) -> None:
        """Log progress with count indicator."""
        prefix = "  ERROR" if is_error else "  "
        print(f"{prefix}[{current}/{total}] {message}")

    def _log_stage_complete(
        self, stage: str, success: int, total: int, *, extra: str = ""
    ) -> None:
        """Log stage completion with success rate."""
        rate = (success / total * 100) if total > 0 else 0
        extra_str = f" {extra}" if extra else ""
        print(f"  -> {stage}完了: {success}/{total} ({rate:.0f}%){extra_str}")

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

        # Show workflow configuration
        mode_str = "[DRY-RUN] " if dry_run else ""
        status_str = ", ".join(statuses) if statuses else "全て"
        limit_str = str(max_articles) if max_articles else "無制限"
        print(f"\n{mode_str}ニュース収集ワークフロー開始")
        print(f"  対象ステータス: {status_str}")
        print(f"  最大記事数: {limit_str}")

        # 1. Collect articles from RSS feeds
        self._log_stage_start("1/4", "RSSフィードから記事を収集")
        collected = await self._collector.collect(
            max_age_hours=self._config.filtering.max_age_hours
        )
        print(f"  収集完了: {len(collected)}件")

        # Apply status filtering
        if statuses:
            before_count = len(collected)
            collected = self._filter_by_status(collected, statuses)
            print(f"  ステータスフィルタ適用: {before_count} -> {len(collected)}件")

        # Apply max_articles limit
        if max_articles and len(collected) > max_articles:
            collected = collected[:max_articles]
            print(f"  記事数制限適用: {len(collected)}件")

        if not collected:
            print("  -> 処理対象の記事がありません")
            finished_at = datetime.now(timezone.utc)
            return self._build_empty_result(started_at, finished_at)

        # 2. Extract body text from articles
        self._log_stage_start("2/4", "記事本文を抽出")
        extracted = await self._extract_batch_with_progress(collected)
        extracted_success = [
            e for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS
        ]
        self._log_stage_complete("抽出", len(extracted_success), len(extracted))

        if not extracted_success:
            print("  -> 抽出成功した記事がありません")
            finished_at = datetime.now(timezone.utc)
            return self._build_result(
                collected=collected,
                extracted=extracted,
                summarized=[],
                published=[],
                started_at=started_at,
                finished_at=finished_at,
            )

        # 3. Summarize articles with AI
        self._log_stage_start("3/4", "AI要約を生成")
        summarized = await self._summarize_batch_with_progress(extracted_success)
        summarized_success = [
            s
            for s in summarized
            if s.summarization_status == SummarizationStatus.SUCCESS
        ]
        self._log_stage_complete("要約", len(summarized_success), len(summarized))

        if not summarized_success:
            print("  -> 要約成功した記事がありません")
            finished_at = datetime.now(timezone.utc)
            return self._build_result(
                collected=collected,
                extracted=extracted,
                summarized=summarized,
                published=[],
                started_at=started_at,
                finished_at=finished_at,
            )

        # 4. Publish articles to GitHub Issues
        stage_desc = (
            "GitHub Issueを作成" if not dry_run else "GitHub Issue作成 (dry-run)"
        )
        self._log_stage_start("4/4", stage_desc)
        published = await self._publish_batch_with_progress(summarized_success, dry_run)
        success_count = sum(
            1 for p in published if p.publication_status == PublicationStatus.SUCCESS
        )
        duplicate_count = sum(
            1 for p in published if p.publication_status == PublicationStatus.DUPLICATE
        )
        extra = f"(重複: {duplicate_count}件)" if duplicate_count > 0 else ""
        self._log_stage_complete("公開", success_count, len(published), extra=extra)

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

        # Save result to JSON file
        self._save_result(result)

        # Final summary
        elapsed = result.elapsed_seconds
        print(f"\n{'=' * 60}")
        print("ワークフロー完了")
        print(f"{'=' * 60}")
        print(f"  収集: {result.total_collected}件")
        print(f"  抽出: {result.total_extracted}件")
        print(f"  要約: {result.total_summarized}件")
        print(f"  公開: {result.total_published}件")
        if result.total_duplicates > 0:
            print(f"  重複: {result.total_duplicates}件")
        print(f"  処理時間: {elapsed:.1f}秒")

        return result

    async def _extract_batch_with_progress(
        self,
        articles: list[CollectedArticle],
    ) -> list[ExtractedArticle]:
        """Extract body text from articles with progress logging."""
        results: list[ExtractedArticle] = []
        total = len(articles)
        for i, article in enumerate(articles, 1):
            result = await self._extractor.extract(article)
            title = (
                article.title[:40] + "..." if len(article.title) > 40 else article.title
            )
            if result.extraction_status == ExtractionStatus.SUCCESS:
                self._log_progress(i, total, title)
            else:
                self._log_progress(
                    i, total, f"{title} - {result.error_message}", is_error=True
                )
                logger.error(
                    "Extraction failed",
                    url=str(article.url),
                    error=result.error_message,
                )
            results.append(result)
        return results

    async def _summarize_batch_with_progress(
        self,
        articles: list[ExtractedArticle],
    ) -> list[SummarizedArticle]:
        """Summarize articles with progress logging."""
        results: list[SummarizedArticle] = []
        total = len(articles)
        concurrency = self._config.summarization.concurrency

        # Process in batches for concurrency
        for batch_start in range(0, total, concurrency):
            batch_end = min(batch_start + concurrency, total)
            batch = articles[batch_start:batch_end]

            batch_results = await self._summarizer.summarize_batch(
                batch, concurrency=concurrency
            )

            for i, result in enumerate(batch_results):
                idx = batch_start + i + 1
                title = result.extracted.collected.title
                title = title[:40] + "..." if len(title) > 40 else title
                if result.summarization_status == SummarizationStatus.SUCCESS:
                    self._log_progress(idx, total, title)
                else:
                    self._log_progress(
                        idx, total, f"{title} - {result.error_message}", is_error=True
                    )
                    logger.error(
                        "Summarization failed",
                        url=str(result.extracted.collected.url),
                        error=result.error_message,
                    )
                results.append(result)

        return results

    async def _publish_batch_with_progress(
        self,
        articles: list[SummarizedArticle],
        dry_run: bool,
    ) -> list[PublishedArticle]:
        """Publish articles with progress logging."""
        published = await self._publisher.publish_batch(articles, dry_run=dry_run)
        total = len(published)

        for i, result in enumerate(published, 1):
            title = result.summarized.extracted.collected.title
            title = title[:40] + "..." if len(title) > 40 else title

            if result.publication_status == PublicationStatus.SUCCESS:
                issue_info = f"#{result.issue_number}" if result.issue_number else ""
                self._log_progress(i, total, f"{title} {issue_info}")
            elif result.publication_status == PublicationStatus.DUPLICATE:
                self._log_progress(i, total, f"{title} (重複スキップ)")
            else:
                self._log_progress(
                    i, total, f"{title} - {result.error_message}", is_error=True
                )
                logger.error(
                    "Publication failed",
                    url=str(result.summarized.extracted.collected.url),
                    error=result.error_message,
                )

        return published

    def _build_empty_result(
        self,
        started_at: datetime,
        finished_at: datetime,
    ) -> WorkflowResult:
        """Build an empty WorkflowResult when no articles to process."""
        return WorkflowResult(
            total_collected=0,
            total_extracted=0,
            total_summarized=0,
            total_published=0,
            total_duplicates=0,
            extraction_failures=[],
            summarization_failures=[],
            publication_failures=[],
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=(finished_at - started_at).total_seconds(),
            published_articles=[],
        )

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

    def _save_result(self, result: WorkflowResult) -> Path:
        """Save WorkflowResult to JSON file.

        Parameters
        ----------
        result : WorkflowResult
            Workflow execution result to save.

        Returns
        -------
        Path
            Path to the saved JSON file.

        Notes
        -----
        - Creates output directory if it doesn't exist
        - Filename includes timestamp in format: workflow-result-YYYY-MM-DDTHH-MM-SS.json
        - Uses Pydantic's model_dump_json for JSON serialization
        """
        output_dir = Path(self._config.output.result_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        output_path = output_dir / f"workflow-result-{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        logger.info("Result saved", path=str(output_path))

        return output_path


__all__ = [
    "NewsWorkflowOrchestrator",
]
