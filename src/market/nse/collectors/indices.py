"""NSE Indices data collector with DataCollector ABC compliance.

This module provides ``IndicesCollector``, the entry point for fetching
NSE index data including constituent stocks, all indices summary, and
market status from the NSE India API.
It inherits from ``DataCollector`` and implements the ``fetch()`` /
``validate()`` interface with additional convenience methods.

Features
--------
- DataCollector ABC compliance (fetch / validate interface)
- Dependency injection for NseSession (testability)
- Constituent stock fetching via ``fetch_index()``
- All indices summary via ``fetch_all_indices()``
- Market status via ``fetch_market_status()``

Examples
--------
Fetch index constituents:

>>> collector = IndicesCollector()
>>> df = collector.fetch_index("NIFTY 50")
>>> print(f"Found {len(df)} constituents")

Fetch all indices summary:

>>> df = collector.fetch_all_indices()
>>> print(f"Found {len(df)} indices")

See Also
--------
market.base_collector : DataCollector abstract base class.
market.nse.session : NseSession with cookie lifecycle management.
market.nse.parsers : JSON response parsers.
market.nse.types : IndexConstituent, MarketStatus dataclasses.
market.bse.collectors.index : Reference DataCollector implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from market.base_collector import DataCollector
from market.nse.collectors._base import NseCollectorMixin
from market.nse.constants import API_BASE_URL
from market.nse.parsers import (
    parse_all_indices,
    parse_index_constituents,
    parse_index_constituents_archive_csv,
    parse_market_status,
)
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.nse.session import NseSession
    from market.nse.types import MarketStatus

logger = get_logger(__name__)

# NSE API endpoints
_EQUITY_STOCK_INDICES_ENDPOINT: str = f"{API_BASE_URL}/equity-stockIndices"
_ALL_INDICES_ENDPOINT: str = f"{API_BASE_URL}/allIndices"
_MARKET_STATUS_ENDPOINT: str = f"{API_BASE_URL}/marketStatus"

# NSE Archives static index constituents CSV files
_INDEX_ARCHIVE_BASE_URL: str = "https://nsearchives.nseindia.com/content/indices"

_INDEX_ARCHIVE_FILENAME_MAP: dict[str, str] = {
    "NIFTY 50": "ind_nifty50list.csv",
    "NIFTY 100": "ind_nifty100list.csv",
    "NIFTY 200": "ind_nifty200list.csv",
    "NIFTY 500": "ind_nifty500list.csv",
    "NIFTY TOTAL MKT": "ind_niftytotalmarket_list.csv",
}
"""Mapping from NSE index names to their archive CSV filenames.

