"""yfinance commodity news source module.

This module provides the CommodityNewsSource class for fetching news from
commodity futures using yfinance Ticker API.

Classes
-------
CommodityNewsSource
    Fetches news for commodity futures (e.g., GC=F, CL=F, SI=F).

Examples
--------
>>> from news.sources.yfinance.commodity import CommodityNewsSource
>>> source = CommodityNewsSource(symbols_file="src/analyze/config/symbols.yaml")
>>> result = source.fetch("GC=F", count=10)
>>> result.article_count
10
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
    ticker_news_to_article,
    validate_ticker,
)

logger = get_logger(__name__, module="yfinance.commodity")

# Default symbols file path
DEFAULT_SYMBOLS_FILE = Path("src/analyze/config/symbols.yaml")

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


class CommodityNewsSource:
    """News source for commodity futures using yfinance Ticker API.

    This class implements the SourceProtocol interface for fetching news
    from commodity futures such as Gold (GC=F), Silver (SI=F),
    Crude Oil (CL=F, BZ=F), and agricultural commodities.

    Parameters
    ----------
    symbols_file : str | Path
        Path to the symbols YAML file containing commodity definitions.
    retry_config : RetryConfig | None, optional
        Retry configuration for network operations.
        If None, uses default configuration.

    Attributes
    ----------
    source_name : str
        Name of this source ("yfinance_ticker_commodity").
    source_type : ArticleSource
        Type of this source (YFINANCE_TICKER).

    Examples
    --------
    >>> source = CommodityNewsSource(
    ...     symbols_file="src/analyze/config/symbols.yaml",
    ... )
    >>> result = source.fetch("GC=F", count=5)
    >>> result.success
    True

    >>> results = source.fetch_all(["GC=F", "CL=F"], count=10)
    >>> len(results)
    2
    """

    def __init__(
        self,
        symbols_file: str | Path,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize CommodityNewsSource.

        Parameters
        ----------
        symbols_file : str | Path
            Path to the symbols YAML file.
        retry_config : RetryConfig | None, optional
            Retry configuration. If None, uses defaults.

        Raises
        ------
        FileNotFoundError
            If the symbols file does not exist.
        """
        self._symbols_file = Path(symbols_file)
        self._retry_config = retry_config or DEFAULT_RETRY_CONFIG

        logger.info(
            "Initializing CommodityNewsSource",
            symbols_file=str(self._symbols_file),
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
            "CommodityNewsSource initialized",
            symbol_count=len(self._symbols),
        )

    @property
    def source_name(self) -> str:
        """Return the name of this source.

        Returns
        -------
        str
            Source name ("yfinance_ticker_commodity").
        """
        return "yfinance_ticker_commodity"

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
        """Get the list of commodity futures symbols.

        Returns
        -------
        list[str]
            List of ticker symbols for commodity futures.

        Examples
        --------
        >>> source = CommodityNewsSource("symbols.yaml")
        >>> symbols = source.get_symbols()
        >>> "GC=F" in symbols
        True
        """
        return self._symbols.copy()

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single commodity ticker.

        Parameters
        ----------
        identifier : str
            Ticker symbol for the commodity (e.g., "GC=F", "CL=F").
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
        >>> source = CommodityNewsSource("symbols.yaml")
        >>> result = source.fetch("GC=F", count=5)
        >>> result.success
        True
        """
        logger.debug(
            "Fetching news for commodity",
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
                    return ticker.get_news(count=count)
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
                "Successfully fetched commodity news",
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
                "Source error fetching commodity news",
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
                "Unexpected error fetching commodity news",
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
        """Fetch news for multiple commodity tickers.

        Parameters
        ----------
        identifiers : list[str]
            List of ticker symbols (e.g., ["GC=F", "CL=F"]).
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
        >>> source = CommodityNewsSource("symbols.yaml")
        >>> results = source.fetch_all(["GC=F", "CL=F"], count=5)
        >>> len(results)
        2
        """
        if not identifiers:
            logger.debug("Empty identifiers list, returning empty results")
            return []

        logger.info(
            "Fetching news for multiple commodities",
            ticker_count=len(identifiers),
            count=count,
        )

        results: list[FetchResult] = []
        for i, ticker in enumerate(identifiers):
            if i > 0:
                apply_polite_delay()
            result = self.fetch(ticker, count)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(
            "Completed fetching news for multiple commodities",
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
        )

        return results

    def _load_symbols(self) -> None:
        """Load commodity symbols from the symbols data.

        Extracts ticker symbols from the 'commodities' section of the
        symbols YAML file.
        """
        commodities_data = self._symbols_data.get("commodities", [])

        if not isinstance(commodities_data, list):
            logger.warning(
                "commodities section is not a list", data_type=type(commodities_data)
            )
            return

        for item in commodities_data:
            if isinstance(item, dict) and "symbol" in item:
                self._symbols.append(item["symbol"])

        logger.debug(
            "Loaded commodity symbols",
            count=len(self._symbols),
        )


# Export all public symbols
__all__ = [
    "CommodityNewsSource",
]
