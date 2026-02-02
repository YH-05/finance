"""YFinance data fetcher for market data retrieval.

This module provides a concrete implementation for fetching market data
using the yfinance library to fetch data from Yahoo Finance.

Uses curl_cffi to bypass Yahoo Finance rate limiting by impersonating
a real browser's TLS fingerprint.
"""

import random
import re
import time
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf
from curl_cffi import requests as curl_requests
from curl_cffi.requests import BrowserTypeLiteral

from market.errors import DataFetchError, ErrorCode, ValidationError
from market.yfinance.session import CurlCffiSession, HttpSessionProtocol
from market.yfinance.types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)
from utils_core.logging import get_logger

logger = get_logger(__name__, module="market.yfinance.fetcher")

# Browser impersonation targets for curl_cffi
# These mimic real browser TLS fingerprints to avoid rate limiting
BROWSER_IMPERSONATE_TARGETS: list[BrowserTypeLiteral] = [
    "chrome",
    "chrome110",
    "chrome120",
    "edge99",
    "safari15_3",
]

# Default retry configuration for API calls
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

# Valid yfinance symbol pattern
# Supports: AAPL, BRK.B, BRK-B, ^GSPC (indices), USDJPY=X (forex), GC=F (futures)
YFINANCE_SYMBOL_PATTERN = re.compile(r"^[\^]?[A-Z0-9.\-]+(=[XF])?$", re.IGNORECASE)

# Standard OHLCV column names
STANDARD_COLUMNS = ["open", "high", "low", "close", "volume"]


