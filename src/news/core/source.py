"""Data source protocol for the news package.

This module defines the SourceProtocol, an abstract interface for fetching
news from various data sources (yfinance, scraper, etc.).

Examples
--------
>>> class YFinanceSource:
...     @property
...     def source_name(self) -> str:
...         return "yfinance_ticker"
...
...     @property
...     def source_type(self) -> ArticleSource:
...         return ArticleSource.YFINANCE_TICKER
...
...     def fetch(self, identifier: str, count: int = 10) -> FetchResult:
...         # Implementation here
...         ...
...
...     def fetch_all(
...         self, identifiers: list[str], count: int = 10
...     ) -> list[FetchResult]:
...         # Implementation here
...         ...
"""

from typing import Protocol, runtime_checkable

from utils_core.logging import get_logger

from .article import ArticleSource
from .result import FetchResult

logger = get_logger(__name__, module="source")


@runtime_checkable
class SourceProtocol(Protocol):
    """Protocol for news data sources.

    This protocol defines the interface that all news data sources must
    implement. It provides a unified way to fetch news from different
    sources (yfinance Ticker, yfinance Search, web scrapers, etc.).

    Attributes
    ----------
    source_name : str
        Human-readable name of the source (e.g., "yfinance_ticker").
    source_type : ArticleSource
        Type of the source from the ArticleSource enum.

    Methods
    -------
    fetch(identifier, count=10)
        Fetch news for a single identifier (ticker or query).
    fetch_all(identifiers, count=10)
        Fetch news for multiple identifiers.

    Notes
    -----
    - This is a `Protocol` class, so implementations don't need to
      explicitly inherit from it.
    - The `@runtime_checkable` decorator enables `isinstance()` checks.
    - Implementations should handle errors gracefully and return
      `FetchResult` with `success=False` on failure.

    Examples
    --------
    Creating a custom source:

    >>> class MySource:
    ...     @property
    ...     def source_name(self) -> str:
    ...         return "my_source"
    ...
    ...     @property
    ...     def source_type(self) -> ArticleSource:
    ...         return ArticleSource.SCRAPER
    ...
    ...     def fetch(self, identifier: str, count: int = 10) -> FetchResult:
    ...         # Fetch news for a single identifier
    ...         ...
    ...
    ...     def fetch_all(
    ...         self, identifiers: list[str], count: int = 10
    ...     ) -> list[FetchResult]:
    ...         return [self.fetch(ident, count) for ident in identifiers]

    Checking if an object implements the protocol:

    >>> isinstance(MySource(), SourceProtocol)
    True
    """

    @property
    def source_name(self) -> str:
        """Name of the data source.

        Returns
        -------
        str
            Human-readable name identifying this source.
            Examples: "yfinance_ticker", "yfinance_search", "scraper".

        Notes
        -----
        This name is used for logging and identifying the source
        in FetchResult objects.
        """
        ...

    @property
    def source_type(self) -> ArticleSource:
        """Type of the data source.

        Returns
        -------
        ArticleSource
            The ArticleSource enum value for this source.

        Notes
        -----
        This type is used to set the `source` field in Article objects.
        """
        ...

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single identifier.

        Parameters
        ----------
        identifier : str
            The identifier to fetch news for.
            For Ticker-based sources: ticker symbol (e.g., "AAPL", "^GSPC").
            For Search-based sources: search query (e.g., "Federal Reserve").
        count : int, optional
            Maximum number of articles to fetch (default: 10).

        Returns
        -------
        FetchResult
            Result containing fetched articles and status.
            On success: `success=True`, `articles` contains fetched items.
            On failure: `success=False`, `error` contains error details.

        Notes
        -----
        - Implementations should handle errors gracefully and return
          a FetchResult with `success=False` rather than raising exceptions.
        - The `ticker` or `query` field in FetchResult should be set
          based on the source type.

        Examples
        --------
        >>> source = YFinanceTickerSource()
        >>> result = source.fetch("AAPL", count=5)
        >>> result.success
        True
        >>> len(result.articles) <= 5
        True
        """
        ...

    def fetch_all(
        self,
        identifiers: list[str],
        count: int = 10,
    ) -> list[FetchResult]:
        """Fetch news for multiple identifiers.

        Parameters
        ----------
        identifiers : list[str]
            List of identifiers to fetch news for.
            For Ticker-based sources: list of ticker symbols.
            For Search-based sources: list of search queries.
        count : int, optional
            Maximum number of articles to fetch per identifier (default: 10).

        Returns
        -------
        list[FetchResult]
            List of FetchResult objects, one per identifier.
            Results are in the same order as the input identifiers.

        Notes
        -----
        - If `identifiers` is empty, returns an empty list.
        - Each identifier is processed independently; a failure for one
          identifier should not affect others.
        - Implementations may choose to process identifiers in parallel
          or sequentially.

        Examples
        --------
        >>> source = YFinanceTickerSource()
        >>> results = source.fetch_all(["AAPL", "GOOGL", "MSFT"], count=5)
        >>> len(results)
        3
        >>> all(r.success for r in results)
        True
        """
        ...


# Export all public symbols
__all__ = [
    "SourceProtocol",
]
