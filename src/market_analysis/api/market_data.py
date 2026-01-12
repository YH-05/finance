"""MarketData API for unified market data retrieval.

This module provides a unified interface for fetching market data from
various sources including Yahoo Finance and FRED.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from ..core import DataFetcherFactory
from ..errors import DataFetchError, ErrorCode, ExportError, ValidationError
from ..types import (
    AgentOutputMetadata,
    CacheConfig,
    DataSource,
    FetchOptions,
    RetryConfig,
)
from ..utils.cache import SQLiteCache
from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="market_data_api")

# Default date range (1 year)
DEFAULT_LOOKBACK_DAYS = 365


class MarketData:
    """Unified interface for market data retrieval.

    Provides methods to fetch stock prices, forex rates, economic indicators,
    and commodity prices from various data sources.

    Parameters
    ----------
    cache_path : str | None
        Path to SQLite cache file. If None, caching is disabled.
    fred_api_key : str | None
        FRED API key. If None, reads from FRED_API_KEY environment variable.
    retry_config : RetryConfig | None
        Configuration for retry behavior on API errors.
    cache_config : CacheConfig | None
        Configuration for cache behavior.

    Examples
    --------
    >>> data = MarketData()
    >>> stock_df = data.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")
    >>> fx_df = data.fetch_forex("USDJPY", start="2024-01-01")
    >>> econ_df = data.fetch_fred("DGS10")
    >>> commodity_df = data.fetch_commodity("GC=F")
    """

    def __init__(
        self,
        cache_path: str | None = None,
        fred_api_key: str | None = None,
        retry_config: RetryConfig | None = None,
        cache_config: CacheConfig | None = None,
    ) -> None:
        """Initialize the MarketData interface.

        Parameters
        ----------
        cache_path : str | None
            Path to SQLite cache file.
        fred_api_key : str | None
            FRED API key. If None, reads from environment variable.
        retry_config : RetryConfig | None
            Retry configuration for API calls.
        cache_config : CacheConfig | None
            Cache configuration.
        """
        logger.debug(
            "Initializing MarketData",
            cache_enabled=cache_path is not None,
            retry_enabled=retry_config is not None,
        )

        self._cache: SQLiteCache | None = None
        self._cache_config = cache_config
        self._retry_config = retry_config
        self._fred_api_key = fred_api_key

        if cache_path is not None:
            # Create CacheConfig from cache_path if not provided
            effective_config = cache_config or CacheConfig(
                enabled=True,
                ttl_seconds=3600,
                max_entries=1000,
                db_path=cache_path,
            )
            self._cache = SQLiteCache(effective_config)
            self._cache_config = effective_config
            logger.debug("Cache initialized", cache_path=cache_path)

        logger.info("MarketData initialized")

    def _parse_date(
        self,
        date: datetime | str | None,
        default_offset_days: int | None = None,
    ) -> datetime | None:
        """Parse date input to datetime.

        Parameters
        ----------
        date : datetime | str | None
            Date to parse
        default_offset_days : int | None
            Days to offset from today if date is None

        Returns
        -------
        datetime | None
            Parsed datetime or None
        """
        if date is None:
            if default_offset_days is not None:
                from datetime import timedelta

                return datetime.now() - timedelta(days=default_offset_days)
            return None

        if isinstance(date, datetime):
            return date

        # At this point, date must be str
        try:
            return datetime.fromisoformat(date)
        except ValueError:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date, fmt)
                except ValueError:
                    continue

            logger.error("Invalid date format", date=date)
            raise ValidationError(
                f"Invalid date format: '{date}'. Use YYYY-MM-DD format.",
                field="date",
                value=str(date),
                code=ErrorCode.INVALID_PARAMETER,
            ) from None

    def _validate_symbol(
        self,
        symbol: str,
        field_name: str = "symbol",
        *,
        uppercase: bool = True,
    ) -> str:
        """Validate and normalize symbol.

        Parameters
        ----------
        symbol : str
            Symbol to validate
        field_name : str
            Field name for error messages
        uppercase : bool, default=True
            Whether to convert symbol to uppercase.
            Set to False for symbols with special suffixes (e.g., "GC=F").

        Returns
        -------
        str
            Validated symbol

        Raises
        ------
        ValidationError
            If symbol is invalid
        """
        if not symbol or not symbol.strip():
            logger.error("Empty symbol provided", field=field_name)
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name,
                value=str(symbol),
                code=ErrorCode.INVALID_PARAMETER,
            )

        cleaned = symbol.strip()
        return cleaned.upper() if uppercase else cleaned

    def fetch_stock(
        self,
        symbol: str,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
    ) -> pd.DataFrame:
        """Fetch stock price data.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g., "AAPL", "7203.T" for Japanese stocks)
        start : datetime | str | None
            Start date (default: 1 year ago)
        end : datetime | str | None
            End date (default: today)

        Returns
        -------
        pd.DataFrame
            OHLCV data with columns: open, high, low, close, volume

        Raises
        ------
        DataFetchError
            If data fetching fails
        ValidationError
            If parameters are invalid

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")
        >>> df.columns.tolist()
        ['open', 'high', 'low', 'close', 'volume']
        """
        symbol = self._validate_symbol(symbol)
        start_date = self._parse_date(start, default_offset_days=DEFAULT_LOOKBACK_DAYS)
        end_date = self._parse_date(end) or datetime.now()

        logger.info(
            "Fetching stock data",
            symbol=symbol,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher = DataFetcherFactory.create(
            "yfinance",
            cache=self._cache,
            cache_config=self._cache_config,
            retry_config=self._retry_config,
        )

        options = FetchOptions(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        if not results or results[0].is_empty:
            logger.error("No data returned for symbol", symbol=symbol)
            raise DataFetchError(
                f"No data found for symbol: {symbol}",
                symbol=symbol,
                source=DataSource.YFINANCE.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        logger.info(
            "Stock data fetched",
            symbol=symbol,
            rows=results[0].row_count,
            from_cache=results[0].from_cache,
        )

        return results[0].data

    def fetch_forex(
        self,
        pair: str,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
    ) -> pd.DataFrame:
        """Fetch forex rate data.

        Parameters
        ----------
        pair : str
            Currency pair (e.g., "USDJPY", "EURUSD")
        start : datetime | str | None
            Start date (default: 1 year ago)
        end : datetime | str | None
            End date (default: today)

        Returns
        -------
        pd.DataFrame
            Forex rate data with OHLCV columns

        Raises
        ------
        DataFetchError
            If data fetching fails
        ValidationError
            If parameters are invalid

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_forex("USDJPY", start="2024-01-01")
        >>> len(df) > 0
        True
        """
        pair = self._validate_symbol(pair, "pair")

        # Convert pair to yfinance format (e.g., USDJPY -> USDJPY=X)
        if not pair.endswith("=X"):
            symbol = f"{pair}=X"
        else:
            symbol = pair

        start_date = self._parse_date(start, default_offset_days=DEFAULT_LOOKBACK_DAYS)
        end_date = self._parse_date(end) or datetime.now()

        logger.info(
            "Fetching forex data",
            pair=pair,
            symbol=symbol,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher = DataFetcherFactory.create(
            "yfinance",
            cache=self._cache,
            cache_config=self._cache_config,
            retry_config=self._retry_config,
        )

        options = FetchOptions(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        if not results or results[0].is_empty:
            logger.error("No data returned for pair", pair=pair, symbol=symbol)
            raise DataFetchError(
                f"No data found for forex pair: {pair}",
                symbol=symbol,
                source=DataSource.YFINANCE.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        logger.info(
            "Forex data fetched",
            pair=pair,
            rows=results[0].row_count,
            from_cache=results[0].from_cache,
        )

        return results[0].data

    def fetch_fred(
        self,
        series_id: str,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
    ) -> pd.DataFrame:
        """Fetch FRED economic indicator data.

        Parameters
        ----------
        series_id : str
            FRED series ID (e.g., "DGS10", "GDP", "CPIAUCSL")
        start : datetime | str | None
            Start date (default: 1 year ago)
        end : datetime | str | None
            End date (default: today)

        Returns
        -------
        pd.DataFrame
            Economic indicator data

        Raises
        ------
        DataFetchError
            If data fetching fails
        ValidationError
            If parameters are invalid or FRED API key is not set

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_fred("DGS10", start="2024-01-01")
        >>> "close" in df.columns  # FRED data is normalized to OHLCV format
        True
        """
        series_id = self._validate_symbol(series_id, "series_id")
        start_date = self._parse_date(start, default_offset_days=DEFAULT_LOOKBACK_DAYS)
        end_date = self._parse_date(end) or datetime.now()

        logger.info(
            "Fetching FRED data",
            series_id=series_id,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher_kwargs: dict[str, Any] = {
            "cache": self._cache,
            "cache_config": self._cache_config,
            "retry_config": self._retry_config,
        }

        if self._fred_api_key:
            fetcher_kwargs["api_key"] = self._fred_api_key

        fetcher = DataFetcherFactory.create("fred", **fetcher_kwargs)

        options = FetchOptions(
            symbols=[series_id],
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        if not results or results[0].is_empty:
            logger.error("No data returned for series", series_id=series_id)
            raise DataFetchError(
                f"No data found for FRED series: {series_id}",
                symbol=series_id,
                source=DataSource.FRED.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        logger.info(
            "FRED data fetched",
            series_id=series_id,
            rows=results[0].row_count,
            from_cache=results[0].from_cache,
        )

        return results[0].data

    def fetch_commodity(
        self,
        symbol: str,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
    ) -> pd.DataFrame:
        """Fetch commodity price data.

        Parameters
        ----------
        symbol : str
            Commodity symbol (e.g., "GC=F" for gold, "CL=F" for crude oil)
        start : datetime | str | None
            Start date (default: 1 year ago)
        end : datetime | str | None
            End date (default: today)

        Returns
        -------
        pd.DataFrame
            Commodity price data with OHLCV columns

        Raises
        ------
        DataFetchError
            If data fetching fails
        ValidationError
            If parameters are invalid

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_commodity("GC=F", start="2024-01-01")  # Gold
        >>> df.columns.tolist()
        ['open', 'high', 'low', 'close', 'volume']
        """
        # For commodities, we pass the symbol as-is since they often have
        # special suffixes like =F for futures
        symbol_clean = self._validate_symbol(symbol, uppercase=False)

        start_date = self._parse_date(start, default_offset_days=DEFAULT_LOOKBACK_DAYS)
        end_date = self._parse_date(end) or datetime.now()

        logger.info(
            "Fetching commodity data",
            symbol=symbol_clean,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher = DataFetcherFactory.create(
            "yfinance",
            cache=self._cache,
            cache_config=self._cache_config,
            retry_config=self._retry_config,
        )

        options = FetchOptions(
            symbols=[symbol_clean],
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        if not results or results[0].is_empty:
            logger.error("No data returned for commodity", symbol=symbol_clean)
            raise DataFetchError(
                f"No data found for commodity: {symbol_clean}",
                symbol=symbol_clean,
                source=DataSource.YFINANCE.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        logger.info(
            "Commodity data fetched",
            symbol=symbol_clean,
            rows=results[0].row_count,
            from_cache=results[0].from_cache,
        )

        return results[0].data

    def save_to_sqlite(
        self,
        db_path: str,
        data: pd.DataFrame,
        table_name: str,
    ) -> None:
        """Save DataFrame to SQLite database.

        Parameters
        ----------
        db_path : str
            Path to SQLite database file
        data : pd.DataFrame
            Data to save
        table_name : str
            Name of the table

        Raises
        ------
        ExportError
            If saving fails

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_stock("AAPL")
        >>> data.save_to_sqlite("market.db", df, table_name="aapl")
        """
        import sqlite3

        logger.info(
            "Saving to SQLite",
            db_path=db_path,
            table_name=table_name,
            rows=len(data),
        )

        try:
            with sqlite3.connect(db_path) as conn:
                data.to_sql(table_name, conn, if_exists="replace", index=True)
                logger.info(
                    "Data saved to SQLite",
                    db_path=db_path,
                    table_name=table_name,
                )
        except Exception as e:
            logger.error(
                "Failed to save to SQLite",
                db_path=db_path,
                table_name=table_name,
                error=str(e),
            )
            raise ExportError(
                f"Failed to save data to SQLite: {e}",
                code=ErrorCode.IO_ERROR,
            ) from e

    def to_agent_json(
        self,
        data: pd.DataFrame,
        symbol: str = "",
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Convert DataFrame to AI agent-friendly JSON format.

        Parameters
        ----------
        data : pd.DataFrame
            Data to convert
        symbol : str
            Symbol identifier
        include_metadata : bool
            Whether to include metadata

        Returns
        -------
        dict[str, Any]
            Structured JSON-serializable dictionary

        Examples
        --------
        >>> data = MarketData()
        >>> df = data.fetch_stock("AAPL")
        >>> json_output = data.to_agent_json(df, symbol="AAPL")
        >>> json_output["success"]
        True
        """
        logger.debug(
            "Converting to agent JSON",
            symbol=symbol,
            rows=len(data),
            include_metadata=include_metadata,
        )

        try:
            # Convert DataFrame to list of dicts
            data_copy = data.copy()
            if hasattr(data_copy.index, "strftime"):
                data_copy = data_copy.reset_index()
                if "index" in data_copy.columns:
                    data_copy = data_copy.rename(columns={"index": "date"})
                else:
                    first_col = str(data_copy.columns[0])
                    if first_col not in ["date", "Date"]:
                        data_copy = data_copy.rename(columns={first_col: "date"})

            # Convert to records
            records = data_copy.to_dict(orient="records")

            # Convert dates to ISO format strings
            for record in records:
                for key, value in record.items():
                    if isinstance(value, datetime) or hasattr(value, "isoformat"):
                        record[key] = value.isoformat()

            result: dict[str, Any] = {
                "success": True,
                "data": records,
            }

            if include_metadata:
                metadata = AgentOutputMetadata(
                    generated_at=datetime.now(),
                    source="market_analysis",
                    symbols=[symbol] if symbol else [],
                    period=f"{len(data)} records",
                )

                result["metadata"] = {
                    "generated_at": metadata.generated_at.isoformat(),
                    "source": metadata.source,
                    "symbols": metadata.symbols,
                    "record_count": len(records),
                    "columns": list(data.columns),
                }

            logger.debug(
                "Converted to agent JSON",
                success=True,
                record_count=len(records),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to convert to agent JSON",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "error_code": "CONVERSION_ERROR",
            }


__all__ = [
    "MarketData",
]
