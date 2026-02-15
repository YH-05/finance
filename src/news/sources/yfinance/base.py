"""yfinance base module for common utilities and conversion functions.

This module provides the foundational functionality for the yfinance news source,
including data conversion functions, retry logic with exponential backoff,
polite delay between requests, and input validation.

Functions
---------
apply_polite_delay
    Apply a polite delay between requests (NasdaqSession pattern).
ticker_news_to_article
    Convert yfinance Ticker.news data to Article model.
search_news_to_article
    Convert yfinance Search.news data to Article model.
fetch_with_retry
    Execute a fetch operation with retry logic and exponential backoff.
    Converts YFRateLimitError to RateLimitError on exhaustion.
validate_ticker
    Validate a ticker symbol.
validate_query
    Validate a search query.

Examples
--------
>>> from news.sources.yfinance.base import ticker_news_to_article
>>> raw_data = {"content": {"title": "Test", "pubDate": "2026-01-27T10:00:00Z", ...}}
>>> article = ticker_news_to_article(raw_data, "AAPL")
>>> article.title
'Test'
"""

import contextlib
import random
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar

from pydantic import HttpUrl
from pydantic import ValidationError as PydanticValidationError

from utils_core.logging import get_logger

from ...core.article import (
    Article,
    ArticleSource,
    ContentType,
    Provider,
    Thumbnail,
)
from ...core.errors import RateLimitError, SourceError, ValidationError
from ...core.result import FetchResult, RetryConfig

logger = get_logger(__name__, module="yfinance.base")

# Type variable for generic fetch function
T = TypeVar("T")

# Content type mapping from yfinance to internal enum
_CONTENT_TYPE_MAP: dict[str, ContentType] = {
    "STORY": ContentType.ARTICLE,
    "VIDEO": ContentType.VIDEO,
}

# Regex pattern for valid ticker characters
# Allows: A-Z, 0-9, ^, -, =, .
_TICKER_PATTERN = re.compile(r"^[A-Z0-9\^=\-\.]+$")

# Maximum ticker length
_MAX_TICKER_LENGTH = 15

# Maximum query length
_MAX_QUERY_LENGTH = 200

# Polite delay constants (following NasdaqSession pattern)
DEFAULT_POLITE_DELAY: float = 1.0
DEFAULT_DELAY_JITTER: float = 0.5


def _get_yfinance_retry_config() -> RetryConfig:
    """Build the default retry configuration for yfinance sources.

    Lazy-imports ``YFRateLimitError`` so the module can be imported even
    when *yfinance* is not installed.

    Returns
    -------
    RetryConfig
        Retry configuration with YFRateLimitError as a retryable exception.
    """
    retryable: tuple[type[Exception], ...] = (ConnectionError, TimeoutError)
    try:
        from yfinance.exceptions import YFRateLimitError

        retryable = (*retryable, YFRateLimitError)
    except ImportError:
        pass
    return RetryConfig(
        max_attempts=3,
        initial_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=retryable,
    )


DEFAULT_YFINANCE_RETRY_CONFIG: RetryConfig = _get_yfinance_retry_config()


def apply_polite_delay(
    polite_delay: float = DEFAULT_POLITE_DELAY,
    jitter: float = DEFAULT_DELAY_JITTER,
) -> float:
    """Apply a polite delay between requests.

    Follows the NasdaqSession pattern for rate-limiting courtesy.
    The actual delay is ``polite_delay + random.uniform(0, jitter)``.

    Parameters
    ----------
    polite_delay : float
        Base delay in seconds (default: ``DEFAULT_POLITE_DELAY`` = 1.0).
    jitter : float
        Random jitter in seconds added to the base delay
        (default: ``DEFAULT_DELAY_JITTER`` = 0.5).

    Returns
    -------
    float
        Actual wait time in seconds.

    Examples
    --------
    >>> from unittest.mock import patch
    >>> with patch("news.sources.yfinance.base.time.sleep"):
    ...     delay = apply_polite_delay(polite_delay=1.0, jitter=0.0)
    >>> delay
    1.0
    """
    actual_delay = polite_delay + random.uniform(0, jitter)  # nosec B311 - not used for security/crypto
    time.sleep(actual_delay)
    logger.debug("Polite delay applied", delay_seconds=actual_delay)
    return actual_delay


