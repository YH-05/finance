"""Type definitions for the market.nasdaq module.

This module provides type definitions for the NASDAQ Stock Screener including:

- Filter Enums (Exchange, MarketCap, Sector, Recommendation, Region, Country)
- Configuration dataclasses (NasdaqConfig, RetryConfig)
- Filter dataclass with query parameter conversion (ScreenerFilter)
- Data record type for raw API response rows (StockRecord)
- FilterCategory type alias

All Enums inherit from ``str`` and ``Enum`` so they can be used directly as
string values in API query parameters.  All dataclasses use ``frozen=True``
to ensure immutability.

See Also
--------
market.nasdaq.constants : Default values referenced by NasdaqConfig.
market.etfcom.types : Similar type-definition pattern for the ETF.com module.
"""

from dataclasses import dataclass
from enum import Enum

from market.nasdaq.constants import (
    DEFAULT_DELAY_JITTER,
    DEFAULT_POLITE_DELAY,
    DEFAULT_TIMEOUT,
)

# =============================================================================
# Enum Definitions
# =============================================================================


class Exchange(str, Enum):
    """Stock exchange filter for the NASDAQ Screener API.

    Parameters
    ----------
    value : str
        The API query parameter value for the exchange filter.

    Examples
    --------
    >>> Exchange.NASDAQ
    <Exchange.NASDAQ: 'nasdaq'>
    >>> str(Exchange.NASDAQ)
    'nasdaq'
    """

    NASDAQ = "nasdaq"
    NYSE = "nyse"
    AMEX = "amex"


class MarketCap(str, Enum):
    """Market capitalisation filter for the NASDAQ Screener API.

    Categories follow NASDAQ's classification:
    - MEGA: $200B+
    - LARGE: $10B-$200B
    - MID: $2B-$10B
    - SMALL: $300M-$2B
    - MICRO: $50M-$300M
    - NANO: <$50M

    Parameters
    ----------
    value : str
        The API query parameter value for the market cap filter.

    Examples
    --------
    >>> MarketCap.MEGA
    <MarketCap.MEGA: 'mega'>
    """

    MEGA = "mega"
    LARGE = "large"
    MID = "mid"
    SMALL = "small"
    MICRO = "micro"
    NANO = "nano"


class Sector(str, Enum):
    """Sector filter for the NASDAQ Screener API.

    Covers all 11 sectors available on the NASDAQ Stock Screener.

    Parameters
    ----------
    value : str
        The API query parameter value for the sector filter.

    Examples
    --------
    >>> Sector.TECHNOLOGY
    <Sector.TECHNOLOGY: 'technology'>
    """

    TECHNOLOGY = "technology"
    TELECOMMUNICATIONS = "telecommunications"
    HEALTH_CARE = "health_care"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    BASIC_MATERIALS = "basic_materials"
    ENERGY = "energy"
    UTILITIES = "utilities"


class Recommendation(str, Enum):
    """Analyst recommendation filter for the NASDAQ Screener API.

    Parameters
    ----------
    value : str
        The API query parameter value for the recommendation filter.

    Examples
    --------
    >>> Recommendation.STRONG_BUY
    <Recommendation.STRONG_BUY: 'strong_buy'>
    """

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Region(str, Enum):
    """Geographic region filter for the NASDAQ Screener API.

    Covers all 8 regions available on the NASDAQ Stock Screener.

    Parameters
    ----------
    value : str
        The API query parameter value for the region filter.

    Examples
    --------
    >>> Region.NORTH_AMERICA
    <Region.NORTH_AMERICA: 'north_america'>
    """

    AFRICA = "africa"
    ASIA = "asia"
    AUSTRALIA_AND_SOUTH_PACIFIC = "australia_and_south_pacific"
    CARIBBEAN = "caribbean"
    EUROPE = "europe"
    MIDDLE_EAST = "middle_east"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"


