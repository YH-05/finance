"""Type definitions for the market.nse module.

This module provides type definitions for NSE data retrieval including:

- Enum types (NseIndex)
- Configuration dataclasses (NseConfig)
- Data record dataclasses (StockQuote, IndexConstituent, FinancialResult)

All Enums inherit from ``str`` and ``Enum`` so they can be used directly as
string values in API query parameters. All dataclasses use ``frozen=True``
to ensure immutability.

Notes
-----
``RetryConfig`` is re-exported from ``market.retry`` to provide a single
import point for callers of this module.

See Also
--------
market.nse.constants : Default values referenced by NseConfig.
market.bse.types : Similar type-definition pattern for the BSE module.
market.retry : Shared RetryConfig (canonical definition).
"""

from dataclasses import dataclass
from enum import Enum

from market.nse.constants import (
    COOKIE_REFRESH_INTERVAL,
    DEFAULT_DELAY_JITTER,
    DEFAULT_POLITE_DELAY,
    DEFAULT_TIMEOUT,
)
from market.retry import RetryConfig

# =============================================================================
# Enum Definitions
# =============================================================================


class NseIndex(str, Enum):
    """NSE index names for market data retrieval.

    Contains the major NSE indices used for market tracking
    and benchmarking. Values match the ``index`` query parameter
    accepted by the NSE ``/api/equity-stockIndices`` endpoint.

    Parameters
    ----------
    value : str
        The NSE index identifier as used in API requests.

    Examples
    --------
    >>> NseIndex.NIFTY_50
    <NseIndex.NIFTY_50: 'NIFTY 50'>
    >>> str(NseIndex.NIFTY_50)
    'NIFTY 50'
    """

    NIFTY_50 = "NIFTY 50"
    NIFTY_NEXT_50 = "NIFTY NEXT 50"
    NIFTY_100 = "NIFTY 100"
    NIFTY_200 = "NIFTY 200"
    NIFTY_500 = "NIFTY 500"
    NIFTY_MIDCAP_50 = "NIFTY MIDCAP 50"
    NIFTY_MIDCAP_100 = "NIFTY MIDCAP 100"
    NIFTY_SMALLCAP_100 = "NIFTY SMALLCAP 100"
    NIFTY_BANK = "NIFTY BANK"
    NIFTY_IT = "NIFTY IT"
    NIFTY_PHARMA = "NIFTY PHARMA"
    NIFTY_AUTO = "NIFTY AUTO"
    NIFTY_FMCG = "NIFTY FMCG"
    NIFTY_METAL = "NIFTY METAL"
    NIFTY_REALTY = "NIFTY REALTY"


# =============================================================================
# Configuration Dataclasses
# =============================================================================


@dataclass(frozen=True)
class NseConfig:
    """Configuration for NSE API HTTP behaviour.

    Controls polite delays, cookie refresh interval, request timeout,
    and User-Agent rotation. Default values are sourced from
    ``market.nse.constants`` to keep a single source of truth.

    Parameters
    ----------
    polite_delay : float
        Minimum wait time between consecutive requests in seconds
        (default: ``DEFAULT_POLITE_DELAY`` = 0.5).
    delay_jitter : float
        Random jitter added to polite delay in seconds
        (default: ``DEFAULT_DELAY_JITTER`` = 0.1).
    user_agents : tuple[str, ...]
        User-Agent strings for HTTP request rotation. When empty the
        default list from ``constants.DEFAULT_USER_AGENTS`` is used at
        runtime (default: ``()``).
    timeout : float
        HTTP request timeout in seconds
        (default: ``DEFAULT_TIMEOUT`` = 30.0).
    cookie_refresh_interval : float
        Maximum age of the session cookie in seconds before it is
        refreshed by re-visiting ``BASE_URL``
        (default: ``COOKIE_REFRESH_INTERVAL`` = 300.0).

    Raises
    ------
    ValueError
        If any configuration value is outside its valid range.

    Examples
    --------
    >>> config = NseConfig(polite_delay=1.0, timeout=60.0)
    >>> config.polite_delay
    1.0
    """

    polite_delay: float = DEFAULT_POLITE_DELAY
    delay_jitter: float = DEFAULT_DELAY_JITTER
    user_agents: tuple[str, ...] = ()
    timeout: float = DEFAULT_TIMEOUT
    cookie_refresh_interval: float = COOKIE_REFRESH_INTERVAL

    def __post_init__(self) -> None:
        """Validate configuration value ranges.

        Raises
        ------
        ValueError
            If any configuration value is outside its valid range.
        """
        if not (1.0 <= self.timeout <= 300.0):
            raise ValueError(
                f"timeout must be between 1.0 and 300.0, got {self.timeout}"
            )
        if not (0.0 <= self.polite_delay <= 60.0):
            raise ValueError(
                f"polite_delay must be between 0.0 and 60.0, got {self.polite_delay}"
            )
        if not (0.0 <= self.delay_jitter <= 30.0):
            raise ValueError(
                f"delay_jitter must be between 0.0 and 30.0, got {self.delay_jitter}"
            )
        if not (10.0 <= self.cookie_refresh_interval <= 3600.0):
            raise ValueError(
                f"cookie_refresh_interval must be between 10.0 and 3600.0, "
                f"got {self.cookie_refresh_interval}"
            )


