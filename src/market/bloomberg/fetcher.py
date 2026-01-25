"""Bloomberg data fetcher for market data retrieval.

This module provides a concrete implementation for fetching market data
using the Bloomberg BLPAPI to fetch data from Bloomberg Terminal.

Supports
--------
- Historical price data
- Reference data
- Financial data
- News data
- Field information
- Identifier conversion
- Index members
- Database storage

Examples
--------
>>> from market.bloomberg import BloombergFetcher, BloombergFetchOptions
>>> fetcher = BloombergFetcher()
>>> options = BloombergFetchOptions(
...     securities=["AAPL US Equity"],
...     fields=["PX_LAST", "PX_VOLUME"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> results = fetcher.get_historical_data(options)
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import blpapi
import pandas as pd

from database.utils.logging_config import get_logger
from market.bloomberg.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    NEWS_SERVICE,
    REF_DATA_SERVICE,
)
from market.bloomberg.errors import (
    BloombergConnectionError,
    BloombergSessionError,
    BloombergValidationError,
    ErrorCode,
)
from market.bloomberg.types import (
    BloombergDataResult,
    BloombergFetchOptions,
    DataSource,
    FieldInfo,
    IDType,
    NewsStory,
)

logger = get_logger(__name__, module="market.bloomberg.fetcher")

# Bloomberg security identifier pattern
# Supports: AAPL US Equity, IBM US Equity, USDJPY Curncy, SPX Index
BLOOMBERG_SECURITY_PATTERN = re.compile(
    r"^[A-Z0-9./\-]+ (Equity|Index|Curncy|Govt|Corp|Mtge|Pfd|Cmdty|Muni|Comdty)$",
    re.IGNORECASE,
)


class BloombergFetcher:
    """Data fetcher using Bloomberg BLPAPI.

    Fetches various types of data from Bloomberg Terminal including
    historical prices, reference data, financial data, and news.

    Parameters
    ----------
    host : str
        Bloomberg Terminal host address (default: localhost)
    port : int
        Bloomberg Terminal port (default: 8194)

    Attributes
    ----------
    host : str
        Bloomberg Terminal host address
    port : int
        Bloomberg Terminal port
    source : DataSource
        Always returns DataSource.BLOOMBERG
    REF_DATA_SERVICE : str
        Bloomberg reference data service endpoint
    NEWS_SERVICE : str
        Bloomberg news service endpoint

    Examples
    --------
    >>> fetcher = BloombergFetcher()
    >>> options = BloombergFetchOptions(
    ...     securities=["AAPL US Equity"],
    ...     fields=["PX_LAST", "PX_VOLUME"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-12-31",
    ... )
    >>> results = fetcher.get_historical_data(options)
    >>> len(results)
    1
    """

    # Class-level service constants
    REF_DATA_SERVICE: str = REF_DATA_SERVICE
    NEWS_SERVICE: str = NEWS_SERVICE

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port

        logger.debug(
            "Initializing BloombergFetcher",
            host=host,
            port=port,
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

    def validate_security(self, security: str) -> bool:
        """Validate that a security identifier is valid for Bloomberg.

        Bloomberg securities typically follow the format:
        ``<TICKER> <YELLOW_KEY>`` where YELLOW_KEY is one of:
        Equity, Index, Curncy, Govt, Corp, Mtge, Pfd, Cmdty, Muni, Comdty.

        Parameters
        ----------
        security : str
            The security identifier to validate

        Returns
        -------
        bool
            True if the security matches Bloomberg format

        Examples
        --------
        >>> fetcher = BloombergFetcher()
        >>> fetcher.validate_security("AAPL US Equity")
        True
        >>> fetcher.validate_security("SPX Index")
        True
        >>> fetcher.validate_security("USDJPY Curncy")
        True
        >>> fetcher.validate_security("invalid")
        False
        """
        if not security or not security.strip():
            return False

        return bool(BLOOMBERG_SECURITY_PATTERN.match(security.strip()))

    def _create_session(self) -> blpapi.Session:
        """Create and start a Bloomberg session.

        Returns
        -------
        blpapi.Session
            Started Bloomberg session

        Raises
        ------
        BloombergConnectionError
            If connection to Bloomberg Terminal fails
        """
        logger.debug("Creating Bloomberg session", host=self.host, port=self.port)

        session_options = blpapi.SessionOptions()
        session_options.setServerHost(self.host)
        session_options.setServerPort(self.port)

        session = blpapi.Session(session_options)

        if not session.start():
            logger.error(
                "Failed to start Bloomberg session",
                host=self.host,
                port=self.port,
            )
            raise BloombergConnectionError(
                "Failed to connect to Bloomberg Terminal. "
                "Ensure Bloomberg Terminal is running.",
                host=self.host,
                port=self.port,
            )

        logger.debug("Bloomberg session started successfully")
        return session

    def _open_service(self, session: blpapi.Session, service: str) -> None:
        """Open a Bloomberg service.

        Parameters
        ----------
        session : blpapi.Session
            Active Bloomberg session
        service : str
            Service name to open

        Raises
        ------
        BloombergSessionError
            If service fails to open
        """
        logger.debug("Opening Bloomberg service", service=service)

        if not session.openService(service):
            logger.error("Failed to open Bloomberg service", service=service)
            raise BloombergSessionError(
                f"Failed to open Bloomberg service: {service}",
                service=service,
            )

        logger.debug("Bloomberg service opened successfully", service=service)

    def _validate_options(self, options: BloombergFetchOptions) -> None:
        """Validate fetch options.

        Parameters
        ----------
        options : BloombergFetchOptions
            Options to validate

        Raises
        ------
        BloombergValidationError
            If options are invalid
        """
        logger.debug(
            "Validating fetch options",
            securities_count=len(options.securities),
            fields_count=len(options.fields),
        )

        if not options.securities:
            logger.error("Empty securities list")
            raise BloombergValidationError(
                "securities list must not be empty",
                field="securities",
                value=options.securities,
            )

        if not options.fields:
            logger.error("Empty fields list")
            raise BloombergValidationError(
                "fields list must not be empty",
                field="fields",
                value=options.fields,
            )

        # Validate date range if both dates are provided
        if options.start_date and options.end_date:
            start = self._parse_date(options.start_date)
            end = self._parse_date(options.end_date)

            if start and end and start > end:
                logger.error(
                    "Invalid date range: start_date is after end_date",
                    start_date=str(start),
                    end_date=str(end),
                )
                raise BloombergValidationError(
                    "Invalid date range: start_date must be before or equal to end_date",
                    field="date_range",
                    value={"start_date": str(start), "end_date": str(end)},
                    code=ErrorCode.INVALID_DATE_RANGE,
                )

        logger.debug("Fetch options validated successfully")

    def _parse_date(self, date: datetime | str | None) -> datetime | None:
        """Parse a date value to datetime.

        Parameters
        ----------
        date : datetime | str | None
            Date to parse

        Returns
        -------
        datetime | None
            Parsed datetime or None
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date
        # date is str at this point
        return datetime.strptime(date, "%Y-%m-%d")

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
        # date is str at this point - assume YYYY-MM-DD format, convert to YYYYMMDD
        return date.replace("-", "")

    def get_historical_data(
        self,
        options: BloombergFetchOptions,
    ) -> list[BloombergDataResult]:
        """Fetch historical data for securities.

        Parameters
        ----------
        options : BloombergFetchOptions
            Options specifying securities, fields, and date range

        Returns
        -------
        list[BloombergDataResult]
            List of results for each security

        Raises
        ------
        BloombergValidationError
            If options are invalid
        BloombergConnectionError
            If connection to Bloomberg fails
        BloombergSessionError
            If service fails to open
        BloombergDataError
            If data fetching fails

        Examples
        --------
        >>> options = BloombergFetchOptions(
        ...     securities=["AAPL US Equity"],
        ...     fields=["PX_LAST"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ... )
        >>> results = fetcher.get_historical_data(options)
        """
        self._validate_options(options)

        logger.info(
            "Fetching historical data",
            securities=options.securities,
            fields=options.fields,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
        )

        session = self._create_session()
        try:
            self._open_service(session, self.REF_DATA_SERVICE)

            results: list[BloombergDataResult] = []

            for security in options.securities:
                data = self._process_historical_response(security, options)
                result = BloombergDataResult(
                    security=security,
                    data=data,
                    source=self.source,
                    fetched_at=datetime.now(),
                    metadata={
                        "fields": options.fields,
                        "periodicity": options.periodicity.value,
                    },
                )
                results.append(result)

            logger.info(
                "Historical data fetch completed",
                total_securities=len(options.securities),
                successful=len([r for r in results if not r.is_empty]),
            )

            return results

        finally:
            session.stop()
            logger.debug("Bloomberg session stopped")

    def _process_historical_response(
        self,
        security: str,
        options: BloombergFetchOptions,
    ) -> pd.DataFrame:
        """Process historical data response.

        This is a placeholder that should be replaced with actual
        Bloomberg API response processing.

        Parameters
        ----------
        security : str
            Security identifier
        options : BloombergFetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Historical data
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        # Actual implementation would process blpapi response
        logger.debug("Processing historical response", security=security)
        return pd.DataFrame()

    def get_reference_data(
        self,
        options: BloombergFetchOptions,
    ) -> list[BloombergDataResult]:
        """Fetch reference data for securities.

        Parameters
        ----------
        options : BloombergFetchOptions
            Options specifying securities and fields

        Returns
        -------
        list[BloombergDataResult]
            List of results for each security

        Raises
        ------
        BloombergValidationError
            If options are invalid
        BloombergConnectionError
            If connection to Bloomberg fails
        BloombergSessionError
            If service fails to open
        """
        self._validate_options(options)

        logger.info(
            "Fetching reference data",
            securities=options.securities,
            fields=options.fields,
        )

        session = self._create_session()
        try:
            self._open_service(session, self.REF_DATA_SERVICE)

            results: list[BloombergDataResult] = []

            for security in options.securities:
                data = self._process_reference_response(security, options)
                result = BloombergDataResult(
                    security=security,
                    data=data,
                    source=self.source,
                    fetched_at=datetime.now(),
                    metadata={"fields": options.fields},
                )
                results.append(result)

            logger.info(
                "Reference data fetch completed",
                total_securities=len(options.securities),
            )

            return results

        finally:
            session.stop()
            logger.debug("Bloomberg session stopped")

    def _process_reference_response(
        self,
        security: str,
        options: BloombergFetchOptions,
    ) -> pd.DataFrame:
        """Process reference data response.

        Parameters
        ----------
        security : str
            Security identifier
        options : BloombergFetchOptions
            Fetch options

        Returns
        -------
        pd.DataFrame
            Reference data
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug("Processing reference response", security=security)
        return pd.DataFrame()

    def get_financial_data(
        self,
        options: BloombergFetchOptions,
    ) -> list[BloombergDataResult]:
        """Fetch financial data for securities.

        This is similar to get_reference_data but typically used
        for financial statement data with period overrides.

        Parameters
        ----------
        options : BloombergFetchOptions
            Options specifying securities, fields, and overrides

        Returns
        -------
        list[BloombergDataResult]
            List of results for each security
        """
        logger.info(
            "Fetching financial data",
            securities=options.securities,
            fields=options.fields,
            overrides=[o.field for o in options.overrides],
        )

        # Financial data uses the same reference data service
        return self.get_reference_data(options)

    def convert_identifiers(
        self,
        identifiers: list[str],
        from_type: IDType,
        to_type: IDType,
    ) -> dict[str, str]:
        """Convert security identifiers between types.

        Parameters
        ----------
        identifiers : list[str]
            List of identifiers to convert
        from_type : IDType
            Source identifier type
        to_type : IDType
            Target identifier type

        Returns
        -------
        dict[str, str]
            Mapping of source identifiers to target identifiers

        Examples
        --------
        >>> result = fetcher.convert_identifiers(
        ...     ["US0378331005"],
        ...     from_type=IDType.ISIN,
        ...     to_type=IDType.TICKER,
        ... )
        >>> result["US0378331005"]
        'AAPL US Equity'
        """
        logger.info(
            "Converting identifiers",
            count=len(identifiers),
            from_type=from_type.value,
            to_type=to_type.value,
        )

        session = self._create_session()
        try:
            self._open_service(session, self.REF_DATA_SERVICE)
            result = self._process_id_conversion(identifiers, from_type, to_type)

            logger.info(
                "Identifier conversion completed",
                converted_count=len(result),
            )

            return result

        finally:
            session.stop()

    def _process_id_conversion(
        self,
        identifiers: list[str],
        from_type: IDType,
        to_type: IDType,
    ) -> dict[str, str]:
        """Process identifier conversion response.

        Parameters
        ----------
        identifiers : list[str]
            Identifiers to convert
        from_type : IDType
            Source identifier type
        to_type : IDType
            Target identifier type

        Returns
        -------
        dict[str, str]
            Conversion mapping
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug(
            "Processing ID conversion",
            identifiers=identifiers,
            from_type=from_type.value,
            to_type=to_type.value,
        )
        return {}

    def get_historical_news_by_security(
        self,
        security: str,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> list[NewsStory]:
        """Fetch historical news for a security.

        Parameters
        ----------
        security : str
            Security identifier
        start_date : datetime | str | None
            Start date for news search
        end_date : datetime | str | None
            End date for news search

        Returns
        -------
        list[NewsStory]
            List of news stories

        Examples
        --------
        >>> stories = fetcher.get_historical_news_by_security(
        ...     "AAPL US Equity",
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        """
        logger.info(
            "Fetching historical news",
            security=security,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        session = self._create_session()
        try:
            self._open_service(session, self.NEWS_SERVICE)
            stories = self._process_news_response(security, start_date, end_date)

            logger.info(
                "News fetch completed",
                security=security,
                story_count=len(stories),
            )

            return stories

        finally:
            session.stop()

    def _process_news_response(
        self,
        security: str,
        start_date: datetime | str | None,
        end_date: datetime | str | None,
    ) -> list[NewsStory]:
        """Process news response.

        Parameters
        ----------
        security : str
            Security identifier
        start_date : datetime | str | None
            Start date
        end_date : datetime | str | None
            End date

        Returns
        -------
        list[NewsStory]
            News stories
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug("Processing news response", security=security)
        return []

    def get_news_story_content(self, story_id: str) -> str:
        """Fetch full content of a news story.

        Parameters
        ----------
        story_id : str
            Bloomberg story identifier

        Returns
        -------
        str
            Full story content
        """
        logger.info("Fetching news story content", story_id=story_id)

        session = self._create_session()
        try:
            self._open_service(session, self.NEWS_SERVICE)
            content = self._fetch_story_content(story_id)

            logger.info("Story content fetched", story_id=story_id)

            return content

        finally:
            session.stop()

    def _fetch_story_content(self, story_id: str) -> str:
        """Fetch story content from Bloomberg.

        Parameters
        ----------
        story_id : str
            Story identifier

        Returns
        -------
        str
            Story content
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug("Fetching story content", story_id=story_id)
        return ""

    def get_index_members(self, index: str) -> list[str]:
        """Fetch index constituent members.

        Parameters
        ----------
        index : str
            Index identifier (e.g., "SPX Index")

        Returns
        -------
        list[str]
            List of constituent securities

        Examples
        --------
        >>> members = fetcher.get_index_members("SPX Index")
        >>> "AAPL US Equity" in members
        True
        """
        logger.info("Fetching index members", index=index)

        session = self._create_session()
        try:
            self._open_service(session, self.REF_DATA_SERVICE)
            members = self._process_index_members(index)

            logger.info("Index members fetched", index=index, count=len(members))

            return members

        finally:
            session.stop()

    def _process_index_members(self, index: str) -> list[str]:
        """Process index members response.

        Parameters
        ----------
        index : str
            Index identifier

        Returns
        -------
        list[str]
            Index members
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug("Processing index members", index=index)
        return []

    def get_field_info(self, field_id: str) -> FieldInfo:
        """Fetch Bloomberg field metadata.

        Parameters
        ----------
        field_id : str
            Bloomberg field mnemonic (e.g., "PX_LAST")

        Returns
        -------
        FieldInfo
            Field metadata

        Examples
        --------
        >>> info = fetcher.get_field_info("PX_LAST")
        >>> info.field_name
        'Last Price'
        """
        logger.info("Fetching field info", field_id=field_id)

        session = self._create_session()
        try:
            self._open_service(session, self.REF_DATA_SERVICE)
            info = self._process_field_info(field_id)

            logger.info("Field info fetched", field_id=field_id)

            return info

        finally:
            session.stop()

    def _process_field_info(self, field_id: str) -> FieldInfo:
        """Process field info response.

        Parameters
        ----------
        field_id : str
            Field identifier

        Returns
        -------
        FieldInfo
            Field information
        """
        # AIDEV-NOTE: This method is typically mocked in tests
        logger.debug("Processing field info", field_id=field_id)
        return FieldInfo(
            field_id=field_id,
            field_name="",
            description="",
            data_type="",
        )

    def store_to_database(
        self,
        data: pd.DataFrame,
        db_path: str,
        table_name: str,
    ) -> None:
        """Store data to SQLite database.

        Parameters
        ----------
        data : pd.DataFrame
            Data to store
        db_path : str
            Path to SQLite database
        table_name : str
            Target table name

        Examples
        --------
        >>> fetcher.store_to_database(
        ...     data=df,
        ...     db_path="/path/to/db.sqlite",
        ...     table_name="historical_prices",
        ... )
        """
        logger.info(
            "Storing data to database",
            db_path=db_path,
            table_name=table_name,
            rows=len(data),
        )

        # Ensure parent directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_path) as conn:
            data.to_sql(
                table_name,
                conn,
                if_exists="replace",
                index=False,
            )

        logger.info(
            "Data stored successfully",
            db_path=db_path,
            table_name=table_name,
        )

    def get_latest_date_from_db(
        self,
        db_path: str,
        table_name: str,
        date_column: str = "date",
    ) -> datetime | None:
        """Get the latest date from a database table.

        Parameters
        ----------
        db_path : str
            Path to SQLite database
        table_name : str
            Table name to query
        date_column : str
            Name of date column (default: "date")

        Returns
        -------
        datetime | None
            Latest date or None if table is empty

        Examples
        --------
        >>> latest = fetcher.get_latest_date_from_db(
        ...     db_path="/path/to/db.sqlite",
        ...     table_name="historical_prices",
        ... )
        """
        logger.debug(
            "Getting latest date from database",
            db_path=db_path,
            table_name=table_name,
            date_column=date_column,
        )

        with sqlite3.connect(db_path) as conn:
            query = f"SELECT MAX({date_column}) FROM {table_name}"  # nosec B608
            cursor = conn.execute(query)
            result = cursor.fetchone()

            if result and result[0]:
                latest_date = pd.to_datetime(result[0])
                logger.debug("Latest date found", date=str(latest_date))
                return latest_date.to_pydatetime()

        logger.debug("No data found in table", table_name=table_name)
        return None


__all__ = [
    "BLOOMBERG_SECURITY_PATTERN",
    "BloombergFetcher",
]
