"""Base collector abstract class for news data collection.

This module provides the abstract base class for all news collectors.
Collectors are responsible for fetching article metadata from various
sources such as RSS feeds, yfinance API, or web scraping.

Examples
--------
>>> from news.collectors.base import BaseCollector
>>> from news.models import CollectedArticle, SourceType
>>>
>>> class RSSCollector(BaseCollector):
...     @property
...     def source_type(self) -> SourceType:
...         return SourceType.RSS
...
...     async def collect(
...         self,
...         max_age_hours: int = 168,
...     ) -> list[CollectedArticle]:
...         # Fetch articles from RSS feeds
...         return []
"""

from abc import ABC, abstractmethod

from news.models import CollectedArticle, SourceType


class BaseCollector(ABC):
    """Abstract base class for news collectors.

    This class defines the interface for collectors that fetch article
    metadata from various sources. Concrete implementations must provide:

    1. A `source_type` property returning the type of source
    2. A `collect()` method that fetches and returns articles

    Attributes
    ----------
    source_type : SourceType
        The type of source this collector handles (abstract property).

    Methods
    -------
    collect(max_age_hours=168)
        Collect articles from the source (abstract method).

    Notes
    -----
    - All collectors must be async-compatible
    - The `max_age_hours` parameter filters articles by publication time
    - Default max_age_hours of 168 equals 7 days

    Examples
    --------
    >>> class MyCollector(BaseCollector):
    ...     @property
    ...     def source_type(self) -> SourceType:
    ...         return SourceType.RSS
    ...
    ...     async def collect(
    ...         self,
    ...         max_age_hours: int = 168,
    ...     ) -> list[CollectedArticle]:
    ...         return []
    ...
    >>> collector = MyCollector()
    >>> collector.source_type
    <SourceType.RSS: 'rss'>
    """

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Return the type of source this collector handles.

        Returns
        -------
        SourceType
            The type of data source (RSS, YFINANCE, or SCRAPE).

        Examples
        --------
        >>> collector.source_type
        <SourceType.RSS: 'rss'>
        """

    @abstractmethod
    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """Collect articles from the source.

        Parameters
        ----------
        max_age_hours : int, optional
            Maximum age of articles to collect in hours.
            Default is 168 (7 days).

        Returns
        -------
        list[CollectedArticle]
            List of collected articles.

        Notes
        -----
        - Articles older than `max_age_hours` should be filtered out
        - The method is async to support non-blocking I/O operations
        - Empty list is valid when no articles match the criteria

        Examples
        --------
        >>> articles = await collector.collect(max_age_hours=24)
        >>> len(articles)
        10
        """


__all__ = ["BaseCollector"]
