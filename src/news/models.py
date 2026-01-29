"""Data models for the news collection workflow.

This module provides core data models for representing news article sources
and their metadata in a unified format. These models are used throughout
the news collection pipeline.

Notes
-----
- `SourceType` represents the type of data source (RSS, yfinance, scraper)
- `ArticleSource` represents metadata about where an article came from

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

from enum import StrEnum

from pydantic import BaseModel, Field


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


__all__ = [
    "ArticleSource",
    "SourceType",
]
