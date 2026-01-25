"""YFinance data fetcher for market data retrieval.

This module provides a concrete implementation for fetching market data
using the yfinance library to fetch data from Yahoo Finance.
"""

import re
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from finance.utils.logging_config import get_logger
from market.yfinance.errors import DataFetchError, ErrorCode, ValidationError
from market.yfinance.types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)

logger = get_logger(__name__, module="market.yfinance.fetcher")

# Valid yfinance symbol pattern
# Supports: AAPL, BRK.B, BRK-B, ^GSPC (indices), USDJPY=X (forex)
YFINANCE_SYMBOL_PATTERN = re.compile(r"^[\^]?[A-Z0-9.\-]+(=X)?$", re.IGNORECASE)

# Standard OHLCV column names
STANDARD_COLUMNS = ["open", "high", "low", "close", "volume"]


class YFinanceFetcher:
    """Data fetcher using Yahoo Finance (yfinance) API.

    Fetches OHLCV data for stocks, indices, forex, and other
    financial instruments supported by Yahoo Finance.

    Parameters
    ----------
    cache_config : CacheConfig | None
        Configuration for cache behavior.
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
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._cache_config = cache_config
        self._retry_config = retry_config

        logger.debug(
            "Initializing YFinanceFetcher",
            cache_enabled=cache_config is not None,
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

    @property
    def default_interval(self) -> Interval:
        """Return the default data interval.

        Returns
        -------
        Interval
            The default interval (DAILY by default)
        """
        return Interval.DAILY

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
        )

        return results

    def _validate_options(self, options: FetchOptions) -> None:
        """Validate fetch options before processing.

        Parameters
        ----------
        options : FetchOptions
            The options to validate

        Raises
        ------
        ValidationError
            If options are invalid
        """
        logger.debug(
            "Validating fetch options",
            symbol_count=len(options.symbols),
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
        )

        if not options.symbols:
            logger.error("No symbols provided")
            raise ValidationError(
                "At least one symbol must be provided",
                field="symbols",
                value=options.symbols,
                code=ErrorCode.INVALID_PARAMETER,
            )

        # Validate each symbol
        invalid_symbols = [s for s in options.symbols if not self.validate_symbol(s)]
        if invalid_symbols:
            logger.error(
                "Invalid symbols found",
                invalid_symbols=invalid_symbols,
                source=self.source.value,
            )
            raise ValidationError(
                f"Invalid symbols for {self.source.value}: {invalid_symbols}",
                field="symbols",
                value=invalid_symbols,
                code=ErrorCode.INVALID_SYMBOL,
            )

        logger.debug("Fetch options validated successfully")

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

        # Fetch from API
        data = self._fetch_from_api(symbol, options)

        return self._create_result(
            symbol=symbol,
            data=data,
            from_cache=False,
            metadata={
                "interval": options.interval.value,
                "source": "yfinance",
            },
        )

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
        normalized = self._normalize_dataframe(df, symbol)

        logger.debug(
            "Data fetched successfully",
            symbol=symbol,
            rows=len(normalized),
            date_range=f"{normalized.index.min()} to {normalized.index.max()}"
            if not normalized.empty
            else "empty",
        )

        return normalized

    def _normalize_dataframe(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """Normalize a DataFrame to standard OHLCV format.

        Parameters
        ----------
        df : pd.DataFrame
            The raw DataFrame to normalize
        symbol : str
            The symbol for logging purposes

        Returns
        -------
        pd.DataFrame
            Normalized DataFrame with standard column names
        """
        logger.debug(
            "Normalizing DataFrame",
            symbol=symbol,
            original_columns=list(df.columns),
            row_count=len(df),
        )

        if df.empty:
            logger.warning(
                "Empty DataFrame received",
                symbol=symbol,
            )
            return pd.DataFrame(columns=pd.Index(STANDARD_COLUMNS))

        # Create a copy to avoid modifying the original
        normalized = df.copy()

        # Normalize column names to lowercase
        normalized.columns = normalized.columns.str.lower()

        # Handle multi-level columns (common in yfinance)
        if isinstance(normalized.columns, pd.MultiIndex):
            logger.debug(
                "Flattening multi-level columns",
                symbol=symbol,
                levels=normalized.columns.nlevels,
            )
            normalized.columns = normalized.columns.get_level_values(0)

        # Map common column name variations
        column_mapping = {
            "adj close": "close",
            "adjusted close": "close",
            "adj_close": "close",
            "vol": "volume",
        }

        for old_name, new_name in column_mapping.items():
            if old_name in normalized.columns and new_name not in normalized.columns:
                normalized = normalized.rename(columns={old_name: new_name})
                logger.debug(
                    "Renamed column",
                    symbol=symbol,
                    old_name=old_name,
                    new_name=new_name,
                )

        # Ensure all standard columns exist
        for col in STANDARD_COLUMNS:
            if col not in normalized.columns:
                logger.debug(
                    "Adding missing column with NaN",
                    symbol=symbol,
                    column=col,
                )
                normalized[col] = pd.NA

        # Select only standard columns in order
        try:
            selected = normalized[STANDARD_COLUMNS]
            # When indexing with a list, pandas returns a DataFrame
            assert isinstance(selected, pd.DataFrame)  # nosec B101
            normalized = selected
        except KeyError as e:
            logger.error(
                "Failed to select standard columns",
                symbol=symbol,
                available_columns=list(df.columns),
                error=str(e),
            )
            raise DataFetchError(
                f"Failed to normalize DataFrame for {symbol}: missing required columns",
                symbol=symbol,
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
                cause=e,
            ) from e

        # Ensure index is DatetimeIndex
        if not isinstance(normalized.index, pd.DatetimeIndex):
            logger.debug(
                "Converting index to DatetimeIndex",
                symbol=symbol,
                original_type=type(normalized.index).__name__,
            )
            try:
                normalized.index = pd.to_datetime(normalized.index)
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Failed to convert index to DatetimeIndex",
                    symbol=symbol,
                    error=str(e),
                )

        # Sort by date
        normalized = normalized.sort_index()

        logger.debug(
            "DataFrame normalization completed",
            symbol=symbol,
            final_columns=list(normalized.columns),
            row_count=len(normalized),
            date_range=(
                f"{normalized.index.min()} to {normalized.index.max()}"
                if not normalized.empty
                else "empty"
            ),
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

    def _create_result(
        self,
        symbol: str,
        data: pd.DataFrame,
        from_cache: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> MarketDataResult:
        """Create a MarketDataResult from fetched data.

        Parameters
        ----------
        symbol : str
            The symbol that was fetched
        data : pd.DataFrame
            The fetched and normalized data
        from_cache : bool
            Whether data was retrieved from cache
        metadata : dict[str, Any] | None
            Additional metadata to include

        Returns
        -------
        MarketDataResult
            The result object
        """
        result = MarketDataResult(
            symbol=symbol,
            data=data,
            source=self.source,
            fetched_at=datetime.now(),
            from_cache=from_cache,
            metadata=metadata or {},
        )

        logger.debug(
            "Created MarketDataResult",
            symbol=symbol,
            row_count=result.row_count,
            from_cache=from_cache,
            source=self.source.value,
        )

        return result


__all__ = [
    "YFINANCE_SYMBOL_PATTERN",
    "YFinanceFetcher",
]
