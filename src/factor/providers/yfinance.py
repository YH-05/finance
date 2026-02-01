"""YFinance data provider implementation.

This module provides the YFinanceProvider class for fetching financial data
from Yahoo Finance using the yfinance library.

Examples
--------
>>> from factor.providers.yfinance import YFinanceProvider
>>> provider = YFinanceProvider()
>>> df = provider.get_prices(
...     symbols=["AAPL", "GOOGL"],
...     start_date="2024-01-01",
...     end_date="2024-01-31",
... )
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from utils_core.logging import get_logger

from factor.errors import DataFetchError
from factor.providers.cache import Cache

logger = get_logger(__name__)

# Metric mapping from our API to yfinance info keys
METRIC_MAPPING: dict[str, str] = {
    "per": "trailingPE",
    "pbr": "priceToBook",
    "roe": "returnOnEquity",
    "roa": "returnOnAssets",
    "eps": "trailingEps",
    "dividend_yield": "dividendYield",
}

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds


class YFinanceProvider:
    """Yahoo Finance data provider.

    Fetches financial data from Yahoo Finance using the yfinance library.
    Supports caching with TTL-based invalidation and retry logic with
    exponential backoff.

    Parameters
    ----------
    cache_path : str | Path | None, default=None
        Directory path for cache storage. If None, caching is disabled.
    cache_ttl_hours : int, default=24
        Time To Live in hours for cache entries.
    max_retries : int, default=3
        Maximum number of retry attempts for failed requests.
    retry_base_delay : float, default=1.0
        Base delay in seconds for exponential backoff.

    Attributes
    ----------
    cache : Cache | None
        Cache instance if caching is enabled, None otherwise.
    max_retries : int
        Maximum retry attempts.
    retry_base_delay : float
        Base delay for exponential backoff.

    Examples
    --------
    >>> provider = YFinanceProvider()
    >>> df = provider.get_prices(["AAPL"], "2024-01-01", "2024-01-31")
    >>> df.columns.names
    ['symbol', 'price_type']

    >>> # With caching enabled
    >>> provider = YFinanceProvider(
    ...     cache_path="/tmp/yfinance_cache",
    ...     cache_ttl_hours=24,
    ... )
    """

    def __init__(
        self,
        cache_path: str | Path | None = None,
        cache_ttl_hours: int = 24,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    ) -> None:
        """Initialize YFinanceProvider.

        Parameters
        ----------
        cache_path : str | Path | None, default=None
            Directory path for cache storage. If None, caching is disabled.
        cache_ttl_hours : int, default=24
            Time To Live in hours for cache entries.
        max_retries : int, default=3
            Maximum number of retry attempts for failed requests.
        retry_base_delay : float, default=1.0
            Base delay in seconds for exponential backoff.
        """
        logger.debug(
            "Initializing YFinanceProvider",
            cache_path=str(cache_path) if cache_path else None,
            cache_ttl_hours=cache_ttl_hours,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )

        self.cache: Cache | None = None
        if cache_path is not None:
            self.cache = Cache(cache_path=cache_path, ttl_hours=cache_ttl_hours)

        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

        logger.info(
            "YFinanceProvider initialized",
            caching_enabled=self.cache is not None,
            max_retries=self.max_retries,
        )

    def _normalize_date(self, date: datetime | str) -> str:
        """Convert date to string format.

        Parameters
        ----------
        date : datetime | str
            Date as datetime object or ISO format string.

        Returns
        -------
        str
            Date in ISO format string (YYYY-MM-DD).
        """
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return date

    def _generate_cache_key(
        self,
        operation: str,
        symbols: list[str],
        start_date: str,
        end_date: str,
        extra: str = "",
    ) -> str:
        """Generate a cache key for the given parameters.

        Parameters
        ----------
        operation : str
            Type of operation (e.g., "prices", "volumes").
        symbols : list[str]
            List of ticker symbols.
        start_date : str
            Start date in ISO format.
        end_date : str
            End date in ISO format.
        extra : str, default=""
            Extra parameters for the cache key.

        Returns
        -------
        str
            Cache key string.
        """
        symbols_str = "_".join(sorted(symbols))
        key = f"{operation}_{symbols_str}_{start_date}_{end_date}"
        if extra:
            key += f"_{extra}"
        return key

    def _retry_with_backoff(
        self,
        func: Any,
        symbols: list[str],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry logic and exponential backoff.

        Parameters
        ----------
        func : callable
            Function to execute.
        symbols : list[str]
            Symbols being fetched (for error reporting).
        *args : Any
            Positional arguments for the function.
        **kwargs : Any
            Keyword arguments for the function.

        Returns
        -------
        Any
            Result from the function.

        Raises
        ------
        DataFetchError
            If all retry attempts fail.
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Executing request",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    function=func.__name__,
                )
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                wait_time = self.retry_base_delay * (2**attempt)

                logger.warning(
                    "Request failed, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                    wait_time_seconds=wait_time,
                )

                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)

        logger.error(
            "All retry attempts failed",
            symbols=symbols,
            max_retries=self.max_retries,
            last_error=str(last_exception),
        )

        raise DataFetchError(
            f"Failed to fetch data after {self.max_retries} attempts",
            symbols=symbols,
            cause=last_exception,
        )

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch OHLCV price data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
            Examples: ["AAPL", "GOOGL", "MSFT"]
        start_date : datetime | str
            Start date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, price_type)
            - price_type values: ["Open", "High", "Low", "Close", "Volume"]

        Raises
        ------
        ValueError
            If symbols list is empty.
        DataFetchError
            If data fetching fails or returns empty data.

        Examples
        --------
        >>> provider = YFinanceProvider()
        >>> df = provider.get_prices(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        >>> df.columns.names
        ['symbol', 'price_type']
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty")

        start_str = self._normalize_date(start_date)
        end_str = self._normalize_date(end_date)

        logger.debug(
            "Fetching price data",
            symbols=symbols,
            start_date=start_str,
            end_date=end_str,
        )

        # Check cache first
        cache_key = self._generate_cache_key("prices", symbols, start_str, end_str)
        if self.cache is not None:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(
                    "Cache hit for price data",
                    symbols=symbols,
                    cache_key=cache_key,
                )
                return cached_data

        # Fetch from yfinance
        def fetch_prices() -> pd.DataFrame:
            result = yf.download(
                tickers=symbols,
                start=start_str,
                end=end_str,
                group_by="ticker",
                progress=False,
            )
            if result is None:
                return pd.DataFrame()
            return result

        raw_data = self._retry_with_backoff(fetch_prices, symbols)

        # Check if data is empty
        if raw_data.empty:
            raise DataFetchError(
                f"No data returned for symbols: {symbols}",
                symbols=symbols,
            )

        # Ensure consistent MultiIndex structure
        result = self._normalize_price_dataframe(raw_data, symbols)

        # Save to cache
        if self.cache is not None:
            self.cache.set(cache_key, result)

        logger.info(
            "Price data fetched successfully",
            symbols=symbols,
            rows=len(result),
            columns=len(result.columns),
        )

        return result

    def _normalize_price_dataframe(
        self,
        df: pd.DataFrame,
        symbols: list[str],
    ) -> pd.DataFrame:
        """Normalize yfinance DataFrame to consistent MultiIndex format.

        Parameters
        ----------
        df : pd.DataFrame
            Raw DataFrame from yfinance.
        symbols : list[str]
            List of requested symbols.

        Returns
        -------
        pd.DataFrame
            Normalized DataFrame with (symbol, price_type) MultiIndex columns.
        """
        # For single ticker, yfinance returns flat columns
        if len(symbols) == 1 and not isinstance(df.columns, pd.MultiIndex):
            symbol = symbols[0]
            # Create MultiIndex columns
            new_columns = pd.MultiIndex.from_tuples(
                [(symbol, col) for col in df.columns],
                names=["symbol", "price_type"],
            )
            df.columns = new_columns
        else:
            # For multiple tickers, yfinance returns MultiIndex (ticker, price_type)
            # We need to ensure names are set correctly
            df.columns.names = ["symbol", "price_type"]

        # Ensure index name is "Date"
        df.index.name = "Date"

        return df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch volume data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
        start_date : datetime | str
            Start date for the data range.
        end_date : datetime | str
            End date for the data range.

        Returns
        -------
        pd.DataFrame
            DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names (e.g., ["AAPL", "GOOGL"])

        Raises
        ------
        ValueError
            If symbols list is empty.
        DataFetchError
            If data fetching fails.

        Examples
        --------
        >>> provider = YFinanceProvider()
        >>> df = provider.get_volumes(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        >>> list(df.columns)
        ['AAPL', 'GOOGL']
        """
        logger.debug(
            "Fetching volume data",
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Use get_prices and extract Volume column
        price_data = self.get_prices(symbols, start_date, end_date)

        # Extract Volume column for each symbol
        volume_data: dict[str, pd.Series] = {}
        for symbol in symbols:
            if (symbol, "Volume") in price_data.columns:
                col_data = price_data[(symbol, "Volume")]
                if isinstance(col_data, pd.Series):
                    volume_data[symbol] = col_data

        result = pd.DataFrame(volume_data)
        result.index.name = "Date"

        logger.info(
            "Volume data extracted successfully",
            symbols=symbols,
            rows=len(result),
        )

        return result

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch fundamental data for the specified symbols and metrics.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
        metrics : list[str]
            List of fundamental metrics to fetch.
            Supported: ["per", "pbr", "roe", "roa", "eps", "dividend_yield"]
        start_date : datetime | str
            Start date for the data range.
        end_date : datetime | str
            End date for the data range.

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, metric)

        Raises
        ------
        ValueError
            If symbols list is empty.
        DataFetchError
            If data fetching fails.

        Notes
        -----
        yfinance provides point-in-time fundamental data, so the same
        values are replicated across the date range.

        Examples
        --------
        >>> provider = YFinanceProvider()
        >>> df = provider.get_fundamentals(
        ...     symbols=["AAPL", "GOOGL"],
        ...     metrics=["per", "pbr", "roe"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty")

        start_str = self._normalize_date(start_date)
        end_str = self._normalize_date(end_date)
        metrics_str = "_".join(sorted(metrics))

        logger.debug(
            "Fetching fundamental data",
            symbols=symbols,
            metrics=metrics,
            start_date=start_str,
            end_date=end_str,
        )

        # Check cache first
        cache_key = self._generate_cache_key(
            "fundamentals", symbols, start_str, end_str, metrics_str
        )
        if self.cache is not None:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(
                    "Cache hit for fundamental data",
                    symbols=symbols,
                    cache_key=cache_key,
                )
                return cached_data

        # Fetch fundamental data for each symbol
        fundamentals: dict[tuple[str, str], list[float | None]] = {}

        for symbol in symbols:
            ticker_info = self._get_ticker_info(symbol)

            for metric in metrics:
                yf_key = METRIC_MAPPING.get(metric)
                if yf_key and ticker_info is not None:
                    value = ticker_info.get(yf_key)
                else:
                    value = None

                fundamentals[(symbol, metric)] = [value]

        # Create date range
        date_range = pd.date_range(start=start_str, end=end_str, freq="B")
        if len(date_range) == 0:
            date_range = pd.date_range(start=start_str, periods=1)

        # Create DataFrame with fundamental values replicated across dates
        data_dict: dict[tuple[str, str], list[float | None]] = {}
        for key, values in fundamentals.items():
            # Replicate single value across all dates
            data_dict[key] = [values[0]] * len(date_range)

        result = pd.DataFrame(data_dict, index=date_range)
        result.index.name = "Date"
        result.columns = pd.MultiIndex.from_tuples(
            result.columns, names=["symbol", "metric"]
        )

        # Save to cache
        if self.cache is not None:
            self.cache.set(cache_key, result)

        logger.info(
            "Fundamental data fetched successfully",
            symbols=symbols,
            metrics=metrics,
            rows=len(result),
        )

        return result

    def _get_ticker_info(self, symbol: str) -> dict[str, Any] | None:
        """Get ticker info from yfinance with retry logic.

        Parameters
        ----------
        symbol : str
            Ticker symbol.

        Returns
        -------
        dict[str, Any] | None
            Ticker info dictionary or None if failed.
        """
        try:

            def fetch_info() -> dict[str, Any]:
                ticker = yf.Ticker(symbol)
                return ticker.info

            return self._retry_with_backoff(fetch_info, [symbol])
        except DataFetchError:
            logger.warning(
                "Failed to fetch ticker info",
                symbol=symbol,
            )
            return None

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch market capitalization data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
        start_date : datetime | str
            Start date for the data range.
        end_date : datetime | str
            End date for the data range.

        Returns
        -------
        pd.DataFrame
            DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names (e.g., ["AAPL", "GOOGL"])

        Raises
        ------
        ValueError
            If symbols list is empty.
        DataFetchError
            If data fetching fails.

        Notes
        -----
        yfinance provides point-in-time market cap, so the same
        values are replicated across the date range.

        Examples
        --------
        >>> provider = YFinanceProvider()
        >>> df = provider.get_market_cap(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty")

        start_str = self._normalize_date(start_date)
        end_str = self._normalize_date(end_date)

        logger.debug(
            "Fetching market cap data",
            symbols=symbols,
            start_date=start_str,
            end_date=end_str,
        )

        # Check cache first
        cache_key = self._generate_cache_key("market_cap", symbols, start_str, end_str)
        if self.cache is not None:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(
                    "Cache hit for market cap data",
                    symbols=symbols,
                    cache_key=cache_key,
                )
                return cached_data

        # Fetch market cap for each symbol
        market_caps: dict[str, float | None] = {}

        for symbol in symbols:
            ticker_info = self._get_ticker_info(symbol)
            if ticker_info is not None:
                market_caps[symbol] = ticker_info.get("marketCap")
            else:
                market_caps[symbol] = None

        # Create date range
        date_range = pd.date_range(start=start_str, end=end_str, freq="B")
        if len(date_range) == 0:
            date_range = pd.date_range(start=start_str, periods=1)

        # Create DataFrame with market cap values replicated across dates
        data_dict: dict[str, list[float | None]] = {}
        for symbol, value in market_caps.items():
            data_dict[symbol] = [value] * len(date_range)

        result = pd.DataFrame(data_dict, index=date_range)
        result.index.name = "Date"

        # Save to cache
        if self.cache is not None:
            self.cache.set(cache_key, result)

        logger.info(
            "Market cap data fetched successfully",
            symbols=symbols,
            rows=len(result),
        )

        return result


__all__ = ["YFinanceProvider"]
