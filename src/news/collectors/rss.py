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
from news.models import ArticleSource, CollectedArticle, SourceType
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
        logger.debug(
            "RSSCollector initialized",
            presets_file=config.rss.presets_file,
        )

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
                    logger.warning(
                        "Failed to fetch feed, continuing with next",
                        feed_url=preset.url,
                        feed_title=preset.title,
                        error=str(e),
                    )
                    continue

        logger.info(
            "RSS collection completed",
            total_articles=len(all_articles),
            feeds_processed=len(enabled_presets),
        )

        return all_articles

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
                category=preset_data["category"],
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


__all__ = ["RSSCollector"]
