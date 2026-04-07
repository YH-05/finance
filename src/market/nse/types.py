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
    """Shareholding pattern record from NSE corporate filings.

    Stores shareholding breakdown by investor category for an
    NSE-listed company at a specific quarterly date.

    Parameters
    ----------
    symbol : str
        NSE stock symbol (e.g. ``"RELIANCE"``).
    date : str
        Reporting date string as returned by the API (e.g. ``"31-Dec-2024"``).
    promoter_group : str
        Promoter & promoter group holding percentage (e.g. ``"50.30"``).
    fii : str
        Foreign Institutional Investors holding percentage (e.g. ``"23.45"``).
    dii : str
        Domestic Institutional Investors holding percentage (e.g. ``"12.10"``).
    public : str
        Public / retail holding percentage (e.g. ``"14.15"``).

    Examples
    --------
    >>> pattern = ShareholdingPattern(
    ...     symbol="RELIANCE",
    ...     date="31-Dec-2024",
    ...     promoter_group="50.30",
    ...     fii="23.45",
    ...     dii="12.10",
    ...     public="14.15",
    ... )
    >>> pattern.symbol
    'RELIANCE'
    >>> pattern.promoter_group
    '50.30'
    """

    symbol: str
    date: str
    promoter_group: str
    fii: str
    dii: str
    public: str


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "CorporateEvent",
    "FinancialResult",
    "IndexConstituent",
    "MarketStatus",
    "NseConfig",
    "NseIndex",
    "RetryConfig",
    "ShareholdingPattern",
    "StockQuote",
]
