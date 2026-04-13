"""NSE Shareholding data collector (non-ABC).

This module provides ``ShareholdingCollector``, which fetches corporate
shareholding data from the NSE India API and XBRL archives.  Unlike other
NSE collectors, this class does **not** inherit from ``DataCollector``
because its methods return heterogeneous types (``list[CorporateShareHolding]``,
``ParseResult``) rather than a uniform ``pd.DataFrame``.

Features
--------
- Corporate shareholding list retrieval (``fetch_shareholding``)
- XBRL detail download and parsing (``fetch_xbrl_detail``)
- 3-stage input validation (empty / length / regex) – mirrors CorporateCollector
- SSRF prevention via existing NseSession ALLOWED_HOSTS guard
- Dependency injection for NseSession (testability)

Examples
--------
Corporate shareholding list:

>>> collector = ShareholdingCollector()
>>> holdings = collector.fetch_shareholding("RELIANCE")
>>> for h in holdings:
...     print(f"{h.as_on_date}: promoter {h.promoter_group_pct}%")

XBRL detail:

>>> result = collector.fetch_xbrl_detail(holdings[0].xbrl_url)
>>> print(result.symbol, result.as_on_date, len(result.rows))

See Also
--------
market.nse.session : NseSession with cookie lifecycle management.
market.nse.parsers : parse_corporate_shareholding.
market.nse.xbrl : parse_xbrl, ParseResult, ShareholderRow, ContextInfo.
market.nse.types : CorporateShareHolding dataclass.
market.nse.collectors.corporate : Reference non-ABC collector implementation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from market.nse.collectors._base import NseCollectorMixin
from market.nse.constants import CORPORATE_SHARE_HOLDINGS_ENDPOINT
from market.nse.parsers import parse_corporate_shareholding
from market.nse.xbrl import ParseResult, parse_xbrl
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.nse.session import NseSession
    from market.nse.types import CorporateShareHolding

logger = get_logger(__name__)


class ShareholdingCollector(NseCollectorMixin):
    """Collector for NSE corporate shareholding data (non-ABC).

    Fetches corporate shareholding information from the NSE India API
    (``/api/corporate-share-holdings-master``) and parses XBRL shareholding
    detail files from the NSE archives server.

    This class does **not** inherit from ``DataCollector`` because its
    methods return heterogeneous types rather than a uniform ``pd.DataFrame``.

    The ``NseSession`` can be injected via the constructor for testing
    (dependency injection pattern).  When no session is provided, a new
    session is created internally for each operation and closed in the
    ``finally`` block.

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
    >>> collector = ShareholdingCollector()
    >>> holdings = collector.fetch_shareholding("RELIANCE")
    >>> holdings[0].symbol
    'RELIANCE'

    >>> # With dependency injection for testing
    >>> from unittest.mock import MagicMock
    >>> from market.nse.session import NseSession
    >>> mock_session = MagicMock(spec=NseSession)
    >>> collector = ShareholdingCollector(session=mock_session)
    """

    def __init__(self, session: NseSession | None = None) -> None:
        """Initialize ShareholdingCollector with optional session injection.

        Parameters
        ----------
        session : NseSession | None
            Pre-configured NseSession for dependency injection.
            If None, a new NseSession is created when needed.
        """
        super().__init__(session=session)

        logger.info(
            "ShareholdingCollector initialized",
            session_injected=session is not None,
        )

    def fetch_shareholding(
        self,
        symbol: str,
    ) -> list[CorporateShareHolding]:
        """Fetch corporate shareholding records for an NSE symbol.

        Sends a GET request to the NSE ``corporate-share-holdings-master``
        endpoint and parses the JSON response into a list of
        ``CorporateShareHolding`` dataclasses, one per quarterly filing.

        3-stage input validation (mirrors ``CorporateCollector.get_shareholding_pattern``):

        1. Empty / blank check
        2. Maximum length check (20 characters)
        3. Regex validation (uppercase alphanumeric, hyphens, ampersands only)

        Parameters
        ----------
        symbol : str
            NSE stock symbol (e.g., ``"RELIANCE"`` for Reliance Industries).
            Must be non-empty, at most 20 characters, and match
            ``^[A-Z0-9\\-&]+$``.

        Returns
        -------
        list[CorporateShareHolding]
            A list of ``CorporateShareHolding`` frozen dataclasses, one per
            quarterly filing, ordered by the API response order (most recent
            first).

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
        >>> collector = ShareholdingCollector()
        >>> holdings = collector.fetch_shareholding("RELIANCE")
        >>> holdings[0].symbol
        'RELIANCE'
        >>> holdings[0].promoter_group_pct
        '50.01'
        >>> holdings[0].xbrl_url
        'https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml'
        """
        # Stage 1: empty / blank
        if not symbol or not symbol.strip():
            raise ValueError("symbol must not be empty")
        # Stage 2: length
        if len(symbol) > 20:
            raise ValueError("symbol must not exceed 20 characters")
        # Stage 3: character set (uppercase alphanumeric, hyphens, ampersands)
        if not re.match(r"^[A-Z0-9\-&]+$", symbol):
            raise ValueError(
                "symbol contains invalid characters; "
                "only uppercase alphanumeric, hyphens, and ampersands are allowed"
            )

        logger.info(
            "Fetching corporate shareholding",
            symbol=symbol,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(
                CORPORATE_SHARE_HOLDINGS_ENDPOINT,
                params={
                    "index": "equities",
                    "symbol": symbol,
                },
            )

            json_data = response.json()
            holdings = parse_corporate_shareholding(json_data, symbol=symbol)

            logger.info(
                "Corporate shareholding fetched",
                symbol=symbol,
                count=len(holdings),
            )

            return holdings
        finally:
            if should_close:
                session.close()

    def fetch_xbrl_detail(
        self,
        xbrl_url: str,
    ) -> ParseResult:
        """Download and parse an NSE XBRL shareholding file.

        Sends a GET request to the given ``xbrl_url`` via ``NseSession``
        (which enforces the ``ALLOWED_HOSTS`` SSRF guard), retrieves the
        XBRL bytes, and passes them to ``xbrl.parse_xbrl()``.

        SSRF prevention is delegated to the existing ``NseSession.get_with_retry``
        implementation: only hosts in ``ALLOWED_HOSTS`` (``www.nseindia.com``
        and ``nsearchives.nseindia.com``) are permitted.

        Parameters
        ----------
        xbrl_url : str
            Full URL of the XBRL file on the NSE archives server
            (e.g., ``"https://nsearchives.nseindia.com/corporate/xbrl/RELIANCE.xml"``).
            Must point to an ``ALLOWED_HOSTS`` host; any other host will
            raise ``NseError`` from the session layer.

        Returns
        -------
        ParseResult
            Parsed shareholding data with symbol, as_on_date, and rows.

        Raises
        ------
        NseAPIError
            If the download request fails (HTTP 4xx/5xx).
        NseParseError
            If the XBRL bytes cannot be parsed or the expected namespace
            is not found.
        NseRateLimitError
            If rate limiting is detected.
        NseCookieError
            If the NSE session cookie is expired.

        Examples
        --------
        >>> collector = ShareholdingCollector()
        >>> holdings = collector.fetch_shareholding("RELIANCE")
        >>> result = collector.fetch_xbrl_detail(holdings[0].xbrl_url)
        >>> print(result.symbol, result.as_on_date, len(result.rows))
        RELIANCE 2025-12-31 128
        """
        # 事前バリデーション（多層防御）
        if not xbrl_url or not xbrl_url.strip():
            raise ValueError("xbrl_url must not be empty")
        parsed = urlparse(xbrl_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"xbrl_url scheme must be http/https, got '{parsed.scheme}'"
            )
        # ALLOWED_HOSTS チェックは NseSession 層に委譲

        logger.info(
            "Fetching XBRL detail",
            xbrl_url=xbrl_url,
        )

        session, should_close = self._get_session()
        try:
            response = session.get_with_retry(xbrl_url)
            xml_bytes: bytes = response.content
            result = parse_xbrl(xml_bytes)

            logger.info(
                "XBRL detail fetched and parsed",
                symbol=result.symbol,
                as_on_date=result.as_on_date,
                row_count=len(result.rows),
            )

            return result
        finally:
            if should_close:
                session.close()


__all__ = ["ShareholdingCollector"]
