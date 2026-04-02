"""NSE Stock List data collector with DataCollector ABC compliance.

This module provides ``StockListCollector``, the entry point for fetching
the NSE equity stock list (EQUITY_L.csv), pre-open market data, and
market turnover data from the NSE India API.
It inherits from ``DataCollector`` and implements the ``fetch()`` /
``validate()`` interface with additional convenience methods.

Features
--------
- DataCollector ABC compliance (fetch / validate interface)
- Dependency injection for NseSession (testability)
- Full equity stock list via ``fetch_stock_list()`` (CSV download)
- Pre-open session data via ``fetch_preopen()``
- Market turnover summary via ``fetch_market_turnover()``

Examples
--------
Fetch full stock list:

>>> collector = StockListCollector()
>>> df = collector.fetch_stock_list()
>>> print(f"Found {len(df)} listed stocks")

Fetch pre-open data:

>>> df = collector.fetch_preopen()
>>> print(f"Found {len(df)} pre-open entries")

See Also
--------
market.base_collector : DataCollector abstract base class.
market.nse.session : NseSession with cookie lifecycle management.
market.nse.parsers : CSV and JSON parsers.
market.bse.collectors.bhavcopy : Reference CSV DataCollector implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from market.base_collector import DataCollector
from market.nse.collectors._base import NseCollectorMixin
from market.nse.constants import API_BASE_URL
from market.nse.parsers import parse_preopen_data, parse_stock_list_csv
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.nse.session import NseSession

logger = get_logger(__name__)

# Required columns for validation
_REQUIRED_COLUMNS: frozenset[str] = frozenset({"symbol"})

# NSE data endpoints
_STOCK_LIST_CSV_URL: str = (
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
)
_PREOPEN_ENDPOINT: str = f"{API_BASE_URL}/market-data-pre-open"
_MARKET_TURNOVER_ENDPOINT: str = f"{API_BASE_URL}/market-turnover"


class StockListCollector(NseCollectorMixin, DataCollector):
    """Collector for NSE equity stock list and pre-open data.

    Fetches the NSE equity stock list (CSV), pre-open session data,
    and market turnover data from the NSE India API.

    The ``NseSession`` can be injected via the constructor for testing
    (dependency injection pattern).  When no session is provided, a new
    session is created internally for each operation.

    Parameters
    ----------
    session : NseSession | None
        Pre-configured NseSession instance.  If None, a new session is
        created internally when needed.

    Attributes
    ----------
    _session_instance : NseSession | None
        Injected session instance (None if creating internally).

    Examples
    --------
    >>> collector = StockListCollector()
    >>> df = collector.collect()
    >>> print(f"Collected {len(df)} stocks")

    >>> # With dependency injection for testing
    >>> from unittest.mock import MagicMock
    >>> mock_session = MagicMock(spec=NseSession)
    >>> collector = StockListCollector(session=mock_session)
    """

    def __init__(self, session: NseSession | None = None) -> None:
        """Initialize StockListCollector with optional session injection.

        Parameters
        ----------
        session : NseSession | None
            Pre-configured NseSession for dependency injection.
            If None, a new NseSession is created when needed.
        """
        NseCollectorMixin.__init__(self, session=session)

        logger.info(
            "StockListCollector initialized",
            session_injected=session is not None,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch the NSE equity stock list as a DataFrame.

        Downloads the EQUITY_L.csv file from NSE Archives and parses
        it into a pandas DataFrame.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments (currently unused; reserved for future options).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: symbol, company_name, series,
            date_of_listing, paid_up_value, market_lot, isin, face_value.

        Raises
        ------
        NseParseError
            If the CSV content cannot be parsed.
        NseAPIError
            If the download returns an error status code.
        NseRateLimitError
            If rate limiting is detected.

        Examples
        --------
        >>> collector = StockListCollector()
        >>> df = collector.fetch()
        >>> "symbol" in df.columns
        True
        """
        logger.info("Fetching stock list via fetch()")
        return self.fetch_stock_list()

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched stock list data.

        Checks that the DataFrame:
        - Is not empty
        - Contains the required column (``symbol``)

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = StockListCollector()
        >>> df = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
        >>> collector.validate(df)
        True
        >>> collector.validate(pd.DataFrame())
        False
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        missing = _REQUIRED_COLUMNS - set(df.columns)
        if missing:
            logger.warning(
                "Validation failed: missing required columns",
                missing_columns=sorted(missing),
                actual_columns=list(df.columns),
            )
            return False

        logger.debug(
            "Validation passed",
            row_count=len(df),
        )
        return True

    def fetch_stock_list(self) -> pd.DataFrame:
        """Fetch the complete NSE equity stock list from EQUITY_L.csv.

        Downloads the CSV file from NSE Archives
        (``https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv``)
        and parses it into a cleaned pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: symbol, company_name, series,
            date_of_listing, paid_up_value, market_lot, isin, face_value.

        Raises
        ------
        NseParseError
            If the CSV content cannot be parsed or is empty.
        NseAPIError
            If the download returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        NseCookieError
            If the NSE session cookie is expired.

        Examples
        --------
        >>> collector = StockListCollector()
        >>> df = collector.fetch_stock_list()
        >>> df["symbol"].iloc[0]
        'RELIANCE'
        """
        logger.info("Fetching NSE stock list CSV")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(_STOCK_LIST_CSV_URL)
            content = response.content

            df = parse_stock_list_csv(content)

            logger.info(
                "Stock list fetched",
                row_count=len(df),
            )

            return df
        finally:
            if should_close:
                session.close()

    def fetch_preopen(self) -> pd.DataFrame:
        """Fetch NSE pre-open session market data.

        Sends a GET request to the NSE API's
        ``/api/market-data-pre-open?key=ALL`` endpoint and parses
        the JSON response into a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with pre-open market data including symbol,
            iep (indicative equilibrium price), change, pct_change, etc.

        Raises
        ------
        NseParseError
            If the JSON response cannot be parsed.
        NseAPIError
            If the API returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        NseCookieError
            If the NSE session cookie is expired.

        Examples
        --------
        >>> collector = StockListCollector()
        >>> df = collector.fetch_preopen()
        >>> "symbol" in df.columns
        True
        """
        logger.info("Fetching pre-open market data")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _PREOPEN_ENDPOINT,
                params={"key": "ALL"},
            )

            json_data: dict[str, Any] = response.json()
            df = parse_preopen_data(json_data)

            logger.info(
                "Pre-open data fetched",
                row_count=len(df),
            )

            return df
        finally:
            if should_close:
                session.close()

    def fetch_market_turnover(self) -> dict[str, Any]:
        """Fetch NSE market turnover summary.

        Sends a GET request to the NSE API's ``/api/market-turnover``
        endpoint and returns the raw JSON response as a dictionary.

        Returns
        -------
        dict[str, Any]
            A dictionary containing market turnover data with various
            segment-level trading statistics.

        Raises
        ------
        NseAPIError
            If the API returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        NseCookieError
            If the NSE session cookie is expired.

        Examples
        --------
        >>> collector = StockListCollector()
        >>> turnover = collector.fetch_market_turnover()
        >>> isinstance(turnover, dict)
        True
        """
        logger.info("Fetching market turnover")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(_MARKET_TURNOVER_ENDPOINT)

            json_data: dict[str, Any] = response.json()

            logger.info("Market turnover fetched")

            return json_data
        finally:
            if should_close:
                session.close()


__all__ = ["StockListCollector"]
