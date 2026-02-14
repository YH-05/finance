"""yfinance search news source module.

This module provides the SearchNewsSource class for fetching theme-based news
using yfinance Search API with arbitrary keyword queries.

Unlike MacroNewsSource (which is specialized for macro economics keywords),
SearchNewsSource is a general-purpose search source that can be used for any
topic (AI, semiconductors, EV, biotech, etc.).

Classes
-------
SearchNewsSource
    Fetches news for arbitrary keywords using yfinance Search API.

Examples
--------
>>> from news.sources.yfinance.search import SearchNewsSource
>>> source = SearchNewsSource(keywords=["AI stocks", "semiconductor shortage"])
>>> result = source.fetch("AI stocks", count=10)
>>> result.article_count
10

>>> source = SearchNewsSource.from_config(
...     "data/config/news_search_keywords.yaml",
...     section="search_keywords",
...     category="tech",
... )
>>> result = source.fetch("AI stocks", count=5)
"""

from pathlib import Path
from typing import Any

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from utils_core.logging import get_logger

from ...config.models import ConfigLoader
from ...core.article import ArticleSource
from ...core.errors import SourceError
from ...core.result import FetchResult, RetryConfig
from .base import (
    apply_polite_delay,
    fetch_with_retry,
    search_news_to_article,
    validate_query,
)

logger = get_logger(__name__, module="yfinance.search")

# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        YFRateLimitError,
    ),
)


