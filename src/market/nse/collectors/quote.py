"""NSE Quote data collector with DataCollector ABC compliance.

This module provides ``QuoteCollector``, the main entry point for
fetching equity quote data from the NSE India API.
It inherits from ``DataCollector`` and implements the ``fetch()`` /
``validate()`` interface with an additional convenience method for
single-symbol quote retrieval.

Features
--------
- DataCollector ABC compliance (fetch / validate interface)
- Dependency injection for NseSession (testability)
- Single quote fetching via ``fetch_quote()``

Examples
--------
Basic quote fetch:

>>> collector = QuoteCollector()
>>> quote = collector.fetch_quote("RELIANCE")
>>> print(f"Symbol: {quote.symbol}")

DataFrame fetch:

>>> df = collector.fetch(symbol="RELIANCE")
>>> print(f"Found {len(df)} rows")

See Also
--------
market.base_collector : DataCollector abstract base class.
market.nse.session : NseSession with cookie lifecycle management.
market.nse.parsers : JSON response parser.
market.nse.types : StockQuote dataclass.
market.bse.collectors.quote : Reference DataCollector implementation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

import pandas as pd

from market.base_collector import DataCollector
from market.nse.collectors._base import NseCollectorMixin
from market.nse.constants import API_BASE_URL
from market.nse.parsers import parse_quote_response
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.nse.session import NseSession
    from market.nse.types import StockQuote

logger = get_logger(__name__)

# NSE API endpoints
_QUOTE_ENDPOINT: str = f"{API_BASE_URL}/quote-equity"


class QuoteCollector(NseCollectorMixin, DataCollector):
    """Collector for NSE equity quote data.

    Fetches quote data from the NSE India API, parsing the JSON response
    into ``StockQuote`` dataclasses or pandas DataFrames.

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
    >>> collector = QuoteCollector()
    >>> df = collector.collect(symbol="RELIANCE")
    >>> print(f"Collected {len(df)} rows")

    >>> # With dependency injection for testing
    >>> from unittest.mock import MagicMock
    >>> mock_session = MagicMock(spec=NseSession)
    >>> collector = QuoteCollector(session=mock_session)
    """

    _REQUIRED_COLUMNS: frozenset[str] = frozenset({"symbol", "company_name"})

    def __init__(self, session: NseSession | None = None) -> None:
        """Initialize QuoteCollector with optional session injection.

        Parameters
        ----------
        session : NseSession | None
            Pre-configured NseSession for dependency injection.
            If None, a new NseSession is created when needed.
        """
        NseCollectorMixin.__init__(self, session=session)

        logger.info(
            "QuoteCollector initialized",
            session_injected=session is not None,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch equity quote data from the NSE API as a DataFrame.

        Sends a GET request to the NSE API's ``/api/quote-equity``
        endpoint, parses the JSON response, and returns a single-row
        DataFrame with the quote data.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments.  Expected:
            - symbol (str): NSE stock symbol (e.g., ``"RELIANCE"``).

        Returns
        -------
        pd.DataFrame
            Single-row DataFrame with columns matching ``StockQuote`` fields.

        Raises
        ------
        NseParseError
            If the JSON response cannot be parsed.
        NseAPIError
            If the API returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        ValueError
            If ``symbol`` is not provided.

        Examples
        --------
        >>> collector = QuoteCollector()
        >>> df = collector.fetch(symbol="RELIANCE")
        >>> df["symbol"].iloc[0]
        'RELIANCE'
        """
        symbol: str | None = kwargs.get("symbol")
        if not symbol:
            msg = "symbol is required for fetch()"
            raise ValueError(msg)

        logger.info(
            "Fetching quote data",
            symbol=symbol,
        )

        quote = self.fetch_quote(symbol)

        df = pd.DataFrame([asdict(quote)])

        logger.info(
            "Quote data fetched as DataFrame",
            symbol=symbol,
            columns=list(df.columns),
        )

        return df

    def fetch_quote(self, symbol: str) -> StockQuote:
        """Fetch a single equity quote from the NSE API.

        Sends a GET request to the NSE API's ``/api/quote-equity``
        endpoint and parses the JSON response into a ``StockQuote``
        dataclass.

        Parameters
        ----------
        symbol : str
            NSE stock symbol (e.g., ``"RELIANCE"`` for Reliance Industries).

        Returns
        -------
        StockQuote
            A frozen dataclass containing the parsed quote data.

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
        >>> collector = QuoteCollector()
        >>> quote = collector.fetch_quote("RELIANCE")
        >>> quote.symbol
        'RELIANCE'
        """
        logger.info(
            "Fetching quote",
            symbol=symbol,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _QUOTE_ENDPOINT,
                params={"symbol": symbol},
            )

            json_data: dict[str, Any] = response.json()
            quote = parse_quote_response(json_data)

            logger.info(
                "Quote fetched",
                symbol=quote.symbol,
                company_name=quote.company_name,
            )

            return quote
        finally:
            if should_close:
                session.close()


__all__ = ["QuoteCollector"]
