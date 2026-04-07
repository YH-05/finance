"""NSE Corporate data collector (non-ABC).

This module provides ``CorporateCollector``, the entry point for fetching
corporate information from the NSE India API.  Unlike other NSE collectors,
this class does **not** inherit from ``DataCollector`` because its methods
return heterogeneous types (``list[FinancialResult]``,
``list[CorporateEvent]``, ``list[dict]``) rather than a uniform
``pd.DataFrame``.

Features
--------
- Financial results (quarterly / annual) retrieval (``get_financial_results``)
- Corporate event calendar retrieval (``get_event_calendar``)
- Symbol search (``search``)
- Dependency injection for NseSession (testability)

Examples
--------
Financial results:

>>> collector = CorporateCollector()
>>> results = collector.get_financial_results("RELIANCE")
>>> for r in results:
...     print(f"{r.from_date}: EPS {r.eps}")

Event calendar:

>>> events = collector.get_event_calendar()
>>> for e in events:
...     print(f"{e.date}: {e.symbol} - {e.purpose}")

See Also
--------
market.nse.session : NseSession with cookie lifecycle management.
market.nse.parsers : Corporate data parsers.
market.nse.types : FinancialResult, CorporateEvent dataclasses.
market.nse.collectors.quote : Reference DataCollector implementation.
market.bse.collectors.corporate : BSE reference implementation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from market.nse.collectors._base import NseCollectorMixin
from market.nse.constants import API_BASE_URL
from market.nse.parsers import (
    parse_event_calendar,
    parse_financial_results,
    parse_shareholding_pattern,
)
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.nse.session import NseSession
    from market.nse.types import CorporateEvent, FinancialResult, ShareholdingPattern

logger = get_logger(__name__)

# NSE API endpoints for corporate data
_FINANCIAL_RESULTS_ENDPOINT: str = f"{API_BASE_URL}/results-comparision"
_EVENT_CALENDAR_ENDPOINT: str = f"{API_BASE_URL}/event-calendar"
_SEARCH_ENDPOINT: str = f"{API_BASE_URL}/search/autocomplete"
_SHAREHOLDING_ENDPOINT: str = f"{API_BASE_URL}/corporates-shareholding"


class CorporateCollector(NseCollectorMixin):
    """Collector for NSE corporate data (non-ABC).

    Fetches corporate information from the NSE India API including
    financial results, corporate event calendar, and symbol search.

    This class does **not** inherit from ``DataCollector`` because
    its methods return heterogeneous types rather than a uniform
    ``pd.DataFrame``.

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
    >>> collector = CorporateCollector()
    >>> results = collector.get_financial_results("RELIANCE")
    >>> results[0].symbol
    'RELIANCE'

    >>> # With dependency injection for testing
    >>> from unittest.mock import MagicMock
    >>> mock_session = MagicMock(spec=NseSession)
    >>> collector = CorporateCollector(session=mock_session)
    """

    def __init__(self, session: NseSession | None = None) -> None:
        """Initialize CorporateCollector with optional session injection.

        Parameters
        ----------
        session : NseSession | None
            Pre-configured NseSession for dependency injection.
            If None, a new NseSession is created when needed.
        """
        super().__init__(session=session)

        logger.info(
            "CorporateCollector initialized",
            session_injected=session is not None,
        )

    def get_financial_results(
        self,
        symbol: str,
    ) -> list[FinancialResult]:
        """Fetch financial results for an NSE symbol.

        Sends a GET request to the NSE financial results comparison endpoint
        and parses the JSON response into a list of ``FinancialResult``
        dataclasses.

        Parameters
        ----------
        symbol : str
            NSE stock symbol (e.g., ``"RELIANCE"`` for Reliance Industries).

        Returns
        -------
        list[FinancialResult]
            A list of ``FinancialResult`` frozen dataclasses.

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
        >>> collector = CorporateCollector()
        >>> results = collector.get_financial_results("RELIANCE")
        >>> results[0].symbol
        'RELIANCE'
        """
        logger.info(
            "Fetching financial results",
            symbol=symbol,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _FINANCIAL_RESULTS_ENDPOINT,
                params={"symbol": symbol},
            )

            json_data: dict[str, Any] = response.json()
            results = parse_financial_results(json_data, symbol=symbol)

            logger.info(
                "Financial results fetched",
                symbol=symbol,
                count=len(results),
            )

            return results
        finally:
            if should_close:
                session.close()

    def get_event_calendar(self) -> list[CorporateEvent]:
        """Fetch the NSE corporate event calendar.

        Sends a GET request to the NSE event-calendar endpoint
        and parses the JSON response into a list of ``CorporateEvent``
        dataclasses.

        Returns
        -------
        list[CorporateEvent]
            A list of ``CorporateEvent`` frozen dataclasses.

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
        >>> collector = CorporateCollector()
        >>> events = collector.get_event_calendar()
        >>> events[0].symbol
        'RELIANCE'
        """
        logger.info("Fetching event calendar")

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(_EVENT_CALENDAR_ENDPOINT)

            json_data: Any = response.json()

            event_list: list[dict[str, Any]]
            if isinstance(json_data, list):
                event_list = json_data
            elif isinstance(json_data, dict) and "data" in json_data:
                # Some NSE endpoints wrap the list in a dict with a "data" key
                event_list = json_data["data"]
            else:
                event_list = []

            events = parse_event_calendar(event_list)

            logger.info(
                "Event calendar fetched",
                count=len(events),
            )

            return events
        finally:
            if should_close:
                session.close()

    def get_shareholding_pattern(
        self,
        symbol: str,
    ) -> list[ShareholdingPattern]:
        """Fetch shareholding pattern for an NSE symbol.

        Sends a GET request to the NSE corporates-shareholding endpoint
        and parses the JSON response into a list of ``ShareholdingPattern``
        dataclasses containing promoter / FII / DII / public holding
        percentages per quarter.

        Parameters
        ----------
        symbol : str
            NSE stock symbol (e.g., ``"RELIANCE"`` for Reliance Industries).

        Returns
        -------
        list[ShareholdingPattern]
            A list of ``ShareholdingPattern`` frozen dataclasses, one per
            quarterly reporting period, ordered by the API response order
            (most recent first).

        Raises
        ------
        ValueError
            If ``symbol`` is empty, exceeds 20 characters, or contains
            invalid characters.
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
        >>> collector = CorporateCollector()
        >>> patterns = collector.get_shareholding_pattern("RELIANCE")
        >>> patterns[0].symbol
        'RELIANCE'
        >>> patterns[0].promoter_group
        '50.30'
        """
        if not symbol or not symbol.strip():
            raise ValueError("symbol must not be empty")
        if len(symbol) > 20:
            raise ValueError("symbol must not exceed 20 characters")
        if not re.match(r"^[A-Z0-9\-&]+$", symbol):
            raise ValueError(
                "symbol contains invalid characters; "
                "only uppercase alphanumeric, hyphens, and ampersands are allowed"
            )

        logger.info(
            "Fetching shareholding pattern",
            symbol=symbol,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _SHAREHOLDING_ENDPOINT,
                params={"symbol": symbol},
            )

            json_data: Any = response.json()

            # NSE may return a list directly or wrap it in a dict
            data_list: list[dict[str, Any]]
            if isinstance(json_data, list):
                data_list = json_data
            elif isinstance(json_data, dict) and "data" in json_data:
                data_list = json_data["data"]
            else:
                data_list = []

            patterns = parse_shareholding_pattern(data_list)

            logger.info(
                "Shareholding pattern fetched",
                symbol=symbol,
                count=len(patterns),
            )

            return patterns
        finally:
            if should_close:
                session.close()

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search for NSE symbols by name or code.

        Sends a GET request to the NSE autocomplete search endpoint
        and returns a list of matching symbols.

        Parameters
        ----------
        query : str
            Search query string (e.g., ``"RELIANCE"`` or ``"Reliance"``).

        Returns
        -------
        list[dict[str, Any]]
            A list of dicts, each containing symbol information.

        Raises
        ------
        ValueError
            If ``query`` is empty or exceeds 100 characters.
        NseAPIError
            If the API returns an error status code.
        NseRateLimitError
            If rate limiting is detected.
        NseCookieError
            If the NSE session cookie is expired.

        Examples
        --------
        >>> collector = CorporateCollector()
        >>> results = collector.search("RELIANCE")
        >>> results[0]["symbol"]
        'RELIANCE'
        """
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if len(query) > 100:
            raise ValueError("query must not exceed 100 characters")
        if not re.match(r"^[A-Za-z0-9\s\-&.]+$", query):
            raise ValueError(
                "query contains invalid characters; "
                "only alphanumeric, spaces, hyphens, ampersands, and dots are allowed"
            )

        logger.info(
            "Searching symbol",
            query=query,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                _SEARCH_ENDPOINT,
                params={"q": query, "type": "equity"},
            )

            json_data: Any = response.json()

            if not isinstance(json_data, (list, dict)):
                logger.warning(
                    "Unexpected search response type",
                    response_type=type(json_data).__name__,
                )
                return []

            # NSE search may return {"symbols": [...]} or a flat list
            if isinstance(json_data, dict):
                items = json_data.get("symbols", json_data.get("data", []))
            else:
                items = json_data

            if not isinstance(items, list):
                logger.warning(
                    "Unexpected search items type",
                    items_type=type(items).__name__,
                )
                return []

            results: list[dict[str, Any]] = []
            for item in items:
                if isinstance(item, dict):
                    results.append(item)

            logger.info(
                "Symbol search completed",
                query=query,
                count=len(results),
            )

            return results
        finally:
            if should_close:
                session.close()


__all__ = ["CorporateCollector"]
