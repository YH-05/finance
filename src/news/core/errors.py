"""Custom exception classes for the news package.

This module provides a hierarchy of exceptions for error handling in the news
package. All exceptions inherit from the base NewsError class.

Exception Hierarchy
-------------------
- NewsError (base)
  - SourceError (data source errors)
    - RateLimitError (rate limiting, retryable)
  - ValidationError (input validation errors)

Examples
--------
>>> raise NewsError("Something went wrong")
>>> raise SourceError("Failed to fetch", source="yfinance", ticker="AAPL")
>>> raise ValidationError("Invalid ticker", field="ticker", value="")
>>> raise RateLimitError(source="yfinance", retry_after=60.0)
"""

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="errors")


class NewsError(Exception):
    """Base exception for the news package.

    All exceptions in the news package should inherit from this class.
    This allows catching all news-related errors with a single except clause.

    Examples
    --------
    >>> try:
    ...     raise NewsError("Something went wrong")
    ... except NewsError as e:
    ...     print(f"News error: {e}")
    News error: Something went wrong
    """

    pass


class SourceError(NewsError):
    """Exception raised when fetching data from a source fails.

    This exception is used for errors that occur while fetching news from
    external data sources (yfinance, scrapers, etc.).

    Parameters
    ----------
    message : str
        Human-readable error message.
    source : str
        Name of the data source (e.g., "yfinance", "scraper").
    ticker : str | None, optional
        Ticker symbol if applicable.
    cause : Exception | None, optional
        Original exception that caused this error.
    retryable : bool, optional
        Whether the operation can be retried.

    Attributes
    ----------
    source : str
        Name of the data source.
    ticker : str | None
        Ticker symbol if applicable.
    cause : Exception | None
        Original exception that caused this error.
    retryable : bool
        Whether the operation can be retried.

    Examples
    --------
    >>> error = SourceError(
    ...     message="Connection timeout",
    ...     source="yfinance",
    ...     ticker="AAPL",
    ...     retryable=True,
    ... )
    >>> error.source
    'yfinance'
    >>> error.retryable
    True
    """

    def __init__(
        self,
        message: str,
        source: str,
        ticker: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        """Initialize SourceError with source-specific information."""
        super().__init__(message)
        self.source = source
        self.ticker = ticker
        self.cause = cause
        self.retryable = retryable

        logger.debug(
            "SourceError created",
            message=message,
            source=source,
            ticker=ticker,
            retryable=retryable,
            has_cause=cause is not None,
        )


class ValidationError(NewsError):
    """Exception raised when input validation fails.

    This exception is used for validation errors, such as invalid ticker
    formats, empty values, or out-of-range parameters.

    Parameters
    ----------
    message : str
        Human-readable error message.
    field : str
        Name of the field that failed validation.
    value : object
        The invalid value that was provided.

    Attributes
    ----------
    field : str
        Name of the field that failed validation.
    value : object
        The invalid value that was provided.

    Examples
    --------
    >>> error = ValidationError(
    ...     message="Ticker cannot be empty",
    ...     field="ticker",
    ...     value="",
    ... )
    >>> error.field
    'ticker'
    >>> error.value
    ''
    """

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
    ) -> None:
        """Initialize ValidationError with field information."""
        super().__init__(message)
        self.field = field
        self.value = value

        logger.debug(
            "ValidationError created",
            message=message,
            field=field,
            value_type=type(value).__name__,
        )


class RateLimitError(SourceError):
    """Exception raised when a rate limit is exceeded.

    This exception is a specialized SourceError for rate limiting scenarios.
    It is always retryable and automatically generates an appropriate message.

    Parameters
    ----------
    source : str
        Name of the data source that imposed the rate limit.
    retry_after : float | None, optional
        Seconds to wait before retrying, if known.

    Attributes
    ----------
    retry_after : float | None
        Seconds to wait before retrying.

    Notes
    -----
    - The `retryable` attribute is always set to True.
    - The error message is automatically generated.

    Examples
    --------
    >>> error = RateLimitError(source="yfinance", retry_after=60.0)
    >>> str(error)
    'Rate limit exceeded for yfinance'
    >>> error.retryable
    True
    >>> error.retry_after
    60.0
    """

    def __init__(
        self,
        source: str,
        retry_after: float | None = None,
    ) -> None:
        """Initialize RateLimitError with retry information."""
        super().__init__(
            message=f"Rate limit exceeded for {source}",
            source=source,
            retryable=True,
        )
        self.retry_after = retry_after

        logger.warning(
            "Rate limit exceeded",
            source=source,
            retry_after=retry_after,
        )


# Export all public symbols
__all__ = [
    "NewsError",
    "RateLimitError",
    "SourceError",
    "ValidationError",
]