def ticker_news_to_article(raw: dict[str, Any], ticker: str) -> Article:
    """Convert yfinance Ticker.news data to Article model.

    Parameters
    ----------
    raw : dict[str, Any]
        Raw news data from yfinance Ticker.news.
    ticker : str
        Ticker symbol used to fetch the news.

    Returns
    -------
    Article
        Converted Article instance.

    Raises
    ------
    ValidationError
        If required fields are missing or invalid.

    Examples
    --------
    >>> raw = {
    ...     "content": {
    ...         "title": "Apple Earnings Report",
    ...         "pubDate": "2026-01-27T23:33:53Z",
    ...         "canonicalUrl": {"url": "https://finance.yahoo.com/news/apple-earnings"},
    ...     }
    ... }
    >>> article = ticker_news_to_article(raw, "AAPL")
    >>> article.title
    'Apple Earnings Report'
    >>> article.source
    <ArticleSource.YFINANCE_TICKER: 'yfinance_ticker'>
    """
    logger.debug("Converting ticker news to article", ticker=ticker)

    content = raw.get("content", {})

    # Extract and validate required fields
    url = _extract_url(content)
    title = _extract_title(content)
    published_at = _extract_published_at(content)

    # Extract optional fields
    summary = content.get("summary")
    content_type = _map_content_type(content.get("contentType"))
    provider = _extract_provider(content)
    thumbnail = _extract_thumbnail(content)

    # Build metadata
    metadata = _build_metadata(content, ticker=ticker)

    try:
        article = Article(
            url=url,
            title=title,
            published_at=published_at,
            source=ArticleSource.YFINANCE_TICKER,
            summary=summary,
            content_type=content_type,
            provider=provider,
            thumbnail=thumbnail,
            related_tickers=[ticker],
            metadata=metadata,
        )
        logger.debug(
            "Successfully converted ticker news",
            ticker=ticker,
            title=title[:50] + "..." if len(title) > 50 else title,
        )
        return article
    except PydanticValidationError as e:
        logger.error("Pydantic validation failed", ticker=ticker, error=str(e))
        raise ValidationError(
            message=f"Invalid article data: {e}",
            field="article",
            value=raw,
        ) from e


def search_news_to_article(raw: dict[str, Any], query: str) -> Article:
    """Convert yfinance Search.news data to Article model.

    Parameters
    ----------
    raw : dict[str, Any]
        Raw news data from yfinance Search.news.
    query : str
        Search query used to fetch the news.

    Returns
    -------
    Article
        Converted Article instance.

    Raises
    ------
    ValidationError
        If required fields are missing or invalid.

    Examples
    --------
    >>> raw = {
    ...     "content": {
    ...         "title": "Federal Reserve Update",
    ...         "pubDate": "2026-01-27T20:15:00Z",
    ...         "canonicalUrl": {"url": "https://finance.yahoo.com/news/fed-update"},
    ...     }
    ... }
    >>> article = search_news_to_article(raw, "Federal Reserve")
    >>> article.source
    <ArticleSource.YFINANCE_SEARCH: 'yfinance_search'>
    >>> "Federal Reserve" in article.tags
    True
    """
    logger.debug("Converting search news to article", query=query)

    content = raw.get("content", {})

    # Extract and validate required fields
    url = _extract_url(content)
    title = _extract_title(content)
    published_at = _extract_published_at(content)

    # Extract optional fields
    summary = content.get("summary")
    content_type = _map_content_type(content.get("contentType"))
    provider = _extract_provider(content)
    thumbnail = _extract_thumbnail(content)

    # Build metadata with search query
    metadata = _build_metadata(content, query=query)

    try:
        article = Article(
            url=url,
            title=title,
            published_at=published_at,
            source=ArticleSource.YFINANCE_SEARCH,
            summary=summary,
            content_type=content_type,
            provider=provider,
            thumbnail=thumbnail,
            related_tickers=[],  # Search doesn't auto-populate tickers
            tags=[query],  # Add search query as tag
            metadata=metadata,
        )
        logger.debug(
            "Successfully converted search news",
            query=query,
            title=title[:50] + "..." if len(title) > 50 else title,
        )
        return article
    except PydanticValidationError as e:
        logger.error("Pydantic validation failed", query=query, error=str(e))
        raise ValidationError(
            message=f"Invalid article data: {e}",
            field="article",
            value=raw,
        ) from e


