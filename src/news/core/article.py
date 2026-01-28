"""Article model and related types for the news package.

This module provides the core data models for representing news articles
from various sources (yfinance, scraper, RSS, etc.) in a unified format.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="article")


class ContentType(str, Enum):
    """Content type enumeration for news articles.

    Represents the type of content in a news article.

    Attributes
    ----------
    ARTICLE : str
        Standard text article.
    VIDEO : str
        Video content.
    PRESS_RELEASE : str
        Press release content.
    UNKNOWN : str
        Unknown or unspecified content type.
    """

    ARTICLE = "article"
    VIDEO = "video"
    PRESS_RELEASE = "press_release"
    UNKNOWN = "unknown"


class ArticleSource(str, Enum):
    """Source enumeration for news articles.

    Represents the data source from which an article was fetched.

    Attributes
    ----------
    YFINANCE_TICKER : str
        Article fetched via yfinance Ticker.news (individual stocks, indices, ETFs).
    YFINANCE_SEARCH : str
        Article fetched via yfinance Search.news (keyword search).
    SCRAPER : str
        Article fetched via web scraping.
    RSS : str
        Article fetched via RSS feed (for future integration).
    """

    YFINANCE_TICKER = "yfinance_ticker"
    YFINANCE_SEARCH = "yfinance_search"
    SCRAPER = "scraper"
    RSS = "rss"


class Provider(BaseModel):
    """Provider information for a news article.

    Represents the original publisher or provider of the news content.

    Attributes
    ----------
    name : str
        Name of the provider (e.g., "Yahoo Finance", "Reuters").
    url : HttpUrl | None
        URL of the provider's website.

    Examples
    --------
    >>> provider = Provider(name="Yahoo Finance", url="https://finance.yahoo.com/")
    >>> provider.name
    'Yahoo Finance'
    """

    name: str = Field(..., description="Name of the news provider")
    url: HttpUrl | None = Field(None, description="URL of the provider's website")


class Thumbnail(BaseModel):
    """Thumbnail image information for a news article.

    Attributes
    ----------
    url : HttpUrl
        URL of the thumbnail image.
    width : int | None
        Width of the image in pixels.
    height : int | None
        Height of the image in pixels.

    Examples
    --------
    >>> thumb = Thumbnail(url="https://example.com/image.jpg", width=1200, height=800)
    >>> thumb.width
    1200
    """

    url: HttpUrl = Field(..., description="URL of the thumbnail image")
    width: int | None = Field(None, description="Width of the image in pixels")
    height: int | None = Field(None, description="Height of the image in pixels")


class Article(BaseModel):
    """Unified news article model.

    Represents a news article from various sources (yfinance, scraper, etc.)
    in a unified format. This model is source-agnostic and provides a common
    interface for working with news data.

    Attributes
    ----------
    url : HttpUrl
        URL of the original article (used as the primary key for deduplication).
    title : str
        Title of the article.
    published_at : datetime
        Publication date and time in UTC.
    source : ArticleSource
        Source from which the article was fetched.
    summary : str | None
        Summary or description of the article.
    content_type : ContentType
        Type of content (article, video, press release, etc.).
    provider : Provider | None
        Information about the article's publisher.
    thumbnail : Thumbnail | None
        Thumbnail image information.
    related_tickers : list[str]
        List of related ticker symbols.
    tags : list[str]
        Tags or categories for the article.
    fetched_at : datetime
        Timestamp when the article was fetched.
    metadata : dict[str, Any]
        Source-specific metadata.
    summary_ja : str | None
        Japanese summary (AI-generated).
    category : str | None
        Category classification (AI-generated).
    sentiment : float | None
        Sentiment score between -1.0 (negative) and 1.0 (positive).

    Notes
    -----
    - **Deduplication is done using `url`** (not `id`, as some sources don't provide IDs).
    - If `summary` is empty, it's recommended to use `title` instead.
    - The `fetched_at` field is automatically set to the current UTC time.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> article = Article(
    ...     url="https://finance.yahoo.com/news/example",
    ...     title="Example Article",
    ...     published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
    ...     source=ArticleSource.YFINANCE_TICKER,
    ... )
    >>> article.title
    'Example Article'
    """

    # === Required fields (available from all sources) ===
    url: HttpUrl = Field(
        ...,
        description="Article URL (used as primary key for deduplication)",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Article title",
    )
    published_at: datetime = Field(
        ...,
        description="Publication date and time (UTC)",
    )
    source: ArticleSource = Field(
        ...,
        description="Source from which the article was fetched",
    )

    # === Optional fields ===
    summary: str | None = Field(
        None,
        description="Article summary or description",
    )
    content_type: ContentType = Field(
        default=ContentType.ARTICLE,
        description="Type of content",
    )
    provider: Provider | None = Field(
        None,
        description="Publisher information",
    )
    thumbnail: Thumbnail | None = Field(
        None,
        description="Thumbnail image information",
    )

    # === Related information ===
    related_tickers: list[str] = Field(
        default_factory=list,
        description="Related ticker symbols",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags or categories",
    )

    # === Metadata ===
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the article was fetched (UTC)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific metadata",
    )

    # === AI-generated fields (populated later) ===
    summary_ja: str | None = Field(
        None,
        description="Japanese summary (AI-generated)",
    )
    category: str | None = Field(
        None,
        description="Category classification (AI-generated)",
    )
    sentiment: float | None = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Sentiment score (-1.0 to 1.0)",
    )

    def __init__(self, **data: Any) -> None:
        """Initialize Article with logging."""
        super().__init__(**data)
        logger.debug(
            "Article created",
            url=str(self.url),
            title=self.title[:50] + "..." if len(self.title) > 50 else self.title,
            source=self.source.value,
            published_at=self.published_at.isoformat(),
        )


# Export all public symbols
__all__ = [
    "Article",
    "ArticleSource",
    "ContentType",
    "Provider",
    "Thumbnail",
]