# AIDEV-NOTE: RetryConfig is defined in market.retry and re-exported here for
# caller convenience. Do not duplicate the class definition.

# =============================================================================
# Data Record Dataclasses
# =============================================================================


@dataclass(frozen=True)
class StockQuote:
    """A single stock quote from NSE equity market.

    Stores quote data for an NSE-listed security including price,
    volume, and identification information.

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).
    company_name : str
        Company name (e.g. ``"Reliance Industries Limited"``).
    series : str
        Trading series (e.g. ``"EQ"`` for equity).
    open : str
        Opening price (e.g. ``"2450.00"``).
    high : str
        Day's high price (e.g. ``"2480.50"``).
    low : str
        Day's low price (e.g. ``"2440.00"``).
    last_price : str
        Last traded price (e.g. ``"2470.25"``).
    prev_close : str
        Previous day's closing price (e.g. ``"2445.00"``).
    change : str
        Price change from previous close (e.g. ``"25.25"``).
    pct_change : str
        Percentage change from previous close (e.g. ``"1.03"``).
    total_traded_volume : str
        Total traded volume in shares (e.g. ``"5000000"``).
    total_traded_value : str
        Total traded value in INR (e.g. ``"12345678900.00"``).

    Examples
    --------
    >>> quote = StockQuote(
    ...     symbol="RELIANCE",
    ...     company_name="Reliance Industries Limited",
    ...     series="EQ",
    ...     open="2450.00",
    ...     high="2480.50",
    ...     low="2440.00",
    ...     last_price="2470.25",
    ...     prev_close="2445.00",
    ...     change="25.25",
    ...     pct_change="1.03",
    ...     total_traded_volume="5000000",
    ...     total_traded_value="12345678900.00",
    ... )
    >>> quote.symbol
    'RELIANCE'
    """

    symbol: str
    company_name: str
    series: str
    open: str
    high: str
    low: str
    last_price: str
    prev_close: str
    change: str
    pct_change: str
    total_traded_volume: str
    total_traded_value: str


@dataclass(frozen=True)
class IndexConstituent:
    """A single constituent stock within an NSE index.

    Stores price and volume data for one stock that is a member of
    an NSE index (e.g. NIFTY 50).

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).
    series : str
        Trading series (e.g. ``"EQ"``).
    open : str
        Opening price (e.g. ``"2450.00"``).
    day_high : str
        Day's high price (e.g. ``"2480.50"``).
    day_low : str
        Day's low price (e.g. ``"2440.00"``).
    last_price : str
        Last traded price (e.g. ``"2470.25"``).
    prev_close : str
        Previous day's closing price (e.g. ``"2445.00"``).
    change : str
        Price change from previous close (e.g. ``"25.25"``).
    pct_change : str
        Percentage change from previous close (e.g. ``"1.03"``).
    total_traded_volume : str
        Total traded volume in shares (e.g. ``"5000000"``).
    total_traded_value : str
        Total traded value in INR (e.g. ``"12345678900.00"``).
    year_high : str
        52-week high price (e.g. ``"2900.00"``).
    year_low : str
        52-week low price (e.g. ``"2100.00"``).

    Examples
    --------
    >>> constituent = IndexConstituent(
    ...     symbol="RELIANCE",
    ...     series="EQ",
    ...     open="2450.00",
    ...     day_high="2480.50",
    ...     day_low="2440.00",
    ...     last_price="2470.25",
    ...     prev_close="2445.00",
    ...     change="25.25",
    ...     pct_change="1.03",
    ...     total_traded_volume="5000000",
    ...     total_traded_value="12345678900.00",
    ...     year_high="2900.00",
    ...     year_low="2100.00",
    ... )
    >>> constituent.symbol
    'RELIANCE'
    """

    symbol: str
    series: str
    open: str
    day_high: str
    day_low: str
    last_price: str
    prev_close: str
    change: str
    pct_change: str
    total_traded_volume: str
    total_traded_value: str
    year_high: str
    year_low: str


