"""yfinance sector news source module.

This module provides the SectorNewsSource class for fetching news from sector
ETFs using yfinance Ticker API.

Classes
-------
SectorNewsSource
    Fetches news for sector ETFs (e.g., XLF, XLK, XLV).

Examples
--------
>>> from news.sources.yfinance.sector import SectorNewsSource
>>> source = SectorNewsSource(symbols_file="src/analyze/config/symbols.yaml")
>>> result = source.fetch("XLF", count=10)
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

logger = get_logger(__name__, module="yfinance.sector")

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


class SectorNewsSource:
    """News source for sector ETFs using yfinance Ticker API.

    This class implements the SourceProtocol interface for fetching news
    from sector ETFs such as Financial (XLF), Technology (XLK),
    Health Care (XLV), and other sector SPDRs.

    Parameters
    ----------
    symbols_file : str | Path
        Path to the symbols YAML file containing sector definitions.
    retry_config : RetryConfig | None, optional
        Retry configuration for network operations.
        If None, uses default configuration.

    Attributes
    ----------
    source_name : str
        Name of this source ("yfinance_ticker_sector").
    source_type : ArticleSource
        Type of this source (YFINANCE_TICKER).

    Examples
    --------
    >>> source = SectorNewsSource(
    ...     symbols_file="src/analyze/config/symbols.yaml",
    ... )
    >>> result = source.fetch("XLF", count=5)
    >>> result.success
    True

    >>> results = source.fetch_all(["XLF", "XLK"], count=10)
    >>> len(results)
    2
    """

    def __init__(
        self,
        symbols_file: str | Path,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize SectorNewsSource.

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
            "Initializing SectorNewsSource",
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
            "SectorNewsSource initialized",
            symbol_count=len(self._symbols),
        )

    @property
    def source_name(self) -> str:
        """Return the name of this source.

        Returns
        -------
        str
            Source name ("yfinance_ticker_sector").
        """
        return "yfinance_ticker_sector"

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
        """Get the list of sector ETF symbols.

        Returns
        -------
        list[str]
            List of ticker symbols for sector ETFs.

        Examples
        --------
        >>> source = SectorNewsSource("symbols.yaml")
        >>> symbols = source.get_symbols()
        >>> "XLF" in symbols
        True
        """
        return self._symbols.copy()

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single sector ETF ticker.

        Parameters
        ----------
        identifier : str
            Ticker symbol for the sector ETF (e.g., "XLF", "XLK").
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
        >>> source = SectorNewsSource("symbols.yaml")
        >>> result = source.fetch("XLF", count=5)
        >>> result.success
        True
        """
        logger.debug(
            "Fetching news for sector ETF",
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
                "Successfully fetched sector ETF news",
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
                "Source error fetching sector ETF news",
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
                "Unexpected error fetching sector ETF news",
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
        """Fetch news for multiple sector ETF tickers.

        Parameters
        ----------
        identifiers : list[str]
            List of ticker symbols (e.g., ["XLF", "XLK"]).
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
        >>> source = SectorNewsSource("symbols.yaml")
        >>> results = source.fetch_all(["XLF", "XLK"], count=5)
        >>> len(results)
        2
        """
        if not identifiers:
            logger.debug("Empty identifiers list, returning empty results")
            return []

        logger.info(
            "Fetching news for multiple sector ETFs",
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
            "Completed fetching news for multiple sector ETFs",
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
        )

        return results

    def _load_symbols(self) -> None:
        """Load sector ETF symbols from the symbols data.

        Extracts ticker symbols from the 'sectors' section of the
        symbols YAML file.
        """
        sectors_data = self._symbols_data.get("sectors", [])

        if not isinstance(sectors_data, list):
            logger.warning(
                "sectors section is not a list", data_type=type(sectors_data)
            )
            return

        for item in sectors_data:
            if isinstance(item, dict) and "symbol" in item:
                self._symbols.append(item["symbol"])

        logger.debug(
            "Loaded sector ETF symbols",
            count=len(self._symbols),
        )


# Export all public symbols
__all__ = [
    "SectorNewsSource",
]