class YFinanceFetcher:
    """Data fetcher using Yahoo Finance (yfinance) API.

    Fetches OHLCV data for stocks, indices, forex, and other
    financial instruments supported by Yahoo Finance.

    Uses curl_cffi with browser impersonation to bypass Yahoo Finance
    rate limiting. Supports bulk downloading of multiple symbols
    via yf.download() for improved efficiency.

    Parameters
    ----------
    cache_config : CacheConfig | None
        Configuration for cache behavior.
    retry_config : RetryConfig | None
        Configuration for retry behavior on API errors.
    impersonate : BrowserTypeLiteral | None
        Browser to impersonate for TLS fingerprinting.
        Options: "chrome", "chrome110", "chrome120", "edge99", "safari15_3".
        If None, randomly selects from available options.
    http_session : HttpSessionProtocol | None
        HTTP session for making requests.
        If None, defaults to CurlCffiSession() with the specified impersonate.
        Use this parameter to inject custom session implementations for testing
        or to use alternative HTTP clients.

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

    With custom session injection:

    >>> from market.yfinance.session import StandardRequestsSession
    >>> custom_session = StandardRequestsSession()
    >>> fetcher = YFinanceFetcher(http_session=custom_session)
    """

    def __init__(
        self,
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
        impersonate: BrowserTypeLiteral | None = None,
        http_session: HttpSessionProtocol | None = None,
    ) -> None:
        self._cache_config = cache_config
        self._retry_config = retry_config or DEFAULT_RETRY_CONFIG
        self._impersonate: BrowserTypeLiteral = (
            impersonate
            if impersonate is not None
            else random.choice(BROWSER_IMPERSONATE_TARGETS)  # nosec B311
        )
        # Use injected session or create default CurlCffiSession
        self._http_session: HttpSessionProtocol | None = http_session
        self._owns_session: bool = http_session is None
        # Internally created session (when http_session is not provided)
        self._session: CurlCffiSession | None = None

        logger.debug(
            "Initializing YFinanceFetcher",
            cache_enabled=cache_config is not None,
            retry_enabled=retry_config is not None,
            impersonate=self._impersonate,
            session_injected=http_session is not None,
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

    def _get_session(self) -> HttpSessionProtocol:
        """Get or create an HTTP session.

        Returns an injected session if provided, otherwise creates a
        CurlCffiSession with browser impersonation.

        Returns
        -------
        HttpSessionProtocol
            HTTP session for making requests
        """
        if self._http_session is not None:
            return self._http_session

        # Create default CurlCffiSession if not injected
        if self._session is None:
            self._session = CurlCffiSession(impersonate=self._impersonate)
            logger.debug(
                "Created CurlCffiSession",
                impersonate=self._impersonate,
            )
        return self._session

    def _rotate_session(self) -> None:
        """Rotate to a new browser impersonation to avoid detection.

        Only rotates sessions that are owned by this fetcher (not injected).
        Injected sessions are managed externally and should not be rotated.
        """
        # Do not rotate injected sessions
        if self._http_session is not None:
            logger.debug(
                "Skipping session rotation for injected session",
            )
            return

        if self._session is not None:
            self._session.close()
            self._session = None

        new_target: BrowserTypeLiteral = random.choice(BROWSER_IMPERSONATE_TARGETS)  # nosec B311
        self._impersonate = new_target
        logger.debug(
            "Rotated browser impersonation",
            new_impersonate=self._impersonate,
        )

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
        >>> fetcher.validate_symbol("GC=F")
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

        Uses yf.download() for efficient bulk downloading of multiple symbols.
        Implements retry logic with exponential backoff and browser rotation
        to handle rate limiting.

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
            "Fetching market data via yf.download",
            symbols=options.symbols,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
            interval=options.interval.value,
            symbol_count=len(options.symbols),
        )

        # Use bulk download for multiple symbols
        bulk_data = self._fetch_bulk(options)

        # Convert bulk data to individual results
        results = self._create_results_from_bulk(bulk_data, options)

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

    def _fetch_bulk(
        self,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Fetch data for multiple symbols using yf.download.

        Implements retry logic with exponential backoff and browser
        fingerprint rotation to handle Yahoo Finance rate limiting.

        Parameters
        ----------
        options : FetchOptions
            Fetch options including symbols and date range

        Returns
        -------
        pd.DataFrame
            DataFrame with MultiIndex columns (symbol, OHLCV)
            or single-level columns if only one symbol

        Raises
        ------
        DataFetchError
            If all retry attempts fail
        """
        retry_config = self._retry_config or DEFAULT_RETRY_CONFIG
        last_error: Exception | None = None

        for attempt in range(retry_config.max_attempts):
            try:
                return self._do_bulk_fetch(options)

            except Exception as e:
                last_error = e
                logger.warning(
                    "Bulk fetch attempt failed",
                    attempt=attempt + 1,
                    max_attempts=retry_config.max_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                if attempt < retry_config.max_attempts - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        retry_config.initial_delay
                        * (retry_config.exponential_base**attempt),
                        retry_config.max_delay,
                    )

                    # Add jitter if configured
                    if retry_config.jitter:
                        delay *= 0.5 + random.random()  # nosec B311

                    logger.debug(
                        "Waiting before retry",
                        delay_seconds=delay,
                        next_attempt=attempt + 2,
                    )
                    time.sleep(delay)

                    # Rotate browser fingerprint on retry
                    self._rotate_session()

        raise DataFetchError(
            f"Failed to fetch data after {retry_config.max_attempts} attempts",
            symbol=",".join(options.symbols),
            source=self.source.value,
            code=ErrorCode.API_ERROR,
            cause=last_error,
        )

    def _do_bulk_fetch(
        self,
        options: FetchOptions,
    ) -> pd.DataFrame:
        """Execute the actual yf.download call.

        Parameters
        ----------
        options : FetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Raw data from yf.download
        """
        session = self._get_session()

        start = self._format_date(options.start_date)
        end = self._format_date(options.end_date)
        interval = self._map_interval(options.interval)

        logger.debug(
            "Calling yf.download",
            symbols=options.symbols,
            start=start,
            end=end,
            interval=interval,
            impersonate=self._impersonate,
        )

        # Use yf.download for bulk fetching
        result = yf.download(
            tickers=options.symbols,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            actions=False,
            progress=False,
            session=session,
            threads=True,  # Enable multi-threading for faster downloads
        )

        # Handle None return (shouldn't happen but be defensive)
        if result is None:
            logger.warning("yf.download returned None")
            return pd.DataFrame(columns=pd.Index(STANDARD_COLUMNS))

        df: pd.DataFrame = result

        logger.debug(
            "yf.download completed",
            shape=df.shape if not df.empty else (0, 0),
            columns=list(df.columns)[:10] if not df.empty else [],
        )

        return df

    def _create_results_from_bulk(
        self,
        bulk_data: pd.DataFrame,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Convert bulk download data to individual MarketDataResult objects.

        Parameters
        ----------
        bulk_data : pd.DataFrame
            DataFrame from yf.download (may have MultiIndex columns)
        options : FetchOptions
            Original fetch options

        Returns
        -------
        list[MarketDataResult]
            List of results, one per symbol
        """
        results: list[MarketDataResult] = []

        # yfinance 1.0+ always returns MultiIndex columns: (metric, symbol)
        # Handle each symbol by extracting its data
        for symbol in options.symbols:
            try:
                if bulk_data.empty:
                    symbol_data = pd.DataFrame(columns=pd.Index(STANDARD_COLUMNS))
                elif isinstance(bulk_data.columns, pd.MultiIndex):
                    # Extract data for this symbol from MultiIndex DataFrame
                    # yf.download returns columns like ('Close', 'AAPL')
                    try:
                        symbol_data = bulk_data.xs(symbol, axis=1, level=1)
                    except KeyError:
                        # Symbol might be in level 0 for single-symbol case
                        # Or not present at all
                        logger.warning(
                            "Symbol not found in MultiIndex, using full data",
                            symbol=symbol,
                        )
                        symbol_data = bulk_data
                else:
                    # Non-MultiIndex (older yfinance or single symbol)
                    symbol_data = bulk_data

                normalized = self._normalize_dataframe(symbol_data, symbol)

                results.append(
                    self._create_result(
                        symbol=symbol,
                        data=normalized,
                        from_cache=False,
                        metadata={
                            "interval": options.interval.value,
                            "source": "yfinance",
                            "bulk_download": True,
                        },
                    )
                )

            except Exception as e:
                logger.warning(
                    "Failed to extract symbol data",
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                results.append(
                    self._create_result(
                        symbol=symbol,
                        data=pd.DataFrame(columns=pd.Index(STANDARD_COLUMNS)),
                        from_cache=False,
                        metadata={
                            "interval": options.interval.value,
                            "source": "yfinance",
                            "bulk_download": True,
                            "error": f"Failed to extract: {e}",
                        },
                    )
                )

        return results

    def _fetch_single(
        self,
        symbol: str,
        options: FetchOptions,
    ) -> MarketDataResult:
        """Fetch data for a single symbol (fallback method).

        This method is kept for backward compatibility and can be used
        when bulk download fails for specific symbols.

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
        logger.debug("Fetching single symbol (fallback)", symbol=symbol)

        # Fetch from API using Ticker with curl_cffi session
        data = self._fetch_from_api(symbol, options)

        return self._create_result(
            symbol=symbol,
            data=data,
            from_cache=False,
            metadata={
                "interval": options.interval.value,
                "source": "yfinance",
                "bulk_download": False,
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
        """Execute the actual yfinance fetch for a single symbol.

        Uses curl_cffi session for the Ticker to bypass rate limiting.

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
        session = self._get_session()
        ticker = yf.Ticker(symbol, session=session)

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

        # Handle multi-level columns first (common in yfinance 1.0+)
        if isinstance(normalized.columns, pd.MultiIndex):
            logger.debug(
                "Flattening multi-level columns",
                symbol=symbol,
                levels=normalized.columns.nlevels,
            )
            # Get the first level (OHLCV names) and lowercase them
            normalized.columns = pd.Index(
                [
                    col[0].lower() if isinstance(col, tuple) else str(col).lower()
                    for col in normalized.columns
                ]
            )
        else:
            # Normalize column names to lowercase
            normalized.columns = normalized.columns.str.lower()

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

    def close(self) -> None:
        """Close the HTTP session and release resources.

        Should be called when the fetcher is no longer needed.
        Closes both injected sessions and internally created sessions.
        """
        # Close injected session
        if self._http_session is not None:
            self._http_session.close()
            self._http_session = None
            logger.debug("Closed injected HTTP session")

        # Close internally created session
        if self._session is not None:
            self._session.close()
            self._session = None
            logger.debug("Closed CurlCffiSession")

    def __enter__(self) -> "YFinanceFetcher":
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close session on context exit."""
        self.close()


__all__ = [
    "BROWSER_IMPERSONATE_TARGETS",
    "DEFAULT_RETRY_CONFIG",
    "YFINANCE_SYMBOL_PATTERN",
    "YFinanceFetcher",
]
