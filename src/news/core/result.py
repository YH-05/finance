"""Fetch result and retry configuration for the news package.

This module provides data classes for representing news fetch results
and retry configurations.

Classes
-------
RetryConfig
    Immutable configuration for retry behavior.
FetchResult
    Result of a news fetch operation (success or failure).

Examples
--------
>>> config = RetryConfig(max_attempts=5, initial_delay=0.5)
>>> result = FetchResult(articles=[], success=True, ticker="AAPL")
>>> result.article_count
0
>>> result.is_empty
True
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..utils.logging_config import get_logger
from .article import Article
from .errors import SourceError

logger = get_logger(__name__, module="result")


@dataclass(frozen=True)
class RetryConfig:
    """Immutable configuration for retry behavior.

    This class defines the retry strategy for failed operations,
    including exponential backoff and jitter.

    Parameters
    ----------
    max_attempts : int, optional
        Maximum number of retry attempts (default: 3).
    initial_delay : float, optional
        Initial delay in seconds before first retry (default: 1.0).
    max_delay : float, optional
        Maximum delay in seconds between retries (default: 60.0).
    exponential_base : float, optional
        Base for exponential backoff calculation (default: 2.0).
    jitter : bool, optional
        Whether to add random jitter to delays (default: True).
    retryable_exceptions : tuple[type[Exception], ...], optional
        Exception types that should trigger a retry.

    Attributes
    ----------
    max_attempts : int
        Maximum number of retry attempts.
    initial_delay : float
        Initial delay in seconds.
    max_delay : float
        Maximum delay in seconds.
    exponential_base : float
        Base for exponential backoff.
    jitter : bool
        Whether to add jitter.
    retryable_exceptions : tuple[type[Exception], ...]
        Exception types that trigger retries.

    Notes
    -----
    This dataclass is frozen (immutable). Once created, its values
    cannot be changed.

    The retry delay follows this pattern:
    - 1st retry: initial_delay
    - 2nd retry: initial_delay * exponential_base
    - 3rd retry: initial_delay * exponential_base^2
    - ...up to max_delay

    Examples
    --------
    >>> config = RetryConfig()
    >>> config.max_attempts
    3
    >>> config.initial_delay
    1.0

    >>> custom_config = RetryConfig(
    ...     max_attempts=5,
    ...     initial_delay=0.5,
    ...     retryable_exceptions=(ConnectionError,),
    ... )
    >>> custom_config.max_attempts
    5
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
    )


@dataclass
class FetchResult:
    """Result of a news fetch operation.

    This class represents the result of fetching news from a source,
    supporting both Ticker-based (specific symbols) and Search-based
    (keyword queries) operations.

    Parameters
    ----------
    articles : list[Article]
        List of fetched articles (empty on failure).
    success : bool
        Whether the fetch operation succeeded.
    ticker : str | None, optional
        Ticker symbol for Ticker-based fetches.
    query : str | None, optional
        Search query for Search-based fetches.
    error : SourceError | None, optional
        Error information if the fetch failed.
    fetched_at : datetime, optional
        Timestamp when the fetch occurred (auto-generated).
    retry_count : int, optional
        Number of retries performed (default: 0).

    Attributes
    ----------
    articles : list[Article]
        List of fetched articles.
    success : bool
        Whether the operation succeeded.
    ticker : str | None
        Ticker symbol if applicable.
    query : str | None
        Search query if applicable.
    error : SourceError | None
        Error information if failed.
    fetched_at : datetime
        Timestamp of the fetch.
    retry_count : int
        Number of retries performed.

    Notes
    -----
    - For Ticker-based fetches, `ticker` is set and `query` is None.
    - For Search-based fetches, `query` is set and `ticker` is None.
    - The `source_identifier` property returns whichever is set.

    Examples
    --------
    >>> from news.core.article import Article, ArticleSource
    >>> from datetime import datetime, timezone
    >>> article = Article(
    ...     url="https://example.com/news",
    ...     title="Test",
    ...     published_at=datetime.now(timezone.utc),
    ...     source=ArticleSource.YFINANCE_TICKER,
    ... )
    >>> result = FetchResult(
    ...     articles=[article],
    ...     success=True,
    ...     ticker="AAPL",
    ... )
    >>> result.article_count
    1
    >>> result.is_empty
    False
    >>> result.source_identifier
    'AAPL'
    """

    articles: list[Article]
    success: bool
    ticker: str | None = None
    query: str | None = None
    error: SourceError | None = None
    fetched_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    retry_count: int = 0

    def __post_init__(self) -> None:
        """Log the creation of a FetchResult."""
        logger.debug(
            "FetchResult created",
            success=self.success,
            article_count=len(self.articles),
            ticker=self.ticker,
            query=self.query,
            has_error=self.error is not None,
            retry_count=self.retry_count,
        )

    @property
    def article_count(self) -> int:
        """Return the number of articles fetched.

        Returns
        -------
        int
            Number of articles in the result.

        Examples
        --------
        >>> result = FetchResult(articles=[], success=True, ticker="AAPL")
        >>> result.article_count
        0
        """
        return len(self.articles)

    @property
    def is_empty(self) -> bool:
        """Check if the result contains no articles.

        Returns
        -------
        bool
            True if no articles were fetched, False otherwise.

        Examples
        --------
        >>> result = FetchResult(articles=[], success=True, ticker="AAPL")
        >>> result.is_empty
        True
        """
        return len(self.articles) == 0

    @property
    def source_identifier(self) -> str:
        """Return the identifier of the fetch source.

        Returns the ticker symbol if available, otherwise the search query.
        If neither is set, returns "unknown".

        Returns
        -------
        str
            The ticker, query, or "unknown".

        Examples
        --------
        >>> result = FetchResult(articles=[], success=True, ticker="AAPL")
        >>> result.source_identifier
        'AAPL'

        >>> result = FetchResult(articles=[], success=True, query="Fed")
        >>> result.source_identifier
        'Fed'
        """
        return self.ticker or self.query or "unknown"


# Export all public symbols
__all__ = [
    "FetchResult",
    "RetryConfig",
]
