"""yfinance index news source module.

This module provides the IndexNewsSource class for fetching news from stock
market indices using yfinance Ticker API.

Classes
-------
IndexNewsSource
    Fetches news for stock market indices (e.g., ^GSPC, ^DJI, ^IXIC).

Examples
--------
>>> from news.sources.yfinance.index import IndexNewsSource
>>> source = IndexNewsSource(symbols_file="src/analyze/config/symbols.yaml")
>>> result = source.fetch("^GSPC", count=10)
>>> result.article_count
10
"""

from pathlib import Path
from typing import Any

import yfinance as yf

from utils_core.logging import get_logger

from ...config.models import ConfigLoader
from ...core.article import ArticleSource
from ...core.errors import SourceError
from ...core.result import FetchResult, RetryConfig
from .base import (
    DEFAULT_YFINANCE_RETRY_CONFIG,
    fetch_all_with_polite_delay,
    fetch_with_retry,
    ticker_news_to_article,
    validate_ticker,
)

logger = get_logger(__name__, module="yfinance.index")

# Default symbols file path
DEFAULT_SYMBOLS_FILE = Path("src/analyze/config/symbols.yaml")

# Default retry configuration (shared across all yfinance sources)
DEFAULT_RETRY_CONFIG = DEFAULT_YFINANCE_RETRY_CONFIG