@dataclass(frozen=True)
class CorporateEvent:
    """A corporate event from the NSE event calendar.

    Stores one entry from the NSE ``/api/event-calendar`` response.

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).
    company_name : str
        Company name (e.g. ``"Reliance Industries Limited"``).
    purpose : str
        Event purpose / category (e.g. ``"Dividend"``, ``"Board Meeting"``).
    date : str
        Event date string as returned by the API (e.g. ``"03-Apr-2026"``).
    description : str
        Detailed description of the event (``bm_desc`` field).

    Examples
    --------
    >>> event = CorporateEvent(
    ...     symbol="RELIANCE",
    ...     company_name="Reliance Industries Limited",
    ...     purpose="Dividend",
    ...     date="03-Apr-2026",
    ...     description="Board Meeting to consider dividend.",
    ... )
    >>> event.symbol
    'RELIANCE'
    """

    symbol: str
    company_name: str
    purpose: str
    date: str
    description: str


@dataclass(frozen=True)
class MarketStatus:
    """Market status for a single market segment from NSE.

    Stores one entry from the NSE ``/api/marketStatus`` response.

    Parameters
    ----------
    market : str
        Market segment name (e.g. ``"Capital Market"``, ``"Derivatives"``).
    market_status : str
        Status string (e.g. ``"Open"``, ``"Close"``).
    trade_date : str
        Trading date string (e.g. ``"02-Apr-2026"``).
    index : str
        Benchmark index name (e.g. ``"NIFTY 50"``).
    last : str
        Last traded index value (e.g. ``"22371.80"``).
    variation : str
        Change from previous close (e.g. ``"-307.60"``).
    pct_change : str
        Percentage change from previous close (e.g. ``"-1.36"``).

    Examples
    --------
    >>> ms = MarketStatus(
    ...     market="Capital Market",
    ...     market_status="Open",
    ...     trade_date="02-Apr-2026",
    ...     index="NIFTY 50",
    ...     last="22371.80",
    ...     variation="-307.60",
    ...     pct_change="-1.36",
    ... )
    >>> ms.market
    'Capital Market'
    """

    market: str
    market_status: str
    trade_date: str
    index: str
    last: str
    variation: str
    pct_change: str


@dataclass(frozen=True)
class FinancialResult:
    """A financial result record from NSE corporate filings.

    Stores quarterly or annual financial result data for an
    NSE-listed company.

    Parameters
    ----------
    symbol : str
        NSE stock symbol.
    from_date : str
        Financial period start date (e.g. ``"01-Jan-2025"``).
    to_date : str
        Financial period end date (e.g. ``"31-Mar-2025"``).
    income : str
        Total income/revenue (e.g. ``"250000"`` in Cr).
    profit_after_tax : str
        Net profit after tax (e.g. ``"18500"`` in Cr).
    eps : str
        Earnings per share (e.g. ``"27.35"``).
    result_type : str
        Report type, e.g. ``"Standalone"`` or ``"Consolidated"``.
    broadcast_date : str
        Date results were broadcast/published (e.g. ``"30-Apr-2025"``).

    Examples
    --------
    >>> result = FinancialResult(
    ...     symbol="RELIANCE",
    ...     from_date="01-Jan-2025",
    ...     to_date="31-Mar-2025",
    ...     income="250000",
    ...     profit_after_tax="18500",
    ...     eps="27.35",
    ...     result_type="Consolidated",
    ...     broadcast_date="30-Apr-2025",
    ... )
    >>> result.symbol
    'RELIANCE'
    """

    symbol: str
    from_date: str
    to_date: str
    income: str
    profit_after_tax: str
    eps: str
    result_type: str
    broadcast_date: str


