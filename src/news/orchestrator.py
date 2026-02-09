"""Workflow orchestrator for news collection pipeline.

This module provides the NewsWorkflowOrchestrator class that integrates
all pipeline components into a unified workflow.

Pipeline formats:
- per_category (default): Collect -> Extract -> Summarize -> Group -> Export -> Publish
- per_article (legacy): Collect -> Extract -> Summarize -> Publish

The orchestrator manages the workflow execution, filtering only successful
articles at each stage, and constructing comprehensive WorkflowResult.

Examples
--------
>>> from news.orchestrator import NewsWorkflowOrchestrator
>>> from news.config.models import load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> orchestrator = NewsWorkflowOrchestrator(config=config)
>>> result = await orchestrator.run(statuses=["index"], max_articles=10, dry_run=True)
>>> result.total_published
5
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from news.collectors.rss import RSSCollector
from news.extractors.trafilatura import TrafilaturaExtractor
from news.grouper import ArticleGrouper
from news.markdown_generator import MarkdownExporter
from news.models import (
    CategoryPublishResult,
    CollectedArticle,
    DomainExtractionRate,
    ExtractedArticle,
    ExtractionStatus,
    FailureRecord,
    FeedError,
    PublicationStatus,
    PublishedArticle,
    StageMetrics,
    SummarizationStatus,
    SummarizedArticle,
    WorkflowResult,
)
from news.publisher import Publisher
from news.summarizer import Summarizer
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from news.config.models import NewsWorkflowConfig

logger = get_logger(__name__, module="orchestrator")


class NewsWorkflowOrchestrator:
    """Orchestrator for the news collection workflow pipeline.

    Integrates all pipeline components into a unified workflow.

    Pipeline formats:
    - per_category: Collect -> Extract -> Summarize -> Group -> Export -> Publish
    - per_article: Collect -> Extract -> Summarize -> Publish (legacy)

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
    _grouper : ArticleGrouper
        Article grouper for category-based publishing.
    _exporter : MarkdownExporter
        Markdown exporter for category-based content.
    _publish_format : str
        Publishing format: "per_category" or "per_article".

    Examples
    --------
    >>> from news.orchestrator import NewsWorkflowOrchestrator
    >>> from news.config.models import load_config
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
    - export_only mode exports Markdown without creating Issues
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
        self._grouper = ArticleGrouper(
            status_mapping=config.status_mapping,
            category_labels=config.category_labels,
        )
        self._exporter = MarkdownExporter()
        self._publish_format = config.publishing.format

        logger.debug(
            "NewsWorkflowOrchestrator initialized",
            extraction_concurrency=config.extraction.concurrency,
            summarization_concurrency=config.summarization.concurrency,
            publish_format=self._publish_format,
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
        export_only: bool = False,
    ) -> WorkflowResult:
        """Execute the workflow pipeline.

        Runs the complete workflow based on the configured publishing format:
        - per_category: collect -> extract -> summarize -> group -> export -> publish
        - per_article: collect -> extract -> summarize -> publish (legacy)

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
        export_only : bool, optional
            If True, export Markdown only without creating Issues.
            Only effective when format is "per_category".
            Default is False.

        Returns
        -------
        WorkflowResult
            Comprehensive result containing statistics, failure records,
            timestamps, published articles, and category results.

        Examples
        --------
        >>> result = await orchestrator.run(statuses=["index"], max_articles=5)
        >>> print(f"Published: {result.total_published}/{result.total_collected}")

        >>> result = await orchestrator.run(dry_run=True)
        >>> print(f"Would publish: {result.total_summarized} articles")

        >>> result = await orchestrator.run(export_only=True)
        >>> print(f"Exported {len(result.category_results)} categories")
        """
        is_per_category = self._publish_format == "per_category"
        total_stages = 6 if is_per_category else 4

        started_at = datetime.now(timezone.utc)
        stage_metrics_list: list[StageMetrics] = []

        # Show workflow configuration
        mode_parts: list[str] = []
        if dry_run:
            mode_parts.append("DRY-RUN")
        if export_only:
            mode_parts.append("EXPORT-ONLY")
        mode_str = f"[{', '.join(mode_parts)}] " if mode_parts else ""
        status_str = ", ".join(statuses) if statuses else "全て"
        limit_str = str(max_articles) if max_articles else "無制限"
        format_str = "カテゴリ別" if is_per_category else "記事別（レガシー）"
        print(f"\n{mode_str}ニュース収集ワークフロー開始")
        print(f"  対象ステータス: {status_str}")
        print(f"  最大記事数: {limit_str}")
        print(f"  公開形式: {format_str}")

        # 1. Collect articles from RSS feeds
        self._log_stage_start(f"1/{total_stages}", "RSSフィードから記事を収集")
        stage_start = time.monotonic()
        collected = await self._collector.collect(
            max_age_hours=self._config.filtering.max_age_hours
        )
        feed_errors = self._collector.feed_errors
        stage_elapsed = time.monotonic() - stage_start
        stage_metrics_list.append(
            StageMetrics(
                stage="collection",
                elapsed_seconds=round(stage_elapsed, 2),
                item_count=len(collected),
            )
        )
        logger.info(
            "Stage completed",
            stage="collection",
            elapsed_seconds=round(stage_elapsed, 2),
            item_count=len(collected),
        )
        print(f"  収集完了: {len(collected)}件 ({stage_elapsed:.1f}秒)")

        # Apply status filtering
        if statuses:
            before_count = len(collected)
            collected = self._filter_by_status(collected, statuses)
            print(f"  ステータスフィルタ適用: {before_count} -> {len(collected)}件")

        # Apply max_articles limit
        if max_articles and len(collected) > max_articles:
            collected = collected[:max_articles]
            print(f"  記事数制限適用: {len(collected)}件")

        # Early duplicate check (before extraction)
        existing_urls = await self._publisher.get_existing_urls()
        before_dedup = len(collected)
        collected = [
            a
            for a in collected
            if not self._publisher.is_duplicate_url(str(a.url), existing_urls)
        ]
        early_dedup_count = before_dedup - len(collected)
        if early_dedup_count > 0:
            print(
                f"  重複除外: {before_dedup} -> {len(collected)}件"
                f" (重複: {early_dedup_count}件)"
            )

        if not collected:
            print("  -> 処理対象の記事がありません")
            finished_at = datetime.now(timezone.utc)
            result = self._build_empty_result(
                started_at,
                finished_at,
                feed_errors=feed_errors,
                stage_metrics=stage_metrics_list,
            )
            self._save_result(result)
            return result

        # 2. Extract body text from articles
        self._log_stage_start(f"2/{total_stages}", "記事本文を抽出")
        stage_start = time.monotonic()
        extracted = await self._extract_batch_with_progress(collected)
        stage_elapsed = time.monotonic() - stage_start
        extracted_success = [
            e for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS
        ]
        stage_metrics_list.append(
            StageMetrics(
                stage="extraction",
                elapsed_seconds=round(stage_elapsed, 2),
                item_count=len(extracted),
            )
        )
        logger.info(
            "Stage completed",
            stage="extraction",
            elapsed_seconds=round(stage_elapsed, 2),
            item_count=len(extracted),
            success_count=len(extracted_success),
        )
        self._log_stage_complete(
            "抽出",
            len(extracted_success),
            len(extracted),
            extra=f"({stage_elapsed:.1f}秒)",
        )

        # Compute domain extraction rates
        domain_rates = self._compute_domain_extraction_rates(extracted)

        if not extracted_success:
            print("  -> 抽出成功した記事がありません")
            finished_at = datetime.now(timezone.utc)
            result = self._build_result(
                collected=collected,
                extracted=extracted,
                summarized=[],
                published=[],
                started_at=started_at,
                finished_at=finished_at,
                early_duplicates=early_dedup_count,
                feed_errors=feed_errors,
                stage_metrics=stage_metrics_list,
                domain_extraction_rates=domain_rates,
            )
            self._save_result(result)
            return result

        # 3. Summarize articles with AI
        self._log_stage_start(f"3/{total_stages}", "AI要約を生成")
        stage_start = time.monotonic()
        summarized = await self._summarize_batch_with_progress(extracted_success)
        stage_elapsed = time.monotonic() - stage_start
        summarized_success = [
            s
            for s in summarized
            if s.summarization_status == SummarizationStatus.SUCCESS
        ]
        stage_metrics_list.append(
            StageMetrics(
                stage="summarization",
                elapsed_seconds=round(stage_elapsed, 2),
                item_count=len(summarized),
            )
        )
        logger.info(
            "Stage completed",
            stage="summarization",
            elapsed_seconds=round(stage_elapsed, 2),
            item_count=len(summarized),
            success_count=len(summarized_success),
        )
        self._log_stage_complete(
            "要約",
            len(summarized_success),
            len(summarized),
            extra=f"({stage_elapsed:.1f}秒)",
        )

        if not summarized_success:
            print("  -> 要約成功した記事がありません")
            finished_at = datetime.now(timezone.utc)
            result = self._build_result(
                collected=collected,
                extracted=extracted,
                summarized=summarized,
                published=[],
                started_at=started_at,
                finished_at=finished_at,
                early_duplicates=early_dedup_count,
                feed_errors=feed_errors,
                stage_metrics=stage_metrics_list,
                domain_extraction_rates=domain_rates,
            )
            self._save_result(result)
            return result

        # Branch based on publishing format
        published: list[PublishedArticle] = []
        category_results: list[CategoryPublishResult] = []

        if is_per_category:
            # 4. Group articles by category
            self._log_stage_start(f"4/{total_stages}", "カテゴリ別にグループ化")
            stage_start = time.monotonic()
            groups = self._grouper.group(summarized_success)
            stage_elapsed = time.monotonic() - stage_start
            stage_metrics_list.append(
                StageMetrics(
                    stage="grouping",
                    elapsed_seconds=round(stage_elapsed, 2),
                    item_count=len(groups),
                )
            )
            logger.info(
                "Stage completed",
                stage="grouping",
                elapsed_seconds=round(stage_elapsed, 2),
                item_count=len(groups),
            )
            print(f"  グループ数: {len(groups)}件 ({stage_elapsed:.1f}秒)")
            for group in groups:
                print(
                    f"    [{group.category_label}] {group.date}: "
                    f"{len(group.articles)}件"
                )

            # 5. Export Markdown files (if enabled)
            if self._config.publishing.export_markdown:
                self._log_stage_start(
                    f"5/{total_stages}", "Markdownファイルをエクスポート"
                )
                stage_start = time.monotonic()
                export_dir = Path(self._config.publishing.export_dir)
                for group in groups:
                    export_path = self._exporter.export(group, export_dir=export_dir)
                    print(f"  -> {export_path}")
                stage_elapsed = time.monotonic() - stage_start
                stage_metrics_list.append(
                    StageMetrics(
                        stage="export",
                        elapsed_seconds=round(stage_elapsed, 2),
                        item_count=len(groups),
                    )
                )
                logger.info(
                    "Stage completed",
                    stage="export",
                    elapsed_seconds=round(stage_elapsed, 2),
                    item_count=len(groups),
                )
            else:
                self._log_stage_start(
                    f"5/{total_stages}", "Markdownエクスポート (スキップ)"
                )
                print("  -> export_markdown=False のためスキップ")

            # 6. Publish category Issues (unless export_only)
            if export_only:
                self._log_stage_start(
                    f"6/{total_stages}",
                    "GitHub Issue作成 (export-only: スキップ)",
                )
                print("  -> export-only モードのためスキップ")
            else:
                stage_desc = (
                    "カテゴリ別GitHub Issueを作成"
                    if not dry_run
                    else "カテゴリ別GitHub Issue作成 (dry-run)"
                )
                self._log_stage_start(f"6/{total_stages}", stage_desc)
                stage_start = time.monotonic()
                category_results = await self._publisher.publish_category_batch(
                    groups, dry_run=dry_run
                )
                stage_elapsed = time.monotonic() - stage_start
                stage_metrics_list.append(
                    StageMetrics(
                        stage="publishing",
                        elapsed_seconds=round(stage_elapsed, 2),
                        item_count=len(category_results),
                    )
                )
                logger.info(
                    "Stage completed",
                    stage="publishing",
                    elapsed_seconds=round(stage_elapsed, 2),
                    item_count=len(category_results),
                )
                success_count = sum(
                    1 for r in category_results if r.status == PublicationStatus.SUCCESS
                )
                duplicate_count = sum(
                    1
                    for r in category_results
                    if r.status == PublicationStatus.DUPLICATE
                )
                extra_parts: list[str] = []
                if duplicate_count > 0:
                    extra_parts.append(f"重複: {duplicate_count}件")
                extra_parts.append(f"{stage_elapsed:.1f}秒")
                extra = f"({', '.join(extra_parts)})"
                self._log_stage_complete(
                    "公開", success_count, len(category_results), extra=extra
                )

        else:
            # Legacy per-article publishing (4 stages)
            stage_desc = (
                "GitHub Issueを作成" if not dry_run else "GitHub Issue作成 (dry-run)"
            )
            self._log_stage_start(f"4/{total_stages}", stage_desc)
            stage_start = time.monotonic()
            published = await self._publish_batch_with_progress(
                summarized_success, dry_run
            )
            stage_elapsed = time.monotonic() - stage_start
            stage_metrics_list.append(
                StageMetrics(
                    stage="publishing",
                    elapsed_seconds=round(stage_elapsed, 2),
                    item_count=len(published),
                )
            )
            logger.info(
                "Stage completed",
                stage="publishing",
                elapsed_seconds=round(stage_elapsed, 2),
                item_count=len(published),
            )
            success_count = sum(
                1
                for p in published
                if p.publication_status == PublicationStatus.SUCCESS
            )
            duplicate_count = sum(
                1
                for p in published
                if p.publication_status == PublicationStatus.DUPLICATE
            )
            extra_parts_pub: list[str] = []
            if duplicate_count > 0:
                extra_parts_pub.append(f"重複: {duplicate_count}件")
            extra_parts_pub.append(f"{stage_elapsed:.1f}秒")
            extra = f"({', '.join(extra_parts_pub)})"
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
            early_duplicates=early_dedup_count,
            feed_errors=feed_errors,
            category_results=category_results,
            stage_metrics=stage_metrics_list,
            domain_extraction_rates=domain_rates,
        )

        # Save result to JSON file
        self._save_result(result)

        # Final summary
        elapsed = result.elapsed_seconds
        print(f"\n{'=' * 60}")
        print("ワークフロー完了")
        print(f"{'=' * 60}")
        print(f"  収集: {result.total_collected}件")
        if result.feed_errors:
            print(f"  フィードエラー: {len(result.feed_errors)}件")
        print(f"  抽出: {result.total_extracted}件")
        print(f"  要約: {result.total_summarized}件")
        if is_per_category and category_results:
            cat_published = sum(
                1 for r in category_results if r.status == PublicationStatus.SUCCESS
            )
            print(f"  カテゴリ別公開: {cat_published}/{len(category_results)}件")
        else:
            print(f"  公開: {result.total_published}件")
        if result.total_early_duplicates > 0:
            print(f"  重複除外（早期）: {result.total_early_duplicates}件")
        if result.total_duplicates > 0:
            print(f"  重複（公開時）: {result.total_duplicates}件")
        print(f"  処理時間: {elapsed:.1f}秒")

        # Stage timing summary
        if result.stage_metrics:
            print("\n  ステージ別処理時間:")
            for sm in result.stage_metrics:
                print(f"    {sm.stage}: {sm.elapsed_seconds:.1f}秒 ({sm.item_count}件)")

        # Domain extraction rate summary
        if result.domain_extraction_rates:
            print("\n  ドメイン別抽出成功率:")
            for dr in sorted(
                result.domain_extraction_rates,
                key=lambda x: x.success_rate,
            ):
                print(
                    f"    {dr.domain}: {dr.success}/{dr.total} ({dr.success_rate:.0f}%)"
                )

        return result

    async def _extract_batch_with_progress(
        self,
        articles: list[CollectedArticle],
    ) -> list[ExtractedArticle]:
        """Extract body text from articles with progress logging.

        Uses asyncio.Semaphore to limit concurrent extractions based on
        config.extraction.concurrency setting.
        """
        import asyncio

        total = len(articles)
        concurrency = self._config.extraction.concurrency
        semaphore = asyncio.Semaphore(concurrency)

        # Counter for progress logging (protected by lock for thread safety)
        progress_lock = asyncio.Lock()
        progress_counter = {"count": 0}

        async def extract_with_semaphore(
            article: CollectedArticle,
        ) -> ExtractedArticle:
            async with semaphore:
                result = await self._extractor.extract(article)

                # Update progress with lock
                async with progress_lock:
                    progress_counter["count"] += 1
                    current = progress_counter["count"]

                title = (
                    article.title[:40] + "..."
                    if len(article.title) > 40
                    else article.title
                )
                if result.extraction_status == ExtractionStatus.SUCCESS:
                    self._log_progress(current, total, title)
                else:
                    self._log_progress(
                        current,
                        total,
                        f"{title} - {result.error_message}",
                        is_error=True,
                    )
                    logger.error(
                        "Extraction failed",
                        url=str(article.url),
                        error=result.error_message,
                    )
                return result

        # Execute all extractions concurrently with semaphore limiting
        tasks = [extract_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks)

        return list(results)

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

    def _compute_domain_extraction_rates(
        self,
        extracted: list[ExtractedArticle],
    ) -> list[DomainExtractionRate]:
        """Compute extraction success rate per domain.

        Parameters
        ----------
        extracted : list[ExtractedArticle]
            List of extracted articles to analyze.

        Returns
        -------
        list[DomainExtractionRate]
            Extraction success rates grouped by domain.
        """
        domain_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "success": 0, "failed": 0}
        )

        for article in extracted:
            url_str = str(article.collected.url)
            parsed = urlparse(url_str)
            domain = parsed.netloc.lower()
            # Strip www. prefix for cleaner grouping
            if domain.startswith("www."):
                domain = domain[4:]

            domain_stats[domain]["total"] += 1
            if article.extraction_status == ExtractionStatus.SUCCESS:
                domain_stats[domain]["success"] += 1
            else:
                domain_stats[domain]["failed"] += 1

        rates: list[DomainExtractionRate] = []
        for domain, stats in sorted(domain_stats.items()):
            total = stats["total"]
            success = stats["success"]
            failed = stats["failed"]
            success_rate = (success / total * 100) if total > 0 else 0.0
            rates.append(
                DomainExtractionRate(
                    domain=domain,
                    total=total,
                    success=success,
                    failed=failed,
                    success_rate=round(success_rate, 1),
                )
            )

        logger.info(
            "Domain extraction rates computed",
            domain_count=len(rates),
            domains={r.domain: f"{r.success_rate}%" for r in rates},
        )

        return rates

    def _build_empty_result(
        self,
        started_at: datetime,
        finished_at: datetime,
        feed_errors: list[FeedError] | None = None,
        stage_metrics: list[StageMetrics] | None = None,
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
            feed_errors=feed_errors or [],
            stage_metrics=stage_metrics or [],
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
        early_duplicates: int = 0,
        feed_errors: list[FeedError] | None = None,
        category_results: list[CategoryPublishResult] | None = None,
        stage_metrics: list[StageMetrics] | None = None,
        domain_extraction_rates: list[DomainExtractionRate] | None = None,
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
            Publication results (per-article format).
        started_at : datetime
            Workflow start timestamp.
        finished_at : datetime
            Workflow end timestamp.
        early_duplicates : int, optional
            Number of articles excluded by early duplicate check
            (before extraction). Defaults to 0.
        feed_errors : list[FeedError] | None, optional
            Feed errors that occurred during collection.
            Defaults to None (empty list).
        category_results : list[CategoryPublishResult] | None, optional
            Results of category-based Issue publishing.
            Defaults to None (empty list).
        stage_metrics : list[StageMetrics] | None, optional
            Processing time metrics for each workflow stage.
            Defaults to None (empty list).
        domain_extraction_rates : list[DomainExtractionRate] | None, optional
            Extraction success rate per domain.
            Defaults to None (empty list).

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
            total_early_duplicates=early_duplicates,
            extraction_failures=extraction_failures,
            summarization_failures=summarization_failures,
            publication_failures=publication_failures,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
            published_articles=published_articles,
            feed_errors=feed_errors or [],
            category_results=category_results or [],
            stage_metrics=stage_metrics or [],
            domain_extraction_rates=domain_extraction_rates or [],
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