class IndexNewsSource:
    """News source for stock market indices using yfinance Ticker API.

    This class implements the SourceProtocol interface for fetching news
    from stock market indices such as S&P 500 (^GSPC), Dow Jones (^DJI),
    NASDAQ Composite (^IXIC), and global indices.

    Parameters
    ----------
    symbols_file : str | Path
        Path to the symbols YAML file containing index definitions.
    regions : list[str] | None, optional
        List of regions to include (e.g., ["us", "global"]).
        If None, includes all regions.
    retry_config : RetryConfig | None, optional
        Retry configuration for network operations.
        If None, uses default configuration.

    Attributes
    ----------
    source_name : str
        Name of this source ("yfinance_ticker_index").
    source_type : ArticleSource
        Type of this source (YFINANCE_TICKER).

    Examples
    --------
    >>> source = IndexNewsSource(
    ...     symbols_file="src/analyze/config/symbols.yaml",
    ...     regions=["us"],
    ... )
    >>> result = source.fetch("^GSPC", count=5)
    >>> result.success
    True

    >>> results = source.fetch_all(["^GSPC", "^DJI"], count=10)
    >>> len(results)
    2
    """

    def __init__(
        self,
        symbols_file: str | Path,
        regions: list[str] | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize IndexNewsSource.

        Parameters
        ----------
        symbols_file : str | Path
            Path to the symbols YAML file.
        regions : list[str] | None, optional
            List of regions to include. If None, includes all.
        retry_config : RetryConfig | None, optional
            Retry configuration. If None, uses defaults.

        Raises
        ------
        FileNotFoundError
            If the symbols file does not exist.
        """
        self._symbols_file = Path(symbols_file)
        self._regions = regions
        self._retry_config = retry_config or DEFAULT_RETRY_CONFIG

        logger.info(
            "Initializing IndexNewsSource",
            symbols_file=str(self._symbols_file),
            regions=self._regions,
        )

        # Validate symbols file exists
        if not self._symbols_file.exists():
            logger.error("Symbols file not found", file_path=str(self._symbols_file))
            raise FileNotFoundError(f"Symbols file not found: {self._symbols_file}")

        # Load symbols
        self._loader = ConfigLoader()
        self._symbols_data = self._loader.load_symbols(self._symbols_file)
        self._symbols: list[str] = []
        self._load_symbols()

        logger.info(
            "IndexNewsSource initialized",
            symbol_count=len(self._symbols),
        )

    @property
    def source_name(self) -> str:
        """Return the name of this source.

        Returns
        -------
        str
            Source name ("yfinance_ticker_index").
        """
        return "yfinance_ticker_index"

    @property
    def source_type(self) -> ArticleSource:
        """Return the type of this source.

        Returns
        -------
        ArticleSource
            Source type (YFINANCE_TICKER).
        """
        return ArticleSource.YFINANCE_TICKER

    def get_symbols(self) -> list[str]:
        """Get the list of index symbols.

        Returns
        -------
        list[str]
            List of ticker symbols for indices.

        Examples
        --------
        >>> source = IndexNewsSource("symbols.yaml")
        >>> symbols = source.get_symbols()
        >>> "^GSPC" in symbols
        True
        """
        return self._symbols.copy()

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single index ticker.

        Parameters
        ----------
        identifier : str
            Ticker symbol for the index (e.g., "^GSPC", "^DJI").
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
        >>> source = IndexNewsSource("symbols.yaml")
        >>> result = source.fetch("^GSPC", count=5)
        >>> result.success
        True
        """
        logger.debug(
            "Fetching news for index",
            ticker=identifier,
            count=count,
        )

        try:
            # Validate ticker
            validated_ticker = validate_ticker(identifier)

            # Define fetch function for retry logic
            def do_fetch() -> list[dict[str, Any]]:
                ticker = yf.Ticker(validated_ticker)
                # Use get_news if available, otherwise fallback to news property
                if hasattr(ticker, "get_news"):
                    return ticker.get_news(count=count)  # type: ignore
                return ticker.news[:count] if ticker.news else []

            # Execute with retry
            raw_news = fetch_with_retry(do_fetch, self._retry_config)

            # Convert to Article models
            articles = []
            for raw_item in raw_news:
                try:
                    article = ticker_news_to_article(raw_item, validated_ticker)
                    articles.append(article)
                except Exception as e:
                    logger.warning(
                        "Failed to convert news item",
                        ticker=validated_ticker,
                        error=str(e),
                    )
                    continue

            logger.info(
                "Successfully fetched index news",
                ticker=validated_ticker,
                article_count=len(articles),
            )

            return FetchResult(
                articles=articles,
                success=True,
                ticker=validated_ticker,
            )

        except SourceError as e:
            logger.error(
                "Source error fetching index news",
                ticker=identifier,
                error=str(e),
            )
            return FetchResult(
                articles=[],
                success=False,
                ticker=identifier,
                error=e,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching index news",
                ticker=identifier,
                error=str(e),
                error_type=type(e).__name__,
            )
            return FetchResult(
                articles=[],
                success=False,
                ticker=identifier,
                error=SourceError(
                    message=str(e),
                    source=self.source_name,
                    ticker=identifier,
                    cause=e,
                ),
            )

    def fetch_all(
        self,
        identifiers: list[str],
        count: int = 10,
    ) -> list[FetchResult]:
        """Fetch news for multiple index tickers.

        Parameters
        ----------
        identifiers : list[str]
            List of ticker symbols (e.g., ["^GSPC", "^DJI"]).
        count : int, optional
            Maximum number of articles to fetch per ticker (default: 10).

        Returns
        -------
        list[FetchResult]
            List of FetchResult objects, one per ticker.
            Results are in the same order as the input identifiers.

        Notes
        -----
        If an error occurs for one ticker, processing continues to the next.
        Failed tickers will have success=False in their FetchResult.

        Examples
        --------
        >>> source = IndexNewsSource("symbols.yaml")
        >>> results = source.fetch_all(["^GSPC", "^DJI"], count=5)
        >>> len(results)
        2
        """
        return fetch_all_with_polite_delay(identifiers, self.fetch, count)

    def _load_symbols(self) -> None:
        """Load index symbols from the symbols data.

        Extracts ticker symbols from the 'indices' section of the
        symbols YAML file, optionally filtering by region.
        """
        indices_data = self._symbols_data.get("indices", {})

        if not isinstance(indices_data, dict):
            logger.warning(
                "indices section is not a dict", data_type=type(indices_data)
            )
            return

        for region, symbols_list in indices_data.items():
            # Skip if regions filter is specified and this region is not included
            if self._regions and region not in self._regions:
                continue

            if isinstance(symbols_list, list):
                for item in symbols_list:
                    if isinstance(item, dict) and "symbol" in item:
                        self._symbols.append(item["symbol"])

        logger.debug(
            "Loaded index symbols",
            count=len(self._symbols),
            regions=self._regions or "all",
        )


# Export all public symbols
__all__ = [
    "IndexNewsSource",
]