class SearchNewsSource:
    """General-purpose news source using yfinance Search API.

    This class implements the SourceProtocol interface for fetching news
    using arbitrary keyword-based search queries. It supports both direct
    keyword initialization and configuration file-based initialization.

    Parameters
    ----------
    keywords : list[str]
        List of search keywords.
    retry_config : RetryConfig | None, optional
        Retry configuration for network operations.
        If None, uses default configuration.

    Attributes
    ----------
    source_name : str
        Name of this source ("yfinance_search").
    source_type : ArticleSource
        Type of this source (YFINANCE_SEARCH).

    Examples
    --------
    Direct keyword initialization:

    >>> source = SearchNewsSource(
    ...     keywords=["AI stocks", "semiconductor shortage"],
    ... )
    >>> result = source.fetch("AI stocks", count=5)
    >>> result.success
    True

    From configuration file:

    >>> source = SearchNewsSource.from_config(
    ...     "data/config/news_search_keywords.yaml",
    ...     section="search_keywords",
    ...     category="tech",
    ... )
    >>> keywords = source.get_keywords()
    >>> len(keywords) > 0
    True
    """

    def __init__(
        self,
        keywords: list[str],
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize SearchNewsSource with a keyword list.

        Parameters
        ----------
        keywords : list[str]
            List of search keywords.
        retry_config : RetryConfig | None, optional
            Retry configuration. If None, uses defaults.
        """
        self._keywords = list(keywords)
        self._retry_config = retry_config or DEFAULT_RETRY_CONFIG

        logger.info(
            "Initializing SearchNewsSource",
            keyword_count=len(self._keywords),
        )

    @classmethod
    def from_config(
        cls,
        config_file: str | Path,
        section: str,
        category: str | None = None,
        categories: list[str] | None = None,
        retry_config: RetryConfig | None = None,
    ) -> "SearchNewsSource":
        """Create SearchNewsSource from a configuration file.

        Loads keywords from a YAML configuration file organized by sections
        and categories.

        Parameters
        ----------
        config_file : str | Path
            Path to the keywords YAML configuration file.
        section : str
            Section name in the YAML file containing keyword categories
            (e.g., "search_keywords", "macro_keywords").
        category : str | None, optional
            Single category to include (e.g., "tech").
            Mutually exclusive with `categories`.
        categories : list[str] | None, optional
            List of categories to include (e.g., ["tech", "energy"]).
            If None and `category` is None, includes all categories.
        retry_config : RetryConfig | None, optional
            Retry configuration. If None, uses defaults.

        Returns
        -------
        SearchNewsSource
            Configured SearchNewsSource instance.

        Raises
        ------
        FileNotFoundError
            If the configuration file does not exist.

        Examples
        --------
        Single category:

        >>> source = SearchNewsSource.from_config(
        ...     "keywords.yaml",
        ...     section="search_keywords",
        ...     category="tech",
        ... )

        Multiple categories:

        >>> source = SearchNewsSource.from_config(
        ...     "keywords.yaml",
        ...     section="search_keywords",
        ...     categories=["tech", "energy"],
        ... )

        All categories:

        >>> source = SearchNewsSource.from_config(
        ...     "keywords.yaml",
        ...     section="search_keywords",
        ... )
        """
        config_path = Path(config_file)

        logger.info(
            "Creating SearchNewsSource from config",
            config_file=str(config_path),
            section=section,
            category=category,
            categories=categories,
        )

        # Validate file exists
        if not config_path.exists():
            logger.error("Config file not found", file_path=str(config_path))
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load configuration data
        loader = ConfigLoader()
        config_data = loader.load_symbols(config_path)

        # Extract keywords from the specified section
        keywords = _extract_keywords_from_section(
            config_data,
            section=section,
            category=category,
            categories=categories,
        )

        logger.info(
            "Keywords loaded from config",
            keyword_count=len(keywords),
            section=section,
        )

        return cls(keywords=keywords, retry_config=retry_config)

    @property
    def source_name(self) -> str:
        """Return the name of this source.

        Returns
        -------
        str
            Source name ("yfinance_search").
        """
        return "yfinance_search"

    @property
    def source_type(self) -> ArticleSource:
        """Return the type of this source.

        Returns
        -------
        ArticleSource
            Source type (YFINANCE_SEARCH).
        """
        return ArticleSource.YFINANCE_SEARCH

    def get_keywords(self) -> list[str]:
        """Get the list of search keywords.

        Returns a copy of the keyword list to prevent external modification.

        Returns
        -------
        list[str]
            List of search keywords.

        Examples
        --------
        >>> source = SearchNewsSource(keywords=["AI stocks", "EV market"])
        >>> source.get_keywords()
        ['AI stocks', 'EV market']
        """
        return self._keywords.copy()

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single search query.

        Parameters
        ----------
        identifier : str
            Search query keyword (e.g., "AI stocks", "semiconductor shortage").
        count : int, optional
            Maximum number of articles to fetch (default: 10).

        Returns
        -------
        FetchResult
            Result containing fetched articles and status.
            On success: success=True, articles contains fetched items.
            On failure: success=False, error contains error details.

        Examples
        --------
        >>> source = SearchNewsSource(keywords=["AI stocks"])
        >>> result = source.fetch("AI stocks", count=5)
        >>> result.success
        True
        """
        logger.debug(
            "Fetching search news",
            query=identifier,
            count=count,
        )

        try:
            # Validate query
            validated_query = validate_query(identifier)

            # Define fetch function for retry logic
            def do_fetch() -> list[dict[str, Any]]:
                search = yf.Search(validated_query, news_count=count)
                return search.news if search.news else []

            # Execute with retry
            raw_news = fetch_with_retry(do_fetch, self._retry_config)

            # Convert to Article models
            articles = []
            for raw_item in raw_news:
                try:
                    article = search_news_to_article(raw_item, validated_query)
                    articles.append(article)
                except Exception as e:
                    logger.warning(
                        "Failed to convert news item",
                        query=validated_query,
                        error=str(e),
                    )
                    continue

            logger.info(
                "Successfully fetched search news",
                query=validated_query,
                article_count=len(articles),
            )

            return FetchResult(
                articles=articles,
                success=True,
                query=validated_query,
            )

        except SourceError as e:
            logger.error(
                "Source error fetching search news",
                query=identifier,
                error=str(e),
            )
            return FetchResult(
                articles=[],
                success=False,
                query=identifier,
                error=e,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching search news",
                query=identifier,
                error=str(e),
                error_type=type(e).__name__,
            )
            return FetchResult(
                articles=[],
                success=False,
                query=identifier,
                error=SourceError(
                    message=str(e),
                    source=self.source_name,
                    cause=e,
                ),
            )

    def fetch_all(
        self,
        identifiers: list[str],
        count: int = 10,
    ) -> list[FetchResult]:
        """Fetch news for multiple search queries.

        Parameters
        ----------
        identifiers : list[str]
            List of search queries (e.g., ["AI stocks", "EV market"]).
        count : int, optional
            Maximum number of articles to fetch per query (default: 10).

        Returns
        -------
        list[FetchResult]
            List of FetchResult objects, one per query.
            Results are in the same order as the input identifiers.

        Notes
        -----
        If an error occurs for one query, processing continues to the next.
        Failed queries will have success=False in their FetchResult.

        Examples
        --------
        >>> source = SearchNewsSource(keywords=["AI stocks", "EV market"])
        >>> results = source.fetch_all(["AI stocks", "EV market"], count=5)
        >>> len(results)
        2
        """
        if not identifiers:
            logger.debug("Empty identifiers list, returning empty results")
            return []

        logger.info(
            "Fetching news for multiple search queries",
            query_count=len(identifiers),
            count=count,
        )

        results: list[FetchResult] = []
        for i, query in enumerate(identifiers):
            if i > 0:
                apply_polite_delay()
            result = self.fetch(query, count)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(
            "Completed fetching news for multiple search queries",
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
        )

        return results


# ============================================================================
# Private helper functions
# ============================================================================


def _extract_keywords_from_section(
    config_data: dict[str, Any],
    section: str,
    category: str | None = None,
    categories: list[str] | None = None,
) -> list[str]:
    """Extract keywords from a configuration data section.

    Parameters
    ----------
    config_data : dict[str, Any]
        Full configuration data loaded from YAML.
    section : str
        Section name containing keyword categories.
    category : str | None, optional
        Single category to include.
    categories : list[str] | None, optional
        List of categories to include.

    Returns
    -------
    list[str]
        Extracted keyword list.
    """
    section_data = config_data.get(section, {})

    if not isinstance(section_data, dict):
        logger.warning(
            "Section is not a dict",
            section=section,
            data_type=type(section_data).__name__,
        )
        return []

    # Determine which categories to include
    if category is not None:
        target_categories = [category]
    elif categories is not None:
        target_categories = categories
    else:
        target_categories = None  # Include all

    keywords: list[str] = []
    for cat_name, keywords_list in section_data.items():
        # Skip if category filter is active and this category is excluded
        if target_categories is not None and cat_name not in target_categories:
            continue

        if isinstance(keywords_list, list):
            for keyword in keywords_list:
                if isinstance(keyword, str) and keyword.strip():
                    keywords.append(keyword.strip())
        else:
            logger.warning(
                "Category value is not a list, skipping",
                category=cat_name,
                data_type=type(keywords_list).__name__,
            )

    logger.debug(
        "Extracted keywords from section",
        section=section,
        count=len(keywords),
        target_categories=target_categories or "all",
    )

    return keywords


# Export all public symbols
__all__ = [
    "SearchNewsSource",
]
