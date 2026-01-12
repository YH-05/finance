"""FRED data fetcher for economic indicator data retrieval.

This module provides a concrete implementation of BaseDataFetcher
using the fredapi library to fetch economic data from the Federal
Reserve Economic Data (FRED) service.
"""

import os
import re
from datetime import datetime

import pandas as pd
from fredapi import Fred

from ..errors import DataFetchError, ErrorCode, ValidationError
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

logger = get_logger(__name__, module="fred_fetcher")

# Environment variable name for FRED API key
FRED_API_KEY_ENV = "FRED_API_KEY"

# Valid FRED series ID pattern (uppercase letters, numbers, underscores)
FRED_SERIES_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class FREDFetcher(BaseDataFetcher):
    """Data fetcher using Federal Reserve Economic Data (FRED) API.

    Fetches economic indicator data such as interest rates, GDP,
    inflation rates, and other macroeconomic data from FRED.

    Parameters
    ----------
    api_key : str | None
        FRED API key. If None, reads from FRED_API_KEY environment variable.
    cache : SQLiteCache | None
        Cache instance for storing fetched data.
        If None, caching is disabled.
    cache_config : CacheConfig | None
        Configuration for cache behavior.
    retry_config : RetryConfig | None
        Configuration for retry behavior on API errors.

    Attributes
    ----------
    source : DataSource
        Always returns DataSource.FRED

    Raises
    ------
    ValidationError
        If API key is not provided and not found in environment variables.

    Examples
    --------
    >>> fetcher = FREDFetcher()  # Uses FRED_API_KEY env var
    >>> options = FetchOptions(
    ...     symbols=["GDP", "CPIAUCSL"],
    ...     start_date="2020-01-01",
    ...     end_date="2024-12-31",
    ... )
    >>> results = fetcher.fetch(options)
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache: SQLiteCache | None = None,
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get(FRED_API_KEY_ENV)
        self._cache = cache
        self._cache_config = cache_config
        self._retry_config = retry_config
        self._fred: Fred | None = None

        logger.debug(
            "Initializing FREDFetcher",
            api_key_source="parameter" if api_key else "environment",
            cache_enabled=cache is not None,
        )

        if not self._api_key:
            logger.error(
                "FRED API key not found",
                env_var=FRED_API_KEY_ENV,
            )
            raise ValidationError(
                f"FRED API key not provided. Set {FRED_API_KEY_ENV} environment "
                "variable or pass api_key parameter.",
                field="api_key",
                code=ErrorCode.INVALID_PARAMETER,
            )

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.FRED
        """
        return DataSource.FRED

    @property
    def default_interval(self) -> Interval:
        """Return the default data interval.

        FRED data is typically monthly or quarterly, but we return
        MONTHLY as the most common interval.

        Returns
        -------
        Interval
            Interval.MONTHLY
        """
        return Interval.MONTHLY

    def _get_fred_client(self) -> Fred:
        """Get or create the FRED API client.

        Returns
        -------
        Fred
            The FRED API client instance
        """
        if self._fred is None:
            self._fred = Fred(api_key=self._api_key)
            logger.debug("FRED client initialized")
        return self._fred

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol (series ID) is valid for FRED.

        FRED series IDs are uppercase alphanumeric strings that
        may contain underscores, starting with a letter.

        Parameters
        ----------
        symbol : str
            The series ID to validate

        Returns
        -------
        bool
            True if the series ID matches FRED format

        Examples
        --------
        >>> fetcher.validate_symbol("GDP")
        True
        >>> fetcher.validate_symbol("CPIAUCSL")
        True
        >>> fetcher.validate_symbol("DGS10")
        True
        >>> fetcher.validate_symbol("")
        False
        >>> fetcher.validate_symbol("invalid")
        False
        """
        if not symbol or not symbol.strip():
            return False

        return bool(FRED_SERIES_PATTERN.match(symbol.strip()))

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch economic data for the given options.

        Note: For FRED data, the symbols are interpreted as FRED series IDs.

        Parameters
        ----------
        options : FetchOptions
            Options specifying series IDs, date range, and other parameters.
            The `symbols` field should contain FRED series IDs.

        Returns
        -------
        list[MarketDataResult]
            List of results for each requested series

        Raises
        ------
        DataFetchError
            If fetching fails for any series
        ValidationError
            If options contain invalid parameters

        Examples
        --------
        >>> options = FetchOptions(symbols=["GDP"])
        >>> results = fetcher.fetch(options)
        >>> results[0].symbol
        'GDP'
        """
        self._validate_options(options)

        logger.info(
            "Fetching FRED data",
            series_ids=options.symbols,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
        )

        results: list[MarketDataResult] = []

        for series_id in options.symbols:
            result = self._fetch_single(series_id, options)
            results.append(result)

        logger.info(
            "FRED fetch completed",
            total_series=len(options.symbols),
            successful=len([r for r in results if not r.is_empty]),
            from_cache=len([r for r in results if r.from_cache]),
        )

        return results

    def _fetch_single(
        self,
        series_id: str,
        options: FetchOptions,
    ) -> MarketDataResult:
        """Fetch data for a single FRED series.

        Parameters
        ----------
        series_id : str
            The FRED series ID
        options : FetchOptions
            Fetch options

        Returns
        -------
        MarketDataResult
            The fetch result
        """
        logger.debug("Fetching single series", series_id=series_id)

        # Check cache first
        if self._cache is not None and options.use_cache:
            cached = self._get_from_cache(series_id, options)
            if cached is not None:
                return cached

        # Fetch from API
        data = self._fetch_from_api(series_id, options)

        # Cache the result
        if self._cache is not None and options.use_cache and not data.empty:
            self._save_to_cache(series_id, options, data)

        return self._create_result(
            symbol=series_id,
            data=data,
            from_cache=False,
            metadata={
                "source": "fred",
                "series_id": series_id,
            },
        )

    def _get_from_cache(
        self,
        series_id: str,
        options: FetchOptions,
    ) -> MarketDataResult | None:
        """Try to get data from cache.

        Parameters
        ----------
        series_id : str
            The series ID to look up
        options : FetchOptions
            Fetch options for cache key

        Returns
        -------
        MarketDataResult | None
            Cached result if found, None otherwise
        """
        cache_key = generate_cache_key(
            symbol=series_id,
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
            source=self.source.value,
        )

        assert self._cache is not None
        cached_data = self._cache.get(cache_key)

        if cached_data is not None and isinstance(cached_data, pd.DataFrame):
            logger.debug("Cache hit", series_id=series_id)
            return self._create_result(
                symbol=series_id,
                data=cached_data,
                from_cache=True,
                metadata={
                    "source": "cache",
                    "series_id": series_id,
                },
            )

        return None

    def _save_to_cache(
        self,
        series_id: str,
        options: FetchOptions,
        data: pd.DataFrame,
    ) -> None:
        """Save data to cache.

        Parameters
        ----------
        series_id : str
            The series ID
        options : FetchOptions
            Fetch options for cache key
        data : pd.DataFrame
            Data to cache
        """
        cache_key = generate_cache_key(
            symbol=series_id,
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
            source=self.source.value,
        )

        ttl = self._cache_config.ttl_seconds if self._cache_config else None

        assert self._cache is not None
        self._cache.set(
            cache_key,
            data,
            ttl=ttl,
            metadata={
                "series_id": series_id,
            },
        )

        logger.debug("Data cached", series_id=series_id)

    def _fetch_from_api(
        self,
        series_id: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Fetch data from FRED API.

        Parameters
        ----------
        series_id : str
            The series ID to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Data with 'value' column

        Raises
        ------
        DataFetchError
            If the API call fails
        """
        logger.debug("Fetching from FRED API", series_id=series_id)

        try:
            if self._retry_config:
                return self._fetch_with_retry(series_id, options)
            else:
                return self._do_fetch(series_id, options)

        except DataFetchError:
            raise
        except Exception as e:
            logger.error(
                "FRED API fetch failed",
                series_id=series_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataFetchError(
                f"Failed to fetch FRED series {series_id}: {e}",
                symbol=series_id,
                source=self.source.value,
                code=ErrorCode.API_ERROR,
                cause=e,
            ) from e

    def _fetch_with_retry(
        self,
        series_id: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Fetch with retry decorator applied.

        Parameters
        ----------
        series_id : str
            The series ID to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Fetched data
        """

        @with_retry(config=self._retry_config)
        def fetch_inner() -> pd.DataFrame:
            return self._do_fetch(series_id, options)

        return fetch_inner()

    def _do_fetch(
        self,
        series_id: str,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Execute the actual FRED API fetch.

        Parameters
        ----------
        series_id : str
            The series ID to fetch
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Data with 'value' column (normalized to OHLCV-like format)

        Raises
        ------
        DataFetchError
            If the series ID is invalid or no data is returned
        """
        fred = self._get_fred_client()

        # Format dates
        start = self._format_date(options.start_date)
        end = self._format_date(options.end_date)

        logger.debug(
            "Calling FRED API",
            series_id=series_id,
            start=start,
            end=end,
        )

        try:
            # Get series data
            series = fred.get_series(
                series_id,
                observation_start=start,
                observation_end=end,
            )

            if series is None or series.empty:
                logger.warning("No data returned for series", series_id=series_id)
                raise DataFetchError(
                    f"No data found for FRED series: {series_id}",
                    symbol=series_id,
                    source=self.source.value,
                    code=ErrorCode.DATA_NOT_FOUND,
                )

            # Convert Series to DataFrame with OHLCV-like columns
            # For economic data, we use the value for all OHLC columns
            df = pd.DataFrame(
                {
                    "open": series,
                    "high": series,
                    "low": series,
                    "close": series,
                    "volume": pd.NA,
                },
                index=series.index,
            )

            # Ensure index is DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            df = df.sort_index()

            logger.debug(
                "Data fetched successfully",
                series_id=series_id,
                rows=len(df),
                date_range=f"{df.index.min()} to {df.index.max()}"
                if not df.empty
                else "empty",
            )

            return df

        except DataFetchError:
            raise
        except ValueError as e:
            # fredapi raises ValueError for invalid series IDs
            logger.error(
                "Invalid FRED series ID",
                series_id=series_id,
                error=str(e),
            )
            raise DataFetchError(
                f"Invalid FRED series ID: {series_id}",
                symbol=series_id,
                source=self.source.value,
                code=ErrorCode.INVALID_SYMBOL,
                cause=e,
            ) from e

    def _format_date(
        self,
        date: datetime | str | None,
    ) -> str | None:
        """Format a date for FRED API.

        Parameters
        ----------
        date : datetime | str | None
            Date to format

        Returns
        -------
        str | None
            Formatted date string (YYYY-MM-DD) or None
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)

    def get_series_info(self, series_id: str) -> dict:
        """Get metadata about a FRED series.

        Parameters
        ----------
        series_id : str
            The FRED series ID

        Returns
        -------
        dict
            Series metadata including title, units, frequency, etc.

        Examples
        --------
        >>> info = fetcher.get_series_info("GDP")
        >>> info['title']
        'Gross Domestic Product'
        """
        fred = self._get_fred_client()

        try:
            info = fred.get_series_info(series_id)
            return info.to_dict() if hasattr(info, "to_dict") else dict(info)
        except Exception as e:
            logger.error(
                "Failed to get series info",
                series_id=series_id,
                error=str(e),
            )
            raise DataFetchError(
                f"Failed to get info for series {series_id}: {e}",
                symbol=series_id,
                source=self.source.value,
                code=ErrorCode.API_ERROR,
                cause=e,
            ) from e


__all__ = [
    "FREDFetcher",
    "FRED_API_KEY_ENV",
    "FRED_SERIES_PATTERN",
]
