"""RSS feed collector for news articles.

This module provides the RSSCollector class which collects news articles
from RSS feeds using the existing FeedParser implementation.

Examples
--------
>>> from news.collectors.rss import RSSCollector
>>> from news.config import load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> collector = RSSCollector(config=config)
>>> articles = await collector.collect(max_age_hours=24)
>>> len(articles)
15
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from news.collectors.base import BaseCollector
from news.config import NewsWorkflowConfig
from news.models import ArticleSource, CollectedArticle, FeedError, SourceType
from news.utils.logging_config import get_logger
from rss.core.parser import FeedParser
from rss.types import FeedItem, PresetFeed

logger = get_logger(__name__, module="collectors.rss")


class RSSCollector(BaseCollector):
    """RSS feed collector for news articles.

    Collects articles from RSS feeds defined in the presets configuration file.
    Uses the existing FeedParser to parse feed content.

    Parameters
    ----------
    config : NewsWorkflowConfig
        Workflow configuration containing RSS settings.

    Attributes
    ----------
    source_type : SourceType
        Returns SourceType.RSS.

    Examples
    --------
    >>> from news.collectors.rss import RSSCollector
    >>> from news.config import load_config
    >>> config = load_config("data/config/news-collection-config.yaml")
    >>> collector = RSSCollector(config=config)
    >>> collector.source_type
    <SourceType.RSS: 'rss'>
    >>> articles = await collector.collect()
    >>> all(a.source.source_type == SourceType.RSS for a in articles)
    True
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        """Initialize RSSCollector with configuration.

        Parameters
        ----------
        config : NewsWorkflowConfig
            Workflow configuration containing RSS settings.
        """
        self._config = config
        self._parser = FeedParser()
        self._domain_filter = config.domain_filtering
        self._feed_errors: list[FeedError] = []
        logger.debug(
            "RSSCollector initialized",
            presets_file=config.rss.presets_file,
        )

    @property
    def feed_errors(self) -> list[FeedError]:
        """Return a copy of the feed errors that occurred during collection.

        Returns
        -------
        list[FeedError]
            A copy of the list of feed errors.
        """
        return self._feed_errors.copy()

    @property
    def source_type(self) -> SourceType:
        """Return the source type for this collector.

        Returns
        -------
        SourceType
            Always returns SourceType.RSS.
        """
        return SourceType.RSS

    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """Collect articles from configured RSS feeds.

        Reads the presets configuration, fetches enabled feeds, parses them
        using FeedParser, and converts items to CollectedArticle instances.

        Parameters
        ----------
        max_age_hours : int, optional
            Maximum age of articles to collect in hours.
            Default is 168 (7 days).

        Returns
        -------
        list[CollectedArticle]
            List of collected articles from all enabled RSS feeds.

        Notes
        -----
        - Only enabled feeds are processed
        - HTTP errors for individual feeds are logged but don't stop processing
        - Articles older than max_age_hours are filtered out
        """
        logger.info(
            "Starting RSS collection",
            max_age_hours=max_age_hours,
        )

        # Clear previous feed errors
        self._feed_errors.clear()

        # Load presets configuration
        presets = self._load_presets()
        enabled_presets = [p for p in presets if p.enabled]

        logger.debug(
            "Loaded presets",
            total_presets=len(presets),
            enabled_presets=len(enabled_presets),
        )

        if not enabled_presets:
            logger.info("No enabled presets found, returning empty list")
            return []

        # Collect articles from all enabled feeds
        all_articles: list[CollectedArticle] = []
        cutoff_time = self._calculate_cutoff_time(max_age_hours)

        async with httpx.AsyncClient(timeout=30.0) as client:
            for preset in enabled_presets:
                try:
                    articles = await self._fetch_feed(
                        client=client,
                        preset=preset,
                        cutoff_time=cutoff_time,
                    )
                    all_articles.extend(articles)
                    logger.debug(
                        "Feed processed",
                        feed_title=preset.title,
                        articles_count=len(articles),
                    )
                except Exception as e:
                    self._record_feed_error(preset, e, self._classify_error(e))
                    continue

        # Log summary if there were feed errors
        if self._feed_errors:
            logger.warning(
                "Some feeds failed during collection",
                total_feeds=len(enabled_presets),
                failed_feeds=len(self._feed_errors),
                error_types=self._count_error_types(),
            )

        # Apply domain filtering
        filtered_articles = self._filter_blocked_domains(all_articles)

        logger.info(
            "RSS collection completed",
            total_articles=len(filtered_articles),
            successful_feeds=len(enabled_presets) - len(self._feed_errors),
            failed_feeds=len(self._feed_errors),
        )

        return filtered_articles

    def _load_presets(self) -> list[PresetFeed]:
        """Load RSS feed presets from configuration file.

        Returns
        -------
        list[PresetFeed]
            List of preset feed configurations.

        Raises
        ------
        FileNotFoundError
            If the presets file does not exist.
        json.JSONDecodeError
            If the presets file contains invalid JSON.
        """
        presets_path = Path(self._config.rss.presets_file)
        logger.debug("Loading presets", path=str(presets_path))

        content = presets_path.read_text(encoding="utf-8")
        data = json.loads(content)

        presets: list[PresetFeed] = []
        for preset_data in data.get("presets", []):
            preset = PresetFeed(
                url=preset_data["url"],
                title=preset_data["title"],
                category=preset_data.get("category", "other"),
                fetch_interval=preset_data["fetch_interval"],
                enabled=preset_data["enabled"],
            )
            presets.append(preset)

        return presets

    def _calculate_cutoff_time(self, max_age_hours: int) -> datetime:
        """Calculate the cutoff time for filtering old articles.

        Parameters
        ----------
        max_age_hours : int
            Maximum age of articles in hours.

        Returns
        -------
        datetime
            The cutoff datetime (articles older than this are filtered out).
        """
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        return now - timedelta(hours=max_age_hours)

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        preset: PresetFeed,
        cutoff_time: datetime,
    ) -> list[CollectedArticle]:
        """Fetch and parse a single RSS feed.

        Parameters
        ----------
        client : httpx.AsyncClient
            HTTP client for making requests.
        preset : PresetFeed
            Feed configuration.
        cutoff_time : datetime
            Cutoff time for filtering old articles.

        Returns
        -------
        list[CollectedArticle]
            List of collected articles from the feed.
        """
        logger.debug("Fetching feed", url=preset.url, title=preset.title)

        response = await client.get(preset.url)
        response.raise_for_status()

        # Parse feed content
        feed_items = self._parser.parse(response.content)

        # Convert to CollectedArticle and filter by age
        articles: list[CollectedArticle] = []
        collected_at = datetime.now(timezone.utc)

        for item in feed_items:
            article = self._convert_feed_item(
                item=item,
                preset=preset,
                collected_at=collected_at,
            )

            # Filter by publication time
            if article.published and article.published < cutoff_time:
                continue

            articles.append(article)

        return articles

    def _convert_feed_item(
        self,
        item: FeedItem,
        preset: PresetFeed,
        collected_at: datetime,
    ) -> CollectedArticle:
        """Convert a FeedItem to CollectedArticle.

        Parameters
        ----------
        item : FeedItem
            Parsed feed item.
        preset : PresetFeed
            Feed configuration.
        collected_at : datetime
            Collection timestamp.

        Returns
        -------
        CollectedArticle
            Converted article.
        """
        # Parse published datetime
        published: datetime | None = None
        if item.published:
            try:
                published = datetime.fromisoformat(item.published)
            except ValueError:
                logger.warning(
                    "Failed to parse published date",
                    item_id=item.item_id,
                    published=item.published,
                )

        # Create ArticleSource
        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name=preset.title,
            category=preset.category,
            feed_id=item.item_id,
        )

        return CollectedArticle(
            url=item.link,  # type: ignore[arg-type]
            title=item.title,
            published=published,
            raw_summary=item.summary,
            source=source,
            collected_at=collected_at,
        )

    def _filter_blocked_domains(
        self,
        articles: list[CollectedArticle],
    ) -> list[CollectedArticle]:
        """Filter out articles from blocked domains.

        Parameters
        ----------
        articles : list[CollectedArticle]
            List of articles to filter.

        Returns
        -------
        list[CollectedArticle]
            List of articles with blocked domains removed.
        """
        if not self._domain_filter.enabled:
            return articles

        filtered: list[CollectedArticle] = []
        blocked_count = 0

        for article in articles:
            url = str(article.url)
            if self._domain_filter.is_blocked(url):
                blocked_count += 1
                if self._domain_filter.log_blocked:
                    logger.debug(
                        "Blocked domain article skipped",
                        url=url,
                        title=article.title[:50] if article.title else "",
                    )
            else:
                filtered.append(article)

        if blocked_count > 0:
            logger.info(
                "Filtered blocked domain articles",
                blocked_count=blocked_count,
                remaining_count=len(filtered),
            )

        return filtered

    def _record_feed_error(
        self,
        preset: PresetFeed,
        error: Exception,
        error_type: str,
    ) -> None:
        """Record a feed collection error.

        Parameters
        ----------
        preset : PresetFeed
            The feed that failed.
        error : Exception
            The error that occurred.
        error_type : str
            The type of error (e.g., "fetch", "parse", "validation").
        """
        feed_error = FeedError(
            feed_url=preset.url,
            feed_name=preset.title,
            error=str(error),
            error_type=error_type,
            timestamp=datetime.now(timezone.utc),
        )
        self._feed_errors.append(feed_error)

        logger.error(
            "Feed collection failed, skipping",
            feed_url=preset.url,
            feed_name=preset.title,
            error_type=error_type,
            error=str(error),
        )

    def _classify_error(self, error: Exception) -> str:
        """Classify an exception into an error type.

        Parameters
        ----------
        error : Exception
            The exception to classify.

        Returns
        -------
        str
            The error type: "fetch", "parse", or "validation".
        """
        import httpx

        # HTTP errors are fetch errors
        if isinstance(error, (httpx.HTTPError, httpx.TimeoutException)):
            return "fetch"

        # JSON/XML parsing errors
        if isinstance(error, (json.JSONDecodeError, ValueError)):
            error_msg = str(error).lower()
            if "parse" in error_msg or "xml" in error_msg or "invalid" in error_msg:
                return "parse"

        # File not found errors for presets file
        if isinstance(error, FileNotFoundError):
            return "validation"

        # Default to fetch for unknown errors
        return "fetch"

    def _count_error_types(self) -> dict[str, int]:
        """Count the number of errors by type.

        Returns
        -------
        dict[str, int]
            A dictionary mapping error types to their counts.
        """
        counts: dict[str, int] = {}
        for error in self._feed_errors:
            counts[error.error_type] = counts.get(error.error_type, 0) + 1
        return counts


__all__ = ["RSSCollector"]
