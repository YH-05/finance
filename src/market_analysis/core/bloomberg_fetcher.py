"""Bloomberg data fetcher for market data retrieval.

This module provides a concrete implementation of BaseDataFetcher
using the Bloomberg API (BLPAPI) to fetch market data from Bloomberg Terminal.

Note
----
This module requires a Bloomberg Terminal subscription and BLPAPI library.
For testing without Bloomberg, use the MockBloombergFetcher from mock_fetchers.py.
"""

import os
import re
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator

import pandas as pd

from ..errors import DataFetchError, ErrorCode
from ..types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    IdentifierType,
    Interval,
    MarketDataResult,
    RetryConfig,
)
from ..utils.logging_config import get_logger
from .base_fetcher import BaseDataFetcher

logger = get_logger(__name__, module="bloomberg_fetcher")

# Bloomberg symbol patterns
# Supports:
# - AAPL US Equity (ticker + country + asset class, country required for Equity)
# - SPX Index (index name + asset class, no country)
# - USDJPY Curncy (currency pair + asset class)
# - T 5 Govt (treasury + maturity + asset class)
# - CLF4 Comdty (commodity future + asset class)
# Pattern: (ticker [optional_parts] country Equity) | (identifier [optional_parts] non-equity-class)
BLOOMBERG_EQUITY_PATTERN = re.compile(
    r"^[A-Z0-9]+(?: [A-Z0-9]+)* [A-Z]{2} Equity$",
    re.IGNORECASE,
)
BLOOMBERG_NON_EQUITY_PATTERN = re.compile(
    r"^[A-Z0-9]+(?: [A-Z0-9]+)* (Index|Comdty|Govt|Corp|Mtge|Curncy)$",
    re.IGNORECASE,
)


def _is_valid_bloomberg_symbol(symbol: str) -> bool:
    """Check if symbol matches Bloomberg format.

    Parameters
    ----------
    symbol : str
        Symbol to validate

    Returns
    -------
    bool
        True if valid Bloomberg format
    """
    return bool(
        BLOOMBERG_EQUITY_PATTERN.match(symbol)
        or BLOOMBERG_NON_EQUITY_PATTERN.match(symbol)
    )


# For backwards compatibility
BLOOMBERG_SYMBOL_PATTERN = BLOOMBERG_EQUITY_PATTERN

# Check if Bloomberg is available
BLOOMBERG_AVAILABLE = os.environ.get("BLOOMBERG_AVAILABLE", "false").lower() == "true"


def _get_blpapi() -> Any:
    """Dynamically import blpapi module.

    Returns
    -------
    module
        The blpapi module if available

    Raises
    ------
    DataFetchError
        If blpapi is not installed or Bloomberg is not available
    """
    if not BLOOMBERG_AVAILABLE:
        raise DataFetchError(
            "Bloomberg is not available. Set BLOOMBERG_AVAILABLE=true to enable.",
            symbol="",
            source="bloomberg",
            code=ErrorCode.SERVICE_UNAVAILABLE,
        )

    try:
        import blpapi  # type: ignore[import-untyped]

        return blpapi
    except ImportError as e:
        raise DataFetchError(
            "blpapi library is not installed. Install with: pip install blpapi",
            symbol="",
            source="bloomberg",
            code=ErrorCode.SERVICE_UNAVAILABLE,
            cause=e,
        ) from e