def fetch_with_retry(
    fetch_func: Callable[[], T],
    config: RetryConfig,
) -> T:
    """Execute a fetch operation with retry logic and exponential backoff.

    When all retries are exhausted and the last exception is a
    ``yfinance.exceptions.YFRateLimitError``, it is converted to
    ``RateLimitError`` so callers can handle rate-limiting uniformly.

    Parameters
    ----------
    fetch_func : Callable[[], T]
        The fetch function to execute.
    config : RetryConfig
        Retry configuration.

    Returns
    -------
    T
        The result of the fetch function.

    Raises
    ------
    RateLimitError
        If all retry attempts fail due to YFRateLimitError.
    SourceError
        If all retry attempts fail for other reasons.
    Exception
        If a non-retryable exception occurs.

    Examples
    --------
    >>> def fetch_data():
    ...     return ["article1", "article2"]
    >>> config = RetryConfig(max_attempts=3)
    >>> result = fetch_with_retry(fetch_data, config)
    >>> result
    ['article1', 'article2']
    """
    logger.debug(
        "Starting fetch with retry",
        max_attempts=config.max_attempts,
        initial_delay=config.initial_delay,
    )

    last_exception: Exception | None = None
    attempt = 0

    while attempt < config.max_attempts:
        try:
            result = fetch_func()
            logger.debug("Fetch succeeded", attempt=attempt + 1)
            return result
        except config.retryable_exceptions as e:
            last_exception = e
            attempt += 1
            logger.warning(
                "Retryable error occurred",
                attempt=attempt,
                max_attempts=config.max_attempts,
                error_type=type(e).__name__,
                error=str(e),
            )

            if attempt < config.max_attempts:
                delay = _calculate_delay(attempt, config)
                logger.debug("Waiting before retry", delay_seconds=delay)
                time.sleep(delay)
        except Exception as e:
            # Non-retryable exception, raise immediately
            logger.error(
                "Non-retryable error occurred",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    # All retries exhausted — check for YFRateLimitError before raising generic SourceError
    _try_raise_rate_limit_error(last_exception)

    error_msg = f"Max retries exceeded ({config.max_attempts} attempts)"
    logger.error(
        error_msg,
        last_error=str(last_exception) if last_exception else None,
    )
    raise SourceError(
        message=error_msg,
        source="yfinance",
        cause=last_exception,
        retryable=False,
    )


def validate_ticker(ticker: str) -> str:
    """Validate a ticker symbol.

    Parameters
    ----------
    ticker : str
        Ticker symbol to validate.

    Returns
    -------
    str
        Validated and normalized ticker (uppercase, trimmed).

    Raises
    ------
    ValidationError
        If the ticker is invalid.

    Examples
    --------
    >>> validate_ticker("aapl")
    'AAPL'
    >>> validate_ticker("  GOOGL  ")
    'GOOGL'
    >>> validate_ticker("^GSPC")
    '^GSPC'
    """
    # Strip whitespace
    ticker = ticker.strip()

    # Check for empty ticker
    if not ticker:
        logger.warning("Empty ticker provided")
        raise ValidationError(
            message="Ticker cannot be empty",
            field="ticker",
            value=ticker,
        )

    # Convert to uppercase
    ticker = ticker.upper()

    # Check length
    if len(ticker) > _MAX_TICKER_LENGTH:
        logger.warning("Ticker too long", ticker=ticker, length=len(ticker))
        raise ValidationError(
            message=f"Ticker too long (max {_MAX_TICKER_LENGTH} characters)",
            field="ticker",
            value=ticker,
        )

    # Check pattern
    if not _TICKER_PATTERN.match(ticker):
        logger.warning("Invalid ticker format", ticker=ticker)
        raise ValidationError(
            message="Ticker contains invalid characters",
            field="ticker",
            value=ticker,
        )

    logger.debug("Ticker validated", ticker=ticker)
    return ticker


def validate_query(query: str) -> str:
    """Validate a search query.

    Parameters
    ----------
    query : str
        Search query to validate.

    Returns
    -------
    str
        Validated and trimmed query.

    Raises
    ------
    ValidationError
        If the query is invalid.

    Examples
    --------
    >>> validate_query("Federal Reserve")
    'Federal Reserve'
    >>> validate_query("  inflation  ")
    'inflation'
    """
    # Strip whitespace
    query = query.strip()

    # Check for empty query
    if not query:
        logger.warning("Empty query provided")
        raise ValidationError(
            message="Query cannot be empty",
            field="query",
            value=query,
        )

    # Check length
    if len(query) > _MAX_QUERY_LENGTH:
        logger.warning("Query too long", query=query[:50], length=len(query))
        raise ValidationError(
            message=f"Query too long (max {_MAX_QUERY_LENGTH} characters)",
            field="query",
            value=query,
        )

    logger.debug("Query validated", query=query)
    return query


def fetch_all_with_polite_delay(
    identifiers: list[str],
    fetch_func: Callable[[str, int], FetchResult],
    count: int = 10,
) -> list[FetchResult]:
    """Fetch multiple identifiers with polite delays between requests.

    This is the common implementation for all yfinance source ``fetch_all``
    methods.  A polite delay is inserted between each request to avoid
    triggering Yahoo Finance rate limits.

    Parameters
    ----------
    identifiers : list[str]
        List of ticker symbols or search queries.
    fetch_func : Callable[[str, int], FetchResult]
        The fetch function to call for each identifier (typically
        ``self.fetch``).
    count : int, optional
        Maximum number of articles to fetch per identifier (default: 10).

    Returns
    -------
    list[FetchResult]
        List of FetchResult objects, one per identifier.
    """
    if not identifiers:
        logger.debug("Empty identifiers list, returning empty results")
        return []

    results: list[FetchResult] = []
    for i, identifier in enumerate(identifiers):
        if i > 0:
            apply_polite_delay()
        result = fetch_func(identifier, count)
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    logger.info(
        "Completed fetching news for multiple identifiers",
        total=len(results),
        success=success_count,
        failed=len(results) - success_count,
    )
    return results


# ============================================================================
# Private helper functions
# ============================================================================


def _extract_url(content: dict[str, Any]) -> HttpUrl:
    """Extract and validate URL from content."""
    canonical_url = content.get("canonicalUrl", {})
    url_str = canonical_url.get("url") if isinstance(canonical_url, dict) else None

    if not url_str:
        logger.error("URL missing from content")
        raise ValidationError(
            message="URL is required but missing",
            field="url",
            value=content,
        )

    try:
        # Validate URL format using Pydantic
        return HttpUrl(url_str)
    except PydanticValidationError as e:
        logger.error("Invalid URL format", url=url_str, error=str(e))
        raise ValidationError(
            message=f"Invalid URL format: {url_str}",
            field="url",
            value=url_str,
        ) from e


def _extract_title(content: dict[str, Any]) -> str:
    """Extract and validate title from content."""
    title = content.get("title")

    if not title or not isinstance(title, str) or not title.strip():
        logger.error("Title missing or empty")
        raise ValidationError(
            message="Title is required but missing or empty",
            field="title",
            value=title,
        )

    return title.strip()


def _extract_published_at(content: dict[str, Any]) -> datetime:
    """Extract and validate published_at from content."""
    pub_date = content.get("pubDate")

    if not pub_date:
        logger.error("Publication date missing")
        raise ValidationError(
            message="Publication date is required but missing",
            field="published_at",
            value=pub_date,
        )

    try:
        # Parse ISO 8601 format (handle Z suffix)
        if isinstance(pub_date, str):
            pub_date = pub_date.replace("Z", "+00:00")
            return datetime.fromisoformat(pub_date)
        raise ValueError("pubDate is not a string")
    except (ValueError, TypeError) as e:
        logger.error("Invalid date format", pub_date=pub_date, error=str(e))
        raise ValidationError(
            message=f"Invalid date format: {pub_date}",
            field="published_at",
            value=pub_date,
        ) from e


def _map_content_type(content_type: str | None) -> ContentType:
    """Map yfinance content type to internal enum."""
    if content_type is None:
        return ContentType.UNKNOWN
    return _CONTENT_TYPE_MAP.get(content_type, ContentType.UNKNOWN)


def _extract_provider(content: dict[str, Any]) -> Provider | None:
    """Extract provider information from content."""
    provider_data = content.get("provider")
    if not provider_data or not isinstance(provider_data, dict):
        return None

    name = provider_data.get("displayName")
    if not name:
        return None

    url_str = provider_data.get("url")
    url = None
    if url_str:
        with contextlib.suppress(PydanticValidationError):
            url = HttpUrl(url_str)

    return Provider(name=name, url=url)


def _extract_thumbnail(content: dict[str, Any]) -> Thumbnail | None:
    """Extract thumbnail information from content."""
    thumbnail_data = content.get("thumbnail")
    if not thumbnail_data or not isinstance(thumbnail_data, dict):
        return None

    url_str = thumbnail_data.get("originalUrl")
    if not url_str:
        return None

    try:
        url = HttpUrl(url_str)
        return Thumbnail(
            url=url,
            width=thumbnail_data.get("originalWidth"),
            height=thumbnail_data.get("originalHeight"),
        )
    except PydanticValidationError:
        # Invalid URL, skip thumbnail
        return None


def _build_metadata(
    content: dict[str, Any],
    ticker: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Build metadata dictionary from content."""
    metadata: dict[str, Any] = {}

    # Content type
    content_type = content.get("contentType")
    if content_type:
        metadata["yfinance_content_type"] = content_type

    # Editor's pick
    metadata_info = content.get("metadata", {})
    if isinstance(metadata_info, dict):
        editors_pick = metadata_info.get("editorsPick")
        if editors_pick is not None:
            metadata["editors_pick"] = editors_pick

    # Premium status
    finance_info = content.get("finance", {})
    if isinstance(finance_info, dict):
        premium_info = finance_info.get("premiumFinance", {})
        if isinstance(premium_info, dict):
            is_premium = premium_info.get("isPremiumNews")
            if is_premium is not None:
                metadata["is_premium"] = is_premium

    # Region and language
    canonical_url = content.get("canonicalUrl", {})
    if isinstance(canonical_url, dict):
        region = canonical_url.get("region")
        if region:
            metadata["region"] = region
        lang = canonical_url.get("lang")
        if lang:
            metadata["lang"] = lang

    # Search query (for search results)
    if query:
        metadata["search_query"] = query

    return metadata


def _try_raise_rate_limit_error(last_exception: Exception | None) -> None:
    """Raise RateLimitError if the last exception is YFRateLimitError.

    This converts yfinance's native rate-limit exception into the news
    package's ``RateLimitError`` so callers can handle it uniformly.

    Parameters
    ----------
    last_exception : Exception | None
        The last exception from retry attempts.

    Raises
    ------
    RateLimitError
        If ``last_exception`` is an instance of ``YFRateLimitError``.
    """
    # Lazy import to avoid hard dependency on yfinance at module level
    try:
        from yfinance.exceptions import YFRateLimitError
    except ImportError:
        return

    if isinstance(last_exception, YFRateLimitError):
        logger.warning(
            "YFRateLimitError detected, converting to RateLimitError",
            error=str(last_exception),
        )
        raise RateLimitError(source="yfinance") from last_exception


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry with exponential backoff and optional jitter."""
    # Exponential backoff: initial_delay * base^(attempt-1)
    delay = config.initial_delay * (config.exponential_base ** (attempt - 1))

    # Cap at max_delay
    delay = min(delay, config.max_delay)

    # Add jitter if enabled (±50% of delay)
    if config.jitter:
        jitter_range = delay * 0.5
        delay = delay + random.uniform(-jitter_range, jitter_range)  # nosec B311 - not used for security/crypto
        delay = max(0.0, delay)  # Ensure non-negative

    return delay


# Export all public symbols
__all__ = [
    "DEFAULT_DELAY_JITTER",
    "DEFAULT_POLITE_DELAY",
    "DEFAULT_YFINANCE_RETRY_CONFIG",
    "apply_polite_delay",
    "fetch_all_with_polite_delay",
    "fetch_with_retry",
    "search_news_to_article",
    "ticker_news_to_article",
    "validate_query",
    "validate_ticker",
]
