"""yfinance stock news source module.

This module provides the StockNewsSource class for fetching news from individual
stocks using yfinance Ticker API.

Classes
-------
StockNewsSource
    Fetches news for individual stocks (mag7 and sector representative stocks).

Examples
--------
>>> from news.sources.yfinance.stock import StockNewsSource
>>> source = StockNewsSource(symbols_file="src/analyze/config/symbols.yaml")
>>> result = source.fetch("AAPL", count=10)
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

logger = get_logger(__name__, module="yfinance.stock")

# Default symbols file path
DEFAULT_SYMBOLS_FILE = Path("src/analyze/config/symbols.yaml")

# Default retry configuration (shared across all yfinance sources)
DEFAULT_RETRY_CONFIG = DEFAULT_YFINANCE_RETRY_CONFIG


class StockNewsSource:
    """News source for individual stocks using yfinance Ticker API.

    This class implements the SourceProtocol interface for fetching news
    from individual stocks including Magnificent 7 (MAG7) stocks and
    sector representative stocks.

    Parameters
    ----------
    symbols_file : str | Path
        Path to the symbols YAML file containing stock definitions.
    retry_config : RetryConfig | None, optional
        Retry configuration for network operations.
        If None, uses default configuration.

    Attributes
    ----------
    source_name : str
        Name of this source ("yfinance_ticker_stock").
    source_type : ArticleSource
        Type of this source (YFINANCE_TICKER).

    Examples
    --------
    >>> source = StockNewsSource(
    ...     symbols_file="src/analyze/config/symbols.yaml",
    ... )
    >>> result = source.fetch("AAPL", count=5)
    >>> result.success
    True

    >>> results = source.fetch_all(["AAPL", "MSFT", "NVDA"], count=10)
    >>> len(results)
    3
    """

    def __init__(
        self,
        symbols_file: str | Path,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize StockNewsSource.

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
            "Initializing StockNewsSource",
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
            "StockNewsSource initialized",
            symbol_count=len(self._symbols),
        )

    @property
    def source_name(self) -> str:
        """Return the name of this source.

        Returns
        -------
        str
            Source name ("yfinance_ticker_stock").
        """
        return "yfinance_ticker_stock"

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
        """Get the list of stock symbols.

        Returns the combined list of MAG7 stocks and sector representative
        stocks loaded from the symbols file.

        Returns
        -------
        list[str]
            List of ticker symbols for stocks.

        Examples
        --------
        >>> source = StockNewsSource("symbols.yaml")
        >>> symbols = source.get_symbols()
        >>> "AAPL" in symbols
        True
        >>> "JPM" in symbols
        True
        """
        return self._symbols.copy()

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        """Fetch news for a single stock ticker.

        Parameters
        ----------
        identifier : str
            Ticker symbol for the stock (e.g., "AAPL", "MSFT").
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
        >>> source = StockNewsSource("symbols.yaml")
        >>> result = source.fetch("AAPL", count=5)
        >>> result.success
        True
        """
        logger.debug(
            "Fetching news for stock",
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
                "Successfully fetched stock news",
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
                "Source error fetching stock news",
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
                "Unexpected error fetching stock news",
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
        """Fetch news for multiple stock tickers.

        Parameters
        ----------
        identifiers : list[str]
            List of ticker symbols (e.g., ["AAPL", "MSFT", "NVDA"]).
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
        >>> source = StockNewsSource("symbols.yaml")
        >>> results = source.fetch_all(["AAPL", "MSFT"], count=5)
        >>> len(results)
        2
        """
        return fetch_all_with_polite_delay(identifiers, self.fetch, count)

    def _load_symbols(self) -> None:
        """Load stock symbols from the symbols data.

        Extracts ticker symbols from the 'mag7' section and 'sector_stocks'
        section of the symbols YAML file. Duplicates are removed.
        """
        # Use a set to avoid duplicates
        symbols_set: set[str] = set()

        # Load mag7 symbols
        mag7_data = self._symbols_data.get("mag7", [])
        if isinstance(mag7_data, list):
            for item in mag7_data:
                if isinstance(item, dict) and "symbol" in item:
                    symbols_set.add(item["symbol"])
            logger.debug(
                "Loaded mag7 symbols",
                count=len(mag7_data),
            )

        # Load sector_stocks symbols
        sector_stocks_data = self._symbols_data.get("sector_stocks", {})
        if isinstance(sector_stocks_data, dict):
            sector_stock_count = 0
            for _sector_etf, stocks_list in sector_stocks_data.items():
                if isinstance(stocks_list, list):
                    for item in stocks_list:
                        if isinstance(item, dict) and "symbol" in item:
                            symbols_set.add(item["symbol"])
                            sector_stock_count += 1
            logger.debug(
                "Loaded sector_stocks symbols",
                count=sector_stock_count,
            )

        # Convert to sorted list for consistent ordering
        self._symbols = sorted(symbols_set)

        logger.debug(
            "Total stock symbols loaded",
            count=len(self._symbols),
        )


# Export all public symbols
__all__ = [
    "StockNewsSource",
]