@dataclass(frozen=True)
class ShareholdingPattern:
    """Shareholding pattern record from NSE NextApi getShareholdingPattern.

    Stores shareholding breakdown (promoter/public) for an NSE-listed
    company at a specific quarterly date.  The NSE NextApi only provides
    promoter and public categories; FII/DII breakdown is not available
    from this endpoint.

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).  Not present in the API
        response; set from the request parameter.
    date : str
        Reporting date string used as the dict key in the API response
        (e.g. ``"31-Dec-2025"``).
    ndsid : str
        Internal NSE data-source identifier (e.g. ``"207095"``).
    series : str
        Equity series identifier (typically ``"equity"``).
    total : str
        Total holding percentage (typically ``"100.00"``).
    promoter_group : str
        Promoter & promoter group holding percentage (e.g. ``"50.01"``).
        Empty string when the company has no promoter holding
        (e.g. HDFCBANK).
    public : str
        Public / retail holding percentage (e.g. ``"49.99"``).

    Examples
    --------
    >>> pattern = ShareholdingPattern(
    ...     symbol="RELIANCE",
    ...     date="31-Dec-2025",
    ...     ndsid="207095",
    ...     series="equity",
    ...     total="100.00",
    ...     promoter_group="50.01",
    ...     public="49.99",
    ... )
    >>> pattern.symbol
    'RELIANCE'
    >>> pattern.promoter_group
    '50.01'
    """

    symbol: str
    date: str
    ndsid: str
    series: str = "equity"
    total: str = "100.00"
    promoter_group: str = ""
    public: str = ""


@dataclass(frozen=True)
class CorporateShareHolding:
    """Corporate share holding record from NSE XBRL shareholding filings.

    Stores shareholding breakdown for an NSE-listed company derived from the
    ``/api/corporate-share-holdings-master`` endpoint.  Numeric percentage
    fields are stored as strings to accommodate both float-formatted and
    non-numeric API responses (HF1: float/str dual compatibility).

    Use the ``to_float_*()`` accessor methods to obtain numeric values;
    they return ``None`` when the underlying string is empty or non-numeric.

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).
    as_on_date : str
        Reporting date string (e.g. ``"31-Dec-2025"``).
    promoter_group_pct : str
        Promoter & promoter group holding percentage string
        (e.g. ``"50.01"``).  Empty string when no promoter holding.
    public_pct : str
        Public / institutional holding percentage string
        (e.g. ``"49.99"``).
    employee_trust_pct : str
        Employee welfare trust holding percentage string
        (e.g. ``"0.05"``).  Defaults to ``""`` when not present.
    submission_date : str
        Filing submission date string (e.g. ``"15-Jan-2026"``).
        Defaults to ``""`` when not available.
    broadcast_date : str
        Date the filing was broadcast on the exchange
        (e.g. ``"16-Jan-2026"``).  Defaults to ``""`` when not available.
    xbrl_url : str
        URL of the raw XBRL filing on NSE archives
        (e.g. ``"https://archives.nseindia.com/...xml"``).
        Defaults to ``""`` when not available.

    Examples
    --------
    >>> holding = CorporateShareHolding(
    ...     symbol="RELIANCE",
    ...     as_on_date="31-Dec-2025",
    ...     promoter_group_pct="50.01",
    ...     public_pct="49.99",
    ... )
    >>> holding.symbol
    'RELIANCE'
    >>> holding.to_float_promoter_group_pct()
    50.01
    >>> empty = CorporateShareHolding(
    ...     symbol="HDFCBANK",
    ...     as_on_date="31-Dec-2025",
    ...     promoter_group_pct="",
    ...     public_pct="100.00",
    ... )
    >>> empty.to_float_promoter_group_pct() is None
    True
    """

    symbol: str
    as_on_date: str
    promoter_group_pct: str
    public_pct: str
    employee_trust_pct: str = ""
    submission_date: str = ""
    broadcast_date: str = ""
    xbrl_url: str = ""

    def to_float_promoter_group_pct(self) -> float | None:
        """Return promoter_group_pct as float, or None on failure.

        Returns
        -------
        float | None
            Parsed float value, or ``None`` if the field is empty or
            cannot be converted (e.g. ``"N/A"``, ``"-"``).

        Examples
        --------
        >>> CorporateShareHolding(
        ...     symbol="R", as_on_date="d", promoter_group_pct="50.01", public_pct="49.99"
        ... ).to_float_promoter_group_pct()
        50.01
        """
        try:
            return float(self.promoter_group_pct)
        except (ValueError, TypeError):
            return None

    def to_float_public_pct(self) -> float | None:
        """Return public_pct as float, or None on failure.

        Returns
        -------
        float | None
            Parsed float value, or ``None`` if the field is empty or
            cannot be converted.

        Examples
        --------
        >>> CorporateShareHolding(
        ...     symbol="R", as_on_date="d", promoter_group_pct="50.01", public_pct="49.99"
        ... ).to_float_public_pct()
        49.99
        """
        try:
            return float(self.public_pct)
        except (ValueError, TypeError):
            return None

    def to_float_employee_trust_pct(self) -> float | None:
        """Return employee_trust_pct as float, or None on failure.

        Returns
        -------
        float | None
            Parsed float value, or ``None`` if the field is empty or
            cannot be converted.

        Examples
        --------
        >>> CorporateShareHolding(
        ...     symbol="R", as_on_date="d", promoter_group_pct="50.00",
        ...     public_pct="49.95", employee_trust_pct="0.05"
        ... ).to_float_employee_trust_pct()
        0.05
        """
        try:
            return float(self.employee_trust_pct)
        except (ValueError, TypeError):
            return None

    def to_normalized_pcts(
        self,
    ) -> tuple[float | None, float | None, float | None, str]:
        """Return promoter / public / employee_trust pct in normalised % form.

        The NSE corporate-share-holdings-master API is usually consistent at
        percentage form (``67.29`` for 67.29 %), but empirically returns
        percent×100 form (``6729``) for a small subset of filings. This
        method detects the storage format from the sum of the three fields
        and auto-scales to percentage form so downstream callers can apply
        a uniform ``[0, 100]`` range check.

        Detection rules (sum = promoter + public + employee_trust):

        - ``sum ≈ 100`` (range 99.0 – 101.0): already percentage form,
          returned as-is with ``source_format = "percent"``.
        - ``sum ≈ 10000`` (range 9900 – 10100): percent×100 form; all
          three values divided by 100 with ``source_format = "x100"``.
        - ``sum ≈ 1`` (range 0.95 – 1.05): ratio form (0-1); all three
          multiplied by 100 with ``source_format = "ratio"``.
        - Otherwise: returned unchanged with
          ``source_format = "unknown"`` so callers can reject the record.

        Returns
        -------
        tuple[float | None, float | None, float | None, str]
            ``(promoter_pct, public_pct, employee_trust_pct, source_format)``.
            Individual fields remain ``None`` if the underlying raw field
            was not parseable as float.

        Examples
        --------
        >>> # Normal percentage-form response
        >>> h = CorporateShareHolding(
        ...     symbol="R", as_on_date="d",
        ...     promoter_group_pct="67.29", public_pct="32.71",
        ... )
        >>> h.to_normalized_pcts()
        (67.29, 32.71, None, 'percent')

        >>> # Buggy percent×100 response (empirically seen for CHENNPETRO)
        >>> h = CorporateShareHolding(
        ...     symbol="R", as_on_date="d",
        ...     promoter_group_pct="6729.0", public_pct="3271.0",
        ...     employee_trust_pct="0.0",
        ... )
        >>> h.to_normalized_pcts()
        (67.29, 32.71, 0.0, 'x100')
        """
        promoter = self.to_float_promoter_group_pct()
        public = self.to_float_public_pct()
        trust = self.to_float_employee_trust_pct()
        return _normalize_shareholding_pcts(promoter, public, trust)