Most index names map regularly (``NIFTY 500`` -> ``ind_nifty500list.csv``),
but ``NIFTY TOTAL MKT`` maps irregularly to ``ind_niftytotalmarket_list.csv``.
"""


class IndicesCollector(NseCollectorMixin, DataCollector):
    """Collector for NSE index constituent and summary data.

    Fetches index data from the NSE India API, parsing the JSON response
    into pandas DataFrames or typed dataclass lists.

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
    >>> collector = IndicesCollector()
    >>> df = collector.collect(index_name="NIFTY 50")
    >>> print(f"Collected {len(df)} constituents")

    >>> # With dependency injection for testing
    >>> from unittest.mock import MagicMock
    >>> mock_session = MagicMock(spec=NseSession)
    >>> collector = IndicesCollector(session=mock_session)
    """

    _REQUIRED_COLUMNS: frozenset[str] = frozenset({"symbol"})

    def __init__(self, session: NseSession | None = None) -> None:
        """Initialize IndicesCollector with optional session injection.

        Parameters
        ----------
        session : NseSession | None
            Pre-configured NseSession for dependency injection.
            If None, a new NseSession is created when needed.
        """
        NseCollectorMixin.__init__(self, session=session)

        logger.info(
            "IndicesCollector initialized",
            session_injected=session is not None,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch index constituent data from the NSE API as a DataFrame.

        Sends a GET request to the NSE API's ``/api/equity-stockIndices``
        endpoint, parses the JSON response, and returns a DataFrame with
        constituent stock data.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments.  Expected:
            - index_name (str): NSE index name (e.g., ``"NIFTY 50"``).

        Returns
        -------
        pd.DataFrame
            DataFrame with constituent stock data.

        Raises
        ------
        NseParseError
            If the JSON response cannot be parsed.
        NseAPIError
            If the API returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        ValueError
            If ``index_name`` is not provided.

        Examples
        --------
        >>> collector = IndicesCollector()
        >>> df = collector.fetch(index_name="NIFTY 50")
        >>> "symbol" in df.columns
        True
        """
        index_name: str | None = kwargs.get("index_name")
        if not index_name:
            msg = "index_name is required for fetch()"
            raise ValueError(msg)

        logger.info(
            "Fetching index constituent data",
            index_name=index_name,
        )

        return self.fetch_index(index_name)

    def fetch_index(self, index_name: str) -> pd.DataFrame:
        """Fetch constituent stocks for an NSE index.

        Sends a GET request to the NSE API's ``/api/equity-stockIndices``
        endpoint and parses the JSON response into a pandas DataFrame.

        Parameters
        ----------
        index_name : str
            NSE index name (e.g., ``"NIFTY 50"``, ``"NIFTY BANK"``).

        Returns
        -------
        pd.DataFrame
            DataFrame with constituent stock data including symbol,
            series, open, day_high, day_low, last_price, etc.

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
        >>> collector = IndicesCollector()
        >>> df = collector.fetch_index("NIFTY 50")
        >>> df["symbol"].iloc[0]
        'RELIANCE'
        """
        from dataclasses import asdict

        logger.info(
            "Fetching index",
            index_name=index_name,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _EQUITY_STOCK_INDICES_ENDPOINT,
                params={"index": index_name},
            )

            json_data: dict[str, Any] = response.json()
            constituents = parse_index_constituents(json_data)

            df = pd.DataFrame([asdict(c) for c in constituents])

            logger.info(
                "Index fetched",
                index_name=index_name,
                constituent_count=len(constituents),
            )

            return df
        finally:
            if should_close:
                session.close()

    def fetch_index_constituents_archive(self, index_name: str) -> pd.DataFrame:
        """Fetch constituent stocks for an NSE index from the static CSV archive.

        Unlike ``fetch_index()``, which calls the dynamic
        ``/api/equity-stockIndices`` endpoint, this method downloads a
        static CSV file from NSE Archives
        (``nsearchives.nseindia.com/content/indices/``). Use this method
        when the dynamic API endpoint is unavailable.

        Parameters
        ----------
        index_name : str
            NSE index name. One of ``"NIFTY 50"``, ``"NIFTY 100"``,
            ``"NIFTY 200"``, ``"NIFTY 500"``, ``"NIFTY TOTAL MKT"``.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: company_name, industry, symbol, series, isin.

        Raises
        ------
        ValueError
            If ``index_name`` is not a recognised index.
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
        >>> collector = IndicesCollector()
        >>> df = collector.fetch_index_constituents_archive("NIFTY 50")
        >>> df["symbol"].iloc[0]
        'RELIANCE'
        """
        filename = _INDEX_ARCHIVE_FILENAME_MAP.get(index_name)
        if filename is None:
            msg = (
                f"Unknown index_name for archive CSV: {index_name!r}. "
                f"Expected one of: {sorted(_INDEX_ARCHIVE_FILENAME_MAP)}"
            )
            raise ValueError(msg)

        url = f"{_INDEX_ARCHIVE_BASE_URL}/{filename}"

        logger.info(
            "Fetching index constituents archive CSV",
            index_name=index_name,
            url=url,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(url)
            df = parse_index_constituents_archive_csv(response.content)

            logger.info(
                "Index constituents archive CSV fetched",
                index_name=index_name,
                row_count=len(df),
            )

            return df
        finally:
            if should_close:
                session.close()

    def fetch_all_indices(self) -> pd.DataFrame:
        """Fetch summary data for all NSE indices.

        Sends a GET request to the NSE API's ``/api/allIndices``
        endpoint and parses the JSON response into a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with summary data for all NSE indices, including
            index_symbol, current, variation, pct_change, etc.

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
        >>> collector = IndicesCollector()
        >>> df = collector.fetch_all_indices()
        >>> "index_symbol" in df.columns
        True
        """
        logger.info("Fetching all indices")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(_ALL_INDICES_ENDPOINT)

            json_data: dict[str, Any] = response.json()
            df = parse_all_indices(json_data)

            logger.info(
                "All indices fetched",
                row_count=len(df),
            )

            return df
        finally:
            if should_close:
                session.close()

    def fetch_market_status(self) -> list[MarketStatus]:
        """Fetch current market status for all NSE market segments.

        Sends a GET request to the NSE API's ``/api/marketStatus``
        endpoint and parses the JSON response into a list of
        ``MarketStatus`` dataclasses.

        Returns
        -------
        list[MarketStatus]
            A list of frozen dataclasses, one per market segment.

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
        >>> collector = IndicesCollector()
        >>> statuses = collector.fetch_market_status()
        >>> statuses[0].market
        'Capital Market'
        """
        logger.info("Fetching market status")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(_MARKET_STATUS_ENDPOINT)

            json_data: dict[str, Any] = response.json()
            statuses = parse_market_status(json_data)

            logger.info(
                "Market status fetched",
                segment_count=len(statuses),
            )

            return statuses
        finally:
            if should_close:
                session.close()


__all__ = ["IndicesCollector"]
