"""YFinance data fetcher for market data retrieval.

This module provides a concrete implementation of BaseDataFetcher
using the yfinance library to fetch market data from Yahoo Finance.
"""

import re
from datetime import datetime

import pandas as pd
import yfinance as yf

from ..errors import DataFetchError, ErrorCode
from ..types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)
from ..utils.cache import SQLiteCache, generate_cache_key
from ..utils.logging_config import get_logger
from ..utils.retry import with_retry
from .base_fetcher import BaseDataFetcher

logger = get_logger(__name__, module="yfinance_fetcher")

# Valid yfinance symbol pattern
# Supports: AAPL, BRK.B, BRK-B, ^GSPC (indices), USDJPY=X (forex)
YFINANCE_SYMBOL_PATTERN = re.compile(r"^[\^]?[A-Z0-9.\-]+(=X)?$", re.IGNORECASE)


class YFinanceFetcher(BaseDataFetcher):
    """Data fetcher using Yahoo Finance (yfinance) API.

    Fetches OHLCV data for stocks, indices, forex, and other
    financial instruments supported by Yahoo Finance.

    Parameters
    ----------
    cache : SQLiteCache | None
        Cache instance for storing fetched data.
        If None, caching is disabled.
    cache_config : CacheConfig | None
        Configuration for cache behavior.
        Only used if cache is None.
    retry_config : RetryConfig | None
        Configuration for retry behavior on API errors.

    Attributes
    ----------
    source : DataSource
        Always returns DataSource.YFINANCE

    Examples
    --------
    >>> fetcher = YFinanceFetcher()
    >>> options = FetchOptions(
    ...     symbols=["AAPL", "GOOGL"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-12-31",
    ... )
    >>> results = fetcher.fetch(options)
    >>> len(results)
    2
    """

    def __init__(
        self,
        cache: SQLiteCache | None = None,
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._cache = cache
        self._cache_config = cache_config
        self._retry_config = retry_config

        logger.debug(
            "Initializing YFinanceFetcher",
            cache_enabled=cache is not None,
            retry_enabled=retry_config is not None,
        )

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.YFINANCE
        """
        return DataSource.YFINANCE

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for Yahoo Finance.

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol matches yfinance format

        Examples
        --------
        >>> fetcher.validate_symbol("AAPL")
        True
        >>> fetcher.validate_symbol("^GSPC")
        True
        >>> fetcher.validate_symbol("USDJPY=X")
        True
        >>> fetcher.validate_symbol("")
        False
        """
        if not symbol or not symbol.strip():
            return False

        return bool(YFINANCE_SYMBOL_PATTERN.match(symbol.strip()))

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch market data for the given options.

        Parameters
        ----------
        options : FetchOptions
            Options specifying symbols, date range, and other parameters

        Returns
        -------
        list[MarketDataResult]
            List of results for each requested symbol

        Raises
        ------
        DataFetchError
            If fetching fails for any symbol
        ValidationError
            If options contain invalid parameters

        Examples
        --------
        >>> options = FetchOptions(symbols=["AAPL"])
        >>> results = fetcher.fetch(options)
        >>> results[0].symbol
        'AAPL'
        """
        self._validate_options(options)

        logger.info(
            "Fetching market data",
            symbols=options.symbols,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
            interval=options.interval.value,
        )

        results: list[MarketDataResult] = []

        for symbol in options.symbols:
            result = self._fetch_single(symbol, options)
            results.append(result)

        logger.info(
            "Fetch completed",
            total_symbols=len(options.symbols),
            successful=len([r for r in results if not r.is_empty]),
            from_cache=len([r for r in results if r.from_cache]),
        )

        return results

    def _fetch_single(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> MarketDataResult:
        """Fetch data for a single symbol.

        Parameters
        ----------
        symbol : str
            The symbol to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        MarketDataResult
            The fetch result
        """
        logger.debug("Fetching single symbol", symbol=symbol)

        # Check cache first
        if self._cache is not None and options.use_cache:
            cached = self._get_from_cache(symbol, options)
            if cached is not None:
                return cached

        # Fetch from API
        data = self._fetch_from_api(symbol, options)

        # Cache the result
        if self._cache is not None and options.use_cache and not data.empty:
            self._save_to_cache(symbol, options, data)

        return self._create_result(
            symbol=symbol,
            data=data,
            from_cache=False,
            metadata={
                "interval": options.interval.value,
                "source": "yfinance",
            },
        )

    def _get_from_cache(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> MarketDataResult | None:
        """Try to get data from cache.

        Parameters
        ----------
        symbol : str
            The symbol to look up
        options : FetchOptions
            Fetch options for cache key

        Returns
        -------
        MarketDataResult | None
            Cached result if found, None otherwise
        """
        cache_key = generate_cache_key(
            symbol=symbol,
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
            source=self.source.value,
        )

        assert self._cache is not None  # nosec B101
        cached_data = self._cache.get(cache_key)

        if cached_data is not None and isinstance(cached_data, pd.DataFrame):
            logger.debug("Cache hit", symbol=symbol)
            return self._create_result(
                symbol=symbol,
                data=cached_data,
                from_cache=True,
                metadata={
                    "interval": options.interval.value,
                    "source": "cache",
                },
            )

        return None

    def _save_to_cache(
        self,
        symbol: str,
        options: FetchOptions,
        data: pd.DataFrame,
    ) -> None:
        """Save data to cache.

        Parameters
        ----------
        symbol : str
            The symbol
        options : FetchOptions
            Fetch options for cache key
        data : pd.DataFrame
            Data to cache
        """
        cache_key = generate_cache_key(
            symbol=symbol,
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
            source=self.source.value,
        )

        ttl = self._cache_config.ttl_seconds if self._cache_config else None

        assert self._cache is not None  # nosec B101
        self._cache.set(
            cache_key,
            data,
            ttl=ttl,
            metadata={
                "symbol": symbol,
                "interval": options.interval.value,
            },
        )

        logger.debug("Data cached", symbol=symbol)

    def _fetch_from_api(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance API.

        Parameters
        ----------
        symbol : str
            The symbol to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Normalized OHLCV data

        Raises
        ------
        DataFetchError
            If the API call fails
        """
        logger.debug("Fetching from yfinance API", symbol=symbol)

        try:
            # Apply retry if configured
            if self._retry_config:
                return self._fetch_with_retry(symbol, options)
            else:
                return self._do_fetch(symbol, options)

        except DataFetchError:
            raise
        except Exception as e:
            logger.error(
                "API fetch failed",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataFetchError(
                f"Failed to fetch data for {symbol}: {e}",
                symbol=symbol,
                source=self.source.value,
                code=ErrorCode.API_ERROR,
                cause=e,
            ) from e

    def _fetch_with_retry(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Fetch with retry decorator applied.

        Parameters
        ----------
        symbol : str
            The symbol to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Normalized OHLCV data
        """

        @with_retry(config=self._retry_config)
        def fetch_inner() -> pd.DataFrame:
            return self._do_fetch(symbol, options)

        return fetch_inner()

    def _do_fetch(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Execute the actual yfinance fetch.

        Parameters
        ----------
        symbol : str
            The symbol to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Normalized OHLCV data

        Raises
        ------
        DataFetchError
            If the symbol is invalid or no data is returned
        """
        ticker = yf.Ticker(symbol)

        # Convert dates to string format for yfinance
        start = self._format_date(options.start_date)
        end = self._format_date(options.end_date)

        # Map interval enum to yfinance format
        interval = self._map_interval(options.interval)

        logger.debug(
            "Calling yfinance.download",
            symbol=symbol,
            start=start,
            end=end,
            interval=interval,
        )

        # Fetch historical data
        df = ticker.history(
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            actions=False,
        )

        if df.empty:
            logger.warning("No data returned for symbol", symbol=symbol)
            # Check if symbol is valid by trying to get info
            try:
                info = ticker.info
                if not info or info.get("regularMarketPrice") is None:
                    raise DataFetchError(
                        f"Invalid or delisted symbol: {symbol}",
                        symbol=symbol,
                        source=self.source.value,
                        code=ErrorCode.INVALID_SYMBOL,
                    )
            except DataFetchError:
                raise
            except Exception as e:
                # Log but don't fail - empty DataFrame will be returned
                logger.debug(
                    "Could not validate symbol info",
                    symbol=symbol,
                    error=str(e),
                )

            return pd.DataFrame(
                columns=pd.Index(["open", "high", "low", "close", "volume"])
            )

        # Normalize the dataframe
        normalized = self.normalize_dataframe(df, symbol)

        logger.debug(
            "Data fetched successfully",
            symbol=symbol,
            rows=len(normalized),
            date_range=f"{normalized.index.min()} to {normalized.index.max()}"
            if not normalized.empty
            else "empty",
        )

        return normalized

    def _format_date(
        self,
        date: datetime | str | None,
    ) -> str | None:
        """Format a date for yfinance API.

        Parameters
        ----------
        date : datetime | str | None
            Date to format

        Returns
        -------
        str | None
            Formatted date string or None
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)

    def _map_interval(self, interval: Interval) -> str:
        """Map Interval enum to yfinance interval string.

        Parameters
        ----------
        interval : Interval
            Interval enum value

        Returns
        -------
        str
            yfinance interval string
        """
        # Interval enum values are already in yfinance format
        return interval.value


__all__ = [
    "YFINANCE_SYMBOL_PATTERN",
    "YFinanceFetcher",
]
