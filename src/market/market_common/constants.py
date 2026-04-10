"""Constants for market common foundation module.

This module defines all shared constants used across market
sub-packages (SGX, Bursa, SET, IDX, HOSE, PSE, NSE, BSE), including:

1. MarketExchange Enum (ASEAN + India exchanges)
2. YFINANCE_SUFFIX_MAP (yfinance ticker suffixes per market)
3. SCREENER_EXCHANGE_MAP (tradingview-screener exchange names)
4. SCREENER_MARKET_MAP (tradingview-screener market/country names)
5. TABLE_TICKERS (DuckDB table name for ticker master)
6. DB_PATH (DuckDB database file path)

Notes
-----
All non-enum constants use ``typing.Final`` type annotations to prevent
reassignment. The ``__all__`` list exports all public constants.

See Also
--------
market.bse.constants : Similar constant pattern used by the BSE module.
"""

from enum import Enum
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# 1. MarketExchange Enum
# ---------------------------------------------------------------------------


class MarketExchange(str, Enum):
    """Stock exchange identifiers for ASEAN and India markets.

    Represents the 6 major ASEAN stock exchanges and 2 India exchanges
    covered by this package. Inherits from ``str`` so members can be
    used directly as string values.

    Parameters
    ----------
    value : str
        The exchange identifier string.

    Examples
    --------
    >>> MarketExchange.SGX
    <MarketExchange.SGX: 'SGX'>
    >>> str(MarketExchange.SGX)
    'SGX'
    >>> MarketExchange.NSE
    <MarketExchange.NSE: 'NSE'>
    """

    SGX = "SGX"
    """Singapore Exchange."""

    BURSA = "BURSA"
    """Bursa Malaysia."""

    SET = "SET"
    """Stock Exchange of Thailand."""

    IDX = "IDX"
    """Indonesia Stock Exchange."""

    HOSE = "HOSE"
    """Ho Chi Minh Stock Exchange (Vietnam)."""

    PSE = "PSE"
    """Philippine Stock Exchange."""

    NSE = "NSE"
    """National Stock Exchange of India (primary India data source)."""

    BSE = "BSE"
    """Bombay Stock Exchange (enum member; implementation deferred due to geo-block)."""


# ---------------------------------------------------------------------------
# 2. yfinance suffix mapping
# ---------------------------------------------------------------------------

YFINANCE_SUFFIX_MAP: Final[dict[MarketExchange, str]] = {
    MarketExchange.SGX: ".SI",
    MarketExchange.BURSA: ".KL",
    MarketExchange.SET: ".BK",
    MarketExchange.IDX: ".JK",
    MarketExchange.HOSE: ".VN",
    MarketExchange.PSE: ".PS",
    MarketExchange.NSE: ".NS",
    MarketExchange.BSE: ".BO",
}
"""Mapping from MarketExchange to yfinance ticker suffix.

Each exchange has a specific suffix used by yfinance to identify the
exchange. For example, DBS Group (SGX) is ``D05.SI``, Maybank (Bursa)
is ``1155.KL``, and Reliance Industries (NSE) is ``RELIANCE.NS``.

Examples
--------
>>> YFINANCE_SUFFIX_MAP[MarketExchange.SGX]
'.SI'
>>> YFINANCE_SUFFIX_MAP[MarketExchange.BURSA]
'.KL'
>>> YFINANCE_SUFFIX_MAP[MarketExchange.NSE]
'.NS'
>>> YFINANCE_SUFFIX_MAP[MarketExchange.BSE]
'.BO'
"""

# ---------------------------------------------------------------------------
# 3. tradingview-screener exchange mapping
# ---------------------------------------------------------------------------

SCREENER_EXCHANGE_MAP: Final[dict[MarketExchange, str]] = {
    MarketExchange.SGX: "SGX",
    MarketExchange.BURSA: "MYX",
    MarketExchange.SET: "SET",
    MarketExchange.IDX: "IDX",
    MarketExchange.HOSE: "HOSE",
    MarketExchange.PSE: "PSE",
    MarketExchange.NSE: "NSE",
}
"""Mapping from MarketExchange to tradingview-screener exchange name.

The tradingview-screener library uses exchange names that may
differ from the standard MarketExchange identifiers. For example,
Bursa Malaysia is ``MYX`` in tradingview-screener.

Notes
-----
BSE is intentionally excluded from this map as its implementation is
deferred. NSE is the primary India data source.

For India (NSE), use ``Query.set_markets("india").where(col("exchange") == "NSE")``
to avoid duplicates between NSE and BSE listings.

Examples
--------
>>> SCREENER_EXCHANGE_MAP[MarketExchange.BURSA]
'MYX'
>>> SCREENER_EXCHANGE_MAP[MarketExchange.NSE]
'NSE'
"""

# ---------------------------------------------------------------------------
# 4. tradingview-screener market (country) mapping
# ---------------------------------------------------------------------------

SCREENER_MARKET_MAP: Final[dict[MarketExchange, str]] = {
    MarketExchange.SGX: "singapore",
    MarketExchange.BURSA: "malaysia",
    MarketExchange.SET: "thailand",
    MarketExchange.IDX: "indonesia",
    MarketExchange.HOSE: "vietnam",
    MarketExchange.PSE: "philippines",
    MarketExchange.NSE: "india",
}
"""Mapping from MarketExchange to tradingview-screener market/country name.

The tradingview-screener ``Query.set_markets()`` method accepts
country/market names (lowercase) rather than exchange codes.
For example, Bursa Malaysia uses ``"malaysia"`` as the market name.

Notes
-----
NSE maps to ``"india"`` (same as BSE). To avoid duplicate listings
when both NSE and BSE-listed stocks appear, apply an exchange filter:
``Query.set_markets("india").where(Column("exchange") == "NSE")``.
BSE is intentionally excluded from this map (implementation deferred).

Examples
--------
>>> SCREENER_MARKET_MAP[MarketExchange.BURSA]
'malaysia'
>>> SCREENER_MARKET_MAP[MarketExchange.SGX]
'singapore'
>>> SCREENER_MARKET_MAP[MarketExchange.NSE]
'india'
"""

# ---------------------------------------------------------------------------
# 5. DuckDB table name
# ---------------------------------------------------------------------------

TABLE_TICKERS: Final[str] = "asean_tickers"
"""DuckDB table name for the ASEAN ticker master.

Stores all ASEAN exchange-listed tickers with metadata
(name, sector, industry, market cap, currency, active status).
"""

# ---------------------------------------------------------------------------
# 6. DuckDB database path
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
"""Project root directory resolved from this file's location.

constants.py -> market_common/ -> market/ -> src/ -> project root.
"""

DB_PATH: Final[Path] = _PROJECT_ROOT / "data" / "processed" / "asean.duckdb"
"""Absolute path to the ASEAN DuckDB database file.

Resolved from the project root so the path is stable regardless of
the current working directory. Follows the project convention of
``data/processed/<domain>.duckdb``.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "DB_PATH",
    "SCREENER_EXCHANGE_MAP",
    "SCREENER_MARKET_MAP",
    "TABLE_TICKERS",
    "YFINANCE_SUFFIX_MAP",
    "MarketExchange",
]
