"""Data models for the news collection workflow.

This module provides core data models for representing news article sources
and their metadata in a unified format. These models are used throughout
the news collection pipeline.

Notes
-----
- `SourceType` represents the type of data source (RSS, yfinance, scraper)
- `ArticleSource` represents metadata about where an article came from
- `CollectedArticle` represents an article collected from a source

Examples
--------
>>> from news.models import SourceType, ArticleSource
>>> source = ArticleSource(
...     source_type=SourceType.RSS,
...     source_name="CNBC Markets",
...     category="market",
... )
>>> source.source_type
<SourceType.RSS: 'rss'>
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class SourceType(StrEnum):
    """Type of news data source.

    Represents the type of source from which news articles are collected.
    This is used to determine how to fetch and process articles.

    Attributes
    ----------
    RSS : str
        RSS feed source. Articles are fetched via RSS/Atom feeds.
    YFINANCE : str
        Yahoo Finance source. Articles are fetched via yfinance API.
    SCRAPE : str
        Web scraping source. Articles are fetched via custom scrapers.

    Examples
    --------
    >>> SourceType.RSS
    <SourceType.RSS: 'rss'>
    >>> SourceType.RSS == "rss"
    True
    >>> SourceType.YFINANCE.value
    'yfinance'
    """

    RSS = "rss"
    YFINANCE = "yfinance"
    SCRAPE = "scrape"


class ArticleSource(BaseModel):
    """Metadata about the source of a news article.

    Represents information about where an article came from, including
    the source type, name, category for mapping, and optional feed ID.

    Attributes
    ----------
    source_type : SourceType
        The type of source (RSS, yfinance, or scraper).
    source_name : str
        Human-readable name of the source (e.g., "CNBC Markets", "NVDA").
    category : str
        Category for status mapping (e.g., "market", "yf_ai_stock").
        This is used to determine the GitHub Project status.
    feed_id : str | None
        Optional feed identifier for RSS sources.
        Not used for yfinance or scraper sources.

    Examples
    --------
    >>> from news.models import ArticleSource, SourceType
    >>> # RSS source
    >>> rss_source = ArticleSource(
    ...     source_type=SourceType.RSS,
    ...     source_name="CNBC Markets",
    ...     category="market",
    ...     feed_id="cnbc-markets-001",
    ... )
    >>> rss_source.source_type
    <SourceType.RSS: 'rss'>

    >>> # yfinance source
    >>> yf_source = ArticleSource(
    ...     source_type=SourceType.YFINANCE,
    ...     source_name="NVDA",
    ...     category="yf_ai_stock",
    ... )
    >>> yf_source.feed_id is None
    True
    """

    source_type: SourceType = Field(
        ...,
        description="Type of the data source (RSS, yfinance, or scraper)",
    )
    source_name: str = Field(
        ...,
        description="Human-readable name of the source",
    )
    category: str = Field(
        ...,
        description="Category for status mapping (e.g., 'market', 'yf_ai_stock')",
    )
    feed_id: str | None = Field(
        default=None,
        description="Optional feed identifier for RSS sources",
    )


class CollectedArticle(BaseModel):
    """An article collected from a news source.

    Represents an article immediately after collection, before any processing
    such as summarization or classification. This is the output of a Collector.

    Attributes
    ----------
    url : HttpUrl
        The original URL of the article.
    title : str
        The article title.
    published : datetime | None
        The publication date/time of the article, if available.
    raw_summary : str | None
        The original summary from the source (e.g., RSS summary field).
        This is the unprocessed summary from the data source.
    source : ArticleSource
        Metadata about where the article came from.
    collected_at : datetime
        The timestamp when the article was collected.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from news.models import ArticleSource, CollectedArticle, SourceType
    >>> source = ArticleSource(
    ...     source_type=SourceType.RSS,
    ...     source_name="CNBC Markets",
    ...     category="market",
    ... )
    >>> article = CollectedArticle(
    ...     url="https://www.cnbc.com/article/123",
    ...     title="Market Update",
    ...     source=source,
    ...     collected_at=datetime.now(tz=timezone.utc),
    ... )
    >>> article.title
    'Market Update'
    """

    url: HttpUrl = Field(
        ...,
        description="The original URL of the article",
    )
    title: str = Field(
        ...,
        description="The article title",
    )
    published: datetime | None = Field(
        default=None,
        description="The publication date/time of the article, if available",
    )
    raw_summary: str | None = Field(
        default=None,
        description="The original summary from the source (e.g., RSS summary field)",
    )
    source: ArticleSource = Field(
        ...,
        description="Metadata about where the article came from",
    )
    collected_at: datetime = Field(
        ...,
        description="The timestamp when the article was collected",
    )


__all__ = [
    "ArticleSource",
    "CollectedArticle",
    "SourceType",
]