def _normalize_shareholding_pcts(
    promoter: float | None,
    public: float | None,
    trust: float | None,
) -> tuple[float | None, float | None, float | None, str]:
    """Normalise promoter / public / employee_trust pct values to percentage form.

    See :meth:`CorporateShareHolding.to_normalized_pcts` for the detection
    rules and worked examples. Exposed as a module-level helper so
    downstream code (notebooks, ETL scripts) can apply the same
    normalisation to arbitrary triples without constructing a dataclass.
    """
    vals = [v for v in (promoter, public, trust) if v is not None]
    if not vals:
        return promoter, public, trust, "empty"

    total = sum(vals)

    # Already in percentage form; no scaling required.
    if 99.0 <= total <= 101.0:
        return promoter, public, trust, "percent"

    # Percent × 100 form: divide by 100.
    if 9900.0 <= total <= 10100.0:
        scale = 1.0 / 100.0
        fmt = "x100"
    # Ratio form (0-1): multiply by 100.
    elif 0.95 <= total <= 1.05:
        scale = 100.0
        fmt = "ratio"
    else:
        # Unknown format; leave untouched so callers can reject the record.
        return promoter, public, trust, "unknown"

    return (
        promoter * scale if promoter is not None else None,
        public * scale if public is not None else None,
        trust * scale if trust is not None else None,
        fmt,
    )


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "CorporateEvent",
    "CorporateShareHolding",
    "FinancialResult",
    "IndexConstituent",
    "MarketStatus",
    "NseConfig",
    "NseIndex",
    "RetryConfig",
    "ShareholdingPattern",
    "StockQuote",
]