class Country(str, Enum):
    """Country filter for the NASDAQ Screener API.

    Contains a representative subset of the 40+ countries available on the
    NASDAQ Stock Screener.  Since NASDAQ supports many countries whose list
    may change, the ``ScreenerFilter.country`` field accepts ``str`` directly
    as well, allowing values not listed in this Enum.

    Parameters
    ----------
    value : str
        The API query parameter value for the country filter.

    Examples
    --------
    >>> Country.USA
    <Country.USA: 'united_states'>
    """

    USA = "united_states"
    CANADA = "canada"
    JAPAN = "japan"
    GERMANY = "germany"
    UK = "united_kingdom"
    FRANCE = "france"
    CHINA = "china"
    INDIA = "india"
    BRAZIL = "brazil"
    AUSTRALIA = "australia"
    SOUTH_KOREA = "south_korea"
    SWITZERLAND = "switzerland"
    NETHERLANDS = "netherlands"
    ISRAEL = "israel"
    IRELAND = "ireland"
    SINGAPORE = "singapore"
    HONG_KONG = "hong_kong"
    TAIWAN = "taiwan"
    MEXICO = "mexico"
    ARGENTINA = "argentina"


# =============================================================================
# Configuration Dataclasses
# =============================================================================


@dataclass(frozen=True)
class NasdaqConfig:
    """Configuration for NASDAQ Stock Screener HTTP behaviour.

    Controls polite delays, TLS fingerprint impersonation, and request
    timeout.  Default values are sourced from ``market.nasdaq.constants``
    to keep a single source of truth.

    Parameters
    ----------
    polite_delay : float
        Minimum wait time between consecutive requests in seconds
        (default: ``DEFAULT_POLITE_DELAY`` = 1.0).
    delay_jitter : float
        Random jitter added to polite delay in seconds
        (default: ``DEFAULT_DELAY_JITTER`` = 0.5).
    user_agents : tuple[str, ...]
        User-Agent strings for HTTP request rotation.  When empty the
        default list from ``constants.DEFAULT_USER_AGENTS`` is used at
        runtime (default: ``()``).
    impersonate : str
        curl_cffi TLS fingerprint impersonation target
        (default: ``'chrome'``).
    timeout : float
        HTTP request timeout in seconds
        (default: ``DEFAULT_TIMEOUT`` = 30.0).

    Examples
    --------
    >>> config = NasdaqConfig(polite_delay=3.0, impersonate="chrome120")
    >>> config.polite_delay
    3.0
    """

    polite_delay: float = DEFAULT_POLITE_DELAY
    delay_jitter: float = DEFAULT_DELAY_JITTER
    user_agents: tuple[str, ...] = ()
    impersonate: str = "chrome"
    timeout: float = DEFAULT_TIMEOUT

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


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behaviour with exponential backoff.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 3).
    initial_delay : float
        Initial delay between retries in seconds (default: 1.0).
    max_delay : float
        Maximum delay between retries in seconds (default: 30.0).
    exponential_base : float
        Base for exponential backoff calculation (default: 2.0).
    jitter : bool
        Whether to add random jitter to delays (default: True).

    Examples
    --------
    >>> config = RetryConfig(max_attempts=5, initial_delay=0.5)
    >>> config.max_attempts
    5
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        """Validate retry configuration value ranges.

        Raises
        ------
        ValueError
            If max_attempts is outside its valid range.
        """
        if not (1 <= self.max_attempts <= 10):
            raise ValueError(
                f"max_attempts must be between 1 and 10, got {self.max_attempts}"
            )


# =============================================================================
# Filter Dataclass
# =============================================================================