class BloombergFetcher(BaseDataFetcher):
    """Data fetcher using Bloomberg API (BLPAPI).

    Fetches OHLCV data and financial data for securities supported
    by Bloomberg Terminal.

    Parameters
    ----------
    host : str
        Bloomberg server host (default: localhost)
    port : int
        Bloomberg server port (default: 8194)
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
        Always returns DataSource.BLOOMBERG

    Examples
    --------
    >>> fetcher = BloombergFetcher()
    >>> options = FetchOptions(
    ...     symbols=["AAPL US Equity"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-12-31",
    ... )
    >>> results = fetcher.fetch(options)
    """

    _REF_DATA_SERVICE = "//blp/refdata"
    _NEWS_SERVICE = "//blp/news"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8194,
        cache: Any | None = None,
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._cache = cache
        self._cache_config = cache_config
        self._retry_config = retry_config
        self._session: Any | None = None

        logger.debug(
            "Initializing BloombergFetcher",
            host=host,
            port=port,
            cache_enabled=cache is not None,
            retry_enabled=retry_config is not None,
        )

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.BLOOMBERG
        """
        return DataSource.BLOOMBERG

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for Bloomberg.

        Bloomberg symbols follow these formats:
        - Equity: TICKER COUNTRY Equity (e.g., AAPL US Equity)
        - Others: IDENTIFIER [PARTS] CLASS (e.g., SPX Index, USDJPY Curncy)

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol matches Bloomberg format

        Examples
        --------
        >>> fetcher.validate_symbol("AAPL US Equity")
        True
        >>> fetcher.validate_symbol("SPX Index")
        True
        >>> fetcher.validate_symbol("AAPL")
        False
        """
        if not symbol or not symbol.strip():
            return False

        return _is_valid_bloomberg_symbol(symbol.strip())

    @contextmanager
    def session(self) -> Generator[Any, None, None]:
        """Context manager for Bloomberg session.

        Creates a Bloomberg session and ensures proper cleanup.

        Yields
        ------
        blpapi.Session
            Active Bloomberg session

        Raises
        ------
        DataFetchError
            If session creation fails

        Examples
        --------
        >>> with fetcher.session() as sess:
        ...     # Use session for data retrieval
        ...     pass
        """
        blpapi = _get_blpapi()

        logger.info("Creating Bloomberg session", host=self._host, port=self._port)

        session_options = blpapi.SessionOptions()
        session_options.setServerHost(self._host)
        session_options.setServerPort(self._port)

        session = blpapi.Session(session_options)

        try:
            if not session.start():
                raise DataFetchError(
                    "Failed to start Bloomberg session. "
                    "Ensure Bloomberg Terminal is running.",
                    symbol="",
                    source=self.source.value,
                    code=ErrorCode.CONNECTION_ERROR,
                )

            if not session.openService(self._REF_DATA_SERVICE):
                raise DataFetchError(
                    f"Failed to open service: {self._REF_DATA_SERVICE}",
                    symbol="",
                    source=self.source.value,
                    code=ErrorCode.SERVICE_UNAVAILABLE,
                )

            logger.info("Bloomberg session started successfully")
            yield session

        finally:
            logger.debug("Stopping Bloomberg session")
            session.stop()

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch historical market data for the given options.

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
        >>> options = FetchOptions(symbols=["AAPL US Equity"])
        >>> results = fetcher.fetch(options)
        >>> results[0].symbol
        'AAPL US Equity'
        """
        self._validate_options(options)

        logger.info(
            "Fetching historical data",
            symbols=options.symbols,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
            interval=options.interval.value,
        )

        results: list[MarketDataResult] = []

        with self.session() as session:
            for symbol in options.symbols:
                result = self._fetch_single(session, symbol, options)
                results.append(result)

        logger.info(
            "Fetch completed",
            total_symbols=len(options.symbols),
            successful=len([r for r in results if not r.is_empty]),
        )

        return results

    def fetch_financial(
        self,
        symbols: list[str],
        fields: list[str],
    ) -> pd.DataFrame:
        """Fetch financial data for securities.

        Parameters
        ----------
        symbols : list[str]
            List of Bloomberg symbols
        fields : list[str]
            List of Bloomberg field codes (e.g., PX_LAST, EPS_BASIC)

        Returns
        -------
        pd.DataFrame
            DataFrame with financial data, indexed by symbol

        Raises
        ------
        DataFetchError
            If fetching fails

        Examples
        --------
        >>> df = fetcher.fetch_financial(
        ...     symbols=["AAPL US Equity", "MSFT US Equity"],
        ...     fields=["PX_LAST", "PE_RATIO", "DIVIDEND_YIELD"],
        ... )
        """
        blpapi = _get_blpapi()

        logger.info(
            "Fetching financial data",
            symbols=symbols,
            fields=fields,
        )

        with self.session() as session:
            ref_data_service = session.getService(self._REF_DATA_SERVICE)
            request = ref_data_service.createRequest("ReferenceDataRequest")

            for symbol in symbols:
                request.append("securities", symbol)

            for field in fields:
                request.append("fields", field)

            session.sendRequest(request)

            data: dict[str, dict[str, Any]] = {}

            while True:
                event = session.nextEvent()

                if event.eventType() == blpapi.Event.RESPONSE:
                    for msg in event:
                        security_data_array = msg.getElement("securityData")

                        for i in range(security_data_array.numValues()):
                            security_data = security_data_array.getValueAsElement(i)
                            security = security_data.getElementAsString("security")

                            field_data = security_data.getElement("fieldData")
                            data[security] = {}

                            for field in fields:
                                if field_data.hasElement(field):
                                    data[security][field] = field_data.getElementValue(
                                        field
                                    )

                    break

                if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    continue

        df = pd.DataFrame.from_dict(data, orient="index")

        logger.info(
            "Financial data fetched",
            rows=len(df),
            columns=list(df.columns),
        )

        return df

    def _fetch_single(
        self,
        session: Any,
        symbol: str,
        options: FetchOptions,
    ) -> MarketDataResult:
        """Fetch historical data for a single symbol.

        Parameters
        ----------
        session : blpapi.Session
            Active Bloomberg session
        symbol : str
            The Bloomberg symbol
        options : FetchOptions
            Fetch options

        Returns
        -------
        MarketDataResult
            The fetch result
        """
        blpapi = _get_blpapi()

        logger.debug("Fetching single symbol", symbol=symbol)

        ref_data_service = session.getService(self._REF_DATA_SERVICE)
        request = ref_data_service.createRequest("HistoricalDataRequest")

        request.append("securities", symbol)

        # Standard OHLCV fields
        fields = ["PX_OPEN", "PX_HIGH", "PX_LOW", "PX_LAST", "VOLUME"]
        for field in fields:
            request.append("fields", field)

        # Set date range
        start = self._format_date(options.start_date)
        end = self._format_date(options.end_date)

        if start:
            request.set("startDate", start)
        if end:
            request.set("endDate", end)

        # Map interval
        request.set("periodicitySelection", self._map_interval(options.interval))

        session.sendRequest(request)

        rows: list[dict[str, Any]] = []

        while True:
            event = session.nextEvent()

            if event.eventType() == blpapi.Event.RESPONSE:
                for msg in event:
                    security_data = msg.getElement("securityData")
                    field_data_array = security_data.getElement("fieldData")

                    for i in range(field_data_array.numValues()):
                        field_data = field_data_array.getValueAsElement(i)

                        row = {
                            "date": field_data.getElementAsDatetime("date"),
                            "open": self._safe_get_value(field_data, "PX_OPEN"),
                            "high": self._safe_get_value(field_data, "PX_HIGH"),
                            "low": self._safe_get_value(field_data, "PX_LOW"),
                            "close": self._safe_get_value(field_data, "PX_LAST"),
                            "volume": self._safe_get_value(field_data, "VOLUME"),
                        }
                        rows.append(row)
                break

            if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                continue

        if not rows:
            logger.warning("No data returned for symbol", symbol=symbol)
            return self._create_result(
                symbol=symbol,
                data=pd.DataFrame(
                    columns=pd.Index(["open", "high", "low", "close", "volume"])
                ),
                from_cache=False,
                metadata={"interval": options.interval.value, "source": "bloomberg"},
            )

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        normalized = self.normalize_dataframe(df, symbol)

        logger.debug(
            "Data fetched successfully",
            symbol=symbol,
            rows=len(normalized),
        )

        return self._create_result(
            symbol=symbol,
            data=normalized,
            from_cache=False,
            metadata={"interval": options.interval.value, "source": "bloomberg"},
        )

    def _safe_get_value(self, element: Any, field: str) -> Any:
        """Safely get a value from a Bloomberg element.

        Parameters
        ----------
        element : blpapi.Element
            Bloomberg element
        field : str
            Field name

        Returns
        -------
        Any
            Field value or None if not present
        """
        try:
            if element.hasElement(field):
                return element.getElementValue(field)
        except Exception:  # noqa: BLE001  # nosec B110 - intentional pass
            pass
        return None

    def _format_date(self, date: datetime | str | None) -> str | None:
        """Format a date for Bloomberg API.

        Parameters
        ----------
        date : datetime | str | None
            Date to format

        Returns
        -------
        str | None
            Formatted date string (YYYYMMDD) or None
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.strftime("%Y%m%d")
        # Try to parse string date
        try:
            parsed = pd.to_datetime(date)
            return parsed.strftime("%Y%m%d")
        except Exception:
            return str(date).replace("-", "")

    def _map_interval(self, interval: Interval) -> str:
        """Map Interval enum to Bloomberg periodicity.

        Parameters
        ----------
        interval : Interval
            Interval enum value

        Returns
        -------
        str
            Bloomberg periodicity string
        """
        mapping = {
            Interval.DAILY: "DAILY",
            Interval.WEEKLY: "WEEKLY",
            Interval.MONTHLY: "MONTHLY",
            Interval.HOURLY: "DAILY",  # Bloomberg doesn't support hourly in HistoricalDataRequest
            Interval.MINUTE: "DAILY",  # Bloomberg doesn't support minute in HistoricalDataRequest
        }
        return mapping.get(interval, "DAILY")

    @staticmethod
    def convert_identifier(
        identifier: str,
        from_type: IdentifierType,
        to_type: IdentifierType = IdentifierType.TICKER,
    ) -> str:
        """Convert between security identifier types.

        Parameters
        ----------
        identifier : str
            The identifier value
        from_type : IdentifierType
            The type of the input identifier
        to_type : IdentifierType
            The type to convert to (default: TICKER)

        Returns
        -------
        str
            Converted identifier in Bloomberg format

        Examples
        --------
        >>> BloombergFetcher.convert_identifier("US0378331005", IdentifierType.ISIN)
        '/isin/US0378331005'

        >>> BloombergFetcher.convert_identifier("2046251", IdentifierType.SEDOL)
        '/sedol/2046251'
        """
        prefix_map = {
            IdentifierType.SEDOL: "/sedol/",
            IdentifierType.CUSIP: "/cusip/",
            IdentifierType.ISIN: "/isin/",
            IdentifierType.FIGI: "/bbgid/",
            IdentifierType.TICKER: "",
        }

        prefix = prefix_map.get(from_type, "")
        return f"{prefix}{identifier}"


__all__ = [
    "BLOOMBERG_AVAILABLE",
    "BLOOMBERG_SYMBOL_PATTERN",
    "BloombergFetcher",
]