@dataclass(frozen=True)
class ScreenerFilter:
    """Filter conditions for the NASDAQ Stock Screener API.

    Converts filter settings into API query parameters via ``to_params()``.
    Fields set to ``None`` are excluded from the resulting parameter dict.
    The ``country`` field accepts ``str`` directly (not just ``Country`` Enum)
    because NASDAQ supports 40+ countries whose full list may change.

    Parameters
    ----------
    exchange : Exchange | None
        Stock exchange filter (default: None).
    marketcap : MarketCap | None
        Market capitalisation filter (default: None).
    sector : Sector | None
        Sector filter (default: None).
    recommendation : Recommendation | None
        Analyst recommendation filter (default: None).
    region : Region | None
        Geographic region filter (default: None).
    country : str | None
        Country filter as string (default: None).
    limit : int
        Maximum number of records to return.  ``0`` retrieves all
        matching records (default: 0).

    Examples
    --------
    >>> f = ScreenerFilter(exchange=Exchange.NASDAQ, sector=Sector.TECHNOLOGY)
    >>> f.to_params()
    {'exchange': 'nasdaq', 'sector': 'technology', 'limit': '0'}
    """

    exchange: Exchange | None = None
    marketcap: MarketCap | None = None
    sector: Sector | None = None
    recommendation: Recommendation | None = None
    region: Region | None = None
    country: str | None = None
    limit: int = 0

    def to_params(self) -> dict[str, str]:
        """Convert filter settings to API query parameters.

        Returns a dictionary suitable for passing to ``requests.get(params=...)``.
        Only non-``None`` filter fields are included.  The ``limit`` field is
        always included.

        Returns
        -------
        dict[str, str]
            API query parameter dictionary with string keys and values.

        Examples
        --------
        >>> ScreenerFilter().to_params()
        {'limit': '0'}

        >>> ScreenerFilter(exchange=Exchange.NYSE, limit=100).to_params()
        {'exchange': 'nyse', 'limit': '100'}
        """
        params: dict[str, str] = {"limit": str(self.limit)}
        if self.exchange is not None:
            params["exchange"] = self.exchange.value
        if self.marketcap is not None:
            params["marketcap"] = self.marketcap.value
        if self.sector is not None:
            params["sector"] = self.sector.value
        if self.recommendation is not None:
            params["recommendation"] = self.recommendation.value
        if self.region is not None:
            params["region"] = self.region.value
        if self.country is not None:
            params["country"] = self.country
        return params


# =============================================================================
# Data Record Dataclass
# =============================================================================


@dataclass(frozen=True)
class StockRecord:
    """A single stock record from the NASDAQ Screener API response.

    Stores raw string values as returned by the API.  Numeric conversion
    (e.g. stripping ``$`` and ``,`` from ``last_sale`` and ``market_cap``)
    is performed by the parser module, not here.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g. ``"AAPL"``).
    name : str
        Company name (e.g. ``"Apple Inc. Common Stock"``).
    last_sale : str
        Last sale price as displayed (e.g. ``"$227.63"``).
    net_change : str
        Net price change (e.g. ``"-1.95"``).
    pct_change : str
        Percentage price change (e.g. ``"-0.849%"``).
    market_cap : str
        Market capitalisation as displayed (e.g. ``"3,435,123,456,789"``).
    country : str
        Country of incorporation (e.g. ``"United States"``).
    ipo_year : str
        IPO year (e.g. ``"1980"``).
    volume : str
        Trading volume as displayed (e.g. ``"48,123,456"``).
    sector : str
        Sector classification (e.g. ``"Technology"``).
    industry : str
        Industry classification (e.g. ``"Computer Manufacturing"``).
    url : str
        Relative URL path (e.g. ``"/market-activity/stocks/aapl"``).

    Examples
    --------
    >>> record = StockRecord(
    ...     symbol="AAPL",
    ...     name="Apple Inc. Common Stock",
    ...     last_sale="$227.63",
    ...     net_change="-1.95",
    ...     pct_change="-0.849%",
    ...     market_cap="3,435,123,456,789",
    ...     country="United States",
    ...     ipo_year="1980",
    ...     volume="48,123,456",
    ...     sector="Technology",
    ...     industry="Computer Manufacturing",
    ...     url="/market-activity/stocks/aapl",
    ... )
    >>> record.symbol
    'AAPL'
    """

    symbol: str
    name: str
    last_sale: str
    net_change: str
    pct_change: str
    market_cap: str
    country: str
    ipo_year: str
    volume: str
    sector: str
    industry: str
    url: str


# =============================================================================
# Type Aliases
# =============================================================================

type FilterCategory = (
    type[Exchange]
    | type[MarketCap]
    | type[Sector]
    | type[Recommendation]
    | type[Region]
)
"""Type alias for filter category Enum classes.

Used by the collector to iterate over all available filter categories
and generate per-category CSV files.

Examples
--------
>>> categories: list[FilterCategory] = [Exchange, MarketCap, Sector]
"""


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "Country",
    "Exchange",
    "FilterCategory",
    "MarketCap",
    "NasdaqConfig",
    "Recommendation",
    "Region",
    "RetryConfig",
    "ScreenerFilter",
    "Sector",
    "StockRecord",
]
