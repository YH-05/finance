"""Pydantic models for symbols.yaml configuration.

This module defines the Pydantic models for the symbols configuration file,
providing type-safe access to symbol groups and their definitions.

Configuration Hierarchy
-----------------------
- SymbolsConfig (root)
  - IndicesConfig
    - IndexSymbol
  - Mag7Symbol
  - SectorSymbol
  - CommoditySymbol
  - CurrencyPairSymbol
  - SectorStocksConfig
    - SectorStockSymbol
  - ReturnPeriodsConfig

Examples
--------
>>> config = SymbolsConfig(...)
>>> config.get_symbols("mag7")
['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

>>> config.get_symbols("indices", "us")
['^GSPC', '^DJI', '^IXIC', ...]
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from utils_core.logging import get_logger

logger = get_logger(__name__, module="config.models")


class IndexSymbol(BaseModel):
    """Stock index symbol definition.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the index (e.g., "^GSPC", "^DJI").
    name : str
        Human-readable name of the index (e.g., "S&P 500").

    Examples
    --------
    >>> symbol = IndexSymbol(symbol="^GSPC", name="S&P 500")
    >>> symbol.symbol
    '^GSPC'
    """

    symbol: str = Field(..., description="Ticker symbol for the index")
    name: str = Field(..., description="Human-readable name of the index")


class Mag7Symbol(BaseModel):
    """Magnificent 7 stock symbol definition.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the stock (e.g., "AAPL", "MSFT").
    name : str
        Company name (e.g., "Apple", "Microsoft").

    Examples
    --------
    >>> symbol = Mag7Symbol(symbol="AAPL", name="Apple")
    >>> symbol.symbol
    'AAPL'
    """

    symbol: str = Field(..., description="Ticker symbol for the stock")
    name: str = Field(..., description="Company name")


class SectorSymbol(BaseModel):
    """Sector ETF symbol definition.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the sector ETF (e.g., "XLF", "XLK").
    name : str
        Full name of the sector ETF (e.g., "Financial Select Sector SPDR").

    Examples
    --------
    >>> symbol = SectorSymbol(symbol="XLF", name="Financial Select Sector SPDR")
    >>> symbol.symbol
    'XLF'
    """

    symbol: str = Field(..., description="Ticker symbol for the sector ETF")
    name: str = Field(..., description="Full name of the sector ETF")


class CommoditySymbol(BaseModel):
    """Commodity futures symbol definition.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the commodity futures (e.g., "GC=F", "CL=F").
    name : str
        Name of the commodity (e.g., "Gold Futures", "WTI Crude Oil Futures").

    Examples
    --------
    >>> symbol = CommoditySymbol(symbol="GC=F", name="Gold Futures")
    >>> symbol.symbol
    'GC=F'
    """

    symbol: str = Field(..., description="Ticker symbol for the commodity futures")
    name: str = Field(..., description="Name of the commodity")


class CurrencyPairSymbol(BaseModel):
    """Currency pair symbol definition.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the currency pair (e.g., "USDJPY=X").
    name : str
        Human-readable name of the pair (e.g., "米ドル/円").

    Examples
    --------
    >>> symbol = CurrencyPairSymbol(symbol="USDJPY=X", name="米ドル/円")
    >>> symbol.symbol
    'USDJPY=X'
    """

    symbol: str = Field(..., description="Ticker symbol for the currency pair")
    name: str = Field(..., description="Human-readable name of the pair")


class SectorStockSymbol(BaseModel):
    """Individual stock within a sector.

    Parameters
    ----------
    symbol : str
        Ticker symbol for the stock (e.g., "JPM", "BAC").
    name : str
        Company name (e.g., "JPMorgan Chase").
    sector : str
        Sector name (e.g., "Financial").

    Examples
    --------
    >>> symbol = SectorStockSymbol(
    ...     symbol="JPM",
    ...     name="JPMorgan Chase",
    ...     sector="Financial",
    ... )
    >>> symbol.sector
    'Financial'
    """

    symbol: str = Field(..., description="Ticker symbol for the stock")
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector name")


class IndicesConfig(BaseModel):
    """Configuration for stock indices.

    Parameters
    ----------
    us : list[IndexSymbol]
        List of US stock indices.
    global_ : list[IndexSymbol]
        List of global stock indices (aliased from 'global' in YAML).

    Examples
    --------
    >>> config = IndicesConfig(
    ...     us=[IndexSymbol(symbol="^GSPC", name="S&P 500")],
    ...     global_=[IndexSymbol(symbol="^N225", name="日経225")],
    ... )
    >>> len(config.us)
    1
    """

    model_config = ConfigDict(populate_by_name=True)

    us: list[IndexSymbol] = Field(
        default_factory=list,
        description="List of US stock indices",
    )
    global_: list[IndexSymbol] = Field(
        default_factory=list,
        alias="global",
        description="List of global stock indices",
    )


class SectorStocksConfig(BaseModel):
    """Configuration for sector representative stocks.

    Each field represents stocks in a specific sector ETF.

    Parameters
    ----------
    XLF : list[SectorStockSymbol]
        Financial sector stocks.
    XLK : list[SectorStockSymbol]
        Technology sector stocks.
    XLV : list[SectorStockSymbol]
        Health Care sector stocks.
    XLE : list[SectorStockSymbol]
        Energy sector stocks.
    XLI : list[SectorStockSymbol]
        Industrial sector stocks.
    XLY : list[SectorStockSymbol]
        Consumer Discretionary sector stocks.
    XLP : list[SectorStockSymbol]
        Consumer Staples sector stocks.
    XLB : list[SectorStockSymbol]
        Materials sector stocks.
    XLU : list[SectorStockSymbol]
        Utilities sector stocks.
    XLRE : list[SectorStockSymbol]
        Real Estate sector stocks.
    XLC : list[SectorStockSymbol]
        Communication Services sector stocks.

    Examples
    --------
    >>> config = SectorStocksConfig(
    ...     XLF=[SectorStockSymbol(
    ...         symbol="JPM",
    ...         name="JPMorgan Chase",
    ...         sector="Financial",
    ...     )],
    ... )
    >>> len(config.XLF)
    1
    """

    XLF: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Financial sector stocks",
    )
    XLK: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Technology sector stocks",
    )
    XLV: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Health Care sector stocks",
    )
    XLE: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Energy sector stocks",
    )
    XLI: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Industrial sector stocks",
    )
    XLY: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Consumer Discretionary sector stocks",
    )
    XLP: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Consumer Staples sector stocks",
    )
    XLB: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Materials sector stocks",
    )
    XLU: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Utilities sector stocks",
    )
    XLRE: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Real Estate sector stocks",
    )
    XLC: list[SectorStockSymbol] = Field(
        default_factory=list,
        description="Communication Services sector stocks",
    )


class ReturnPeriodsConfig(BaseModel):
    """Configuration for return calculation periods.

    Parameters
    ----------
    d1 : int
        1 trading day.
    wow : str
        Week over Week (previous Tuesday close).
    w1 : int
        1 week (5 trading days).
    mtd : str
        Month to date.
    m1 : int
        1 month (21 trading days).
    m3 : int
        3 months (63 trading days).
    m6 : int
        6 months (126 trading days).
    ytd : str
        Year to date.
    y1 : int
        1 year (252 trading days).
    y3 : int
        3 years (756 trading days).
    y5 : int
        5 years (1260 trading days).

    Examples
    --------
    >>> config = ReturnPeriodsConfig(
    ...     d1=1, wow="prev_tue", w1=5, mtd="mtd",
    ...     m1=21, m3=63, m6=126, ytd="ytd",
    ...     y1=252, y3=756, y5=1260,
    ... )
    >>> config.w1
    5
    """

    d1: int = Field(..., alias="1D", description="1 trading day")
    wow: str = Field(..., alias="WoW", description="Week over Week")
    w1: int = Field(..., alias="1W", description="1 week (5 trading days)")
    mtd: str = Field(..., alias="MTD", description="Month to date")
    m1: int = Field(..., alias="1M", description="1 month (21 trading days)")
    m3: int = Field(..., alias="3M", description="3 months (63 trading days)")
    m6: int = Field(..., alias="6M", description="6 months (126 trading days)")
    ytd: str = Field(..., alias="YTD", description="Year to date")
    y1: int = Field(..., alias="1Y", description="1 year (252 trading days)")
    y3: int = Field(..., alias="3Y", description="3 years (756 trading days)")
    y5: int = Field(..., alias="5Y", description="5 years (1260 trading days)")

    model_config = ConfigDict(populate_by_name=True)


class SymbolsConfig(BaseModel):
    """Root configuration model for symbols.yaml.

    This is the main configuration class that contains all symbol group
    definitions for financial market analysis.

    Parameters
    ----------
    indices : IndicesConfig
        Configuration for stock indices (US and global).
    mag7 : list[Mag7Symbol]
        List of Magnificent 7 stocks.
    commodities : list[CommoditySymbol]
        List of commodity futures.
    currencies : dict[str, list[CurrencyPairSymbol]]
        Dictionary of currency pair groups (e.g., jpy_crosses).
    sectors : list[SectorSymbol]
        List of sector ETFs.
    sector_stocks : SectorStocksConfig
        Configuration for sector representative stocks.
    return_periods : ReturnPeriodsConfig
        Configuration for return calculation periods.

    Examples
    --------
    >>> config = SymbolsConfig(...)
    >>> config.get_symbols("mag7")
    ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

    >>> config.get_symbols("indices", "us")
    ['^GSPC', '^DJI', '^IXIC', ...]
    """

    indices: IndicesConfig = Field(
        default_factory=IndicesConfig,
        description="Configuration for stock indices",
    )
    mag7: list[Mag7Symbol] = Field(
        default_factory=list,
        description="List of Magnificent 7 stocks",
    )
    commodities: list[CommoditySymbol] = Field(
        default_factory=list,
        description="List of commodity futures",
    )
    currencies: dict[str, list[CurrencyPairSymbol]] = Field(
        default_factory=dict,
        description="Dictionary of currency pair groups",
    )
    sectors: list[SectorSymbol] = Field(
        default_factory=list,
        description="List of sector ETFs",
    )
    sector_stocks: SectorStocksConfig = Field(
        default_factory=SectorStocksConfig,
        description="Configuration for sector representative stocks",
    )
    return_periods: ReturnPeriodsConfig = Field(
        ...,
        description="Configuration for return calculation periods",
    )

    def get_symbols(
        self,
        group: str,
        subgroup: str | None = None,
    ) -> list[str]:
        """Get list of ticker symbols for a group.

        Parameters
        ----------
        group : str
            Group name (e.g., "mag7", "sectors", "indices").
        subgroup : str | None, optional
            Subgroup name for nested groups (e.g., "us", "global" for indices,
            "jpy_crosses" for currencies).

        Returns
        -------
        list[str]
            List of ticker symbols. Returns empty list if group/subgroup
            is not found.

        Examples
        --------
        >>> config.get_symbols("mag7")
        ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

        >>> config.get_symbols("indices", "us")
        ['^GSPC', '^DJI', '^IXIC', '^NDX', ...]

        >>> config.get_symbols("currencies", "jpy_crosses")
        ['USDJPY=X', 'EURJPY=X', ...]
        """
        match group:
            case "indices":
                return self._get_indices_symbols(subgroup)
            case "mag7":
                return [s.symbol for s in self.mag7]
            case "commodities":
                return [s.symbol for s in self.commodities]
            case "currencies":
                return self._get_currency_symbols(subgroup)
            case "sectors":
                return [s.symbol for s in self.sectors]
            case "sector_stocks":
                return self._get_sector_stock_symbols(subgroup)
            case _:
                logger.warning("Symbol group not found", group=group)
                return []

    def _get_indices_symbols(self, subgroup: str | None) -> list[str]:
        """Get indices symbols for a subgroup.

        Parameters
        ----------
        subgroup : str | None
            Subgroup name ("us" or "global").

        Returns
        -------
        list[str]
            List of index symbols.
        """
        if subgroup is None:
            # Return all indices
            return [s.symbol for s in self.indices.us + self.indices.global_]
        if subgroup == "us":
            return [s.symbol for s in self.indices.us]
        if subgroup == "global":
            return [s.symbol for s in self.indices.global_]
        logger.warning(
            "Symbol subgroup not found",
            group="indices",
            subgroup=subgroup,
        )
        return []

    def _get_currency_symbols(self, subgroup: str | None) -> list[str]:
        """Get currency symbols for a subgroup.

        Parameters
        ----------
        subgroup : str | None
            Subgroup name (e.g., "jpy_crosses").

        Returns
        -------
        list[str]
            List of currency pair symbols.
        """
        if subgroup is None:
            # Return all currencies
            return [s.symbol for pairs in self.currencies.values() for s in pairs]
        if subgroup in self.currencies:
            return [s.symbol for s in self.currencies[subgroup]]
        logger.warning(
            "Symbol subgroup not found",
            group="currencies",
            subgroup=subgroup,
        )
        return []

    def _get_sector_stock_symbols(self, subgroup: str | None) -> list[str]:
        """Get sector stock symbols for a subgroup.

        Parameters
        ----------
        subgroup : str | None
            Sector ETF symbol (e.g., "XLF", "XLK").

        Returns
        -------
        list[str]
            List of stock symbols.
        """
        if subgroup is None:
            # Return all sector stocks
            all_symbols: list[str] = []
            for sector_name in [
                "XLF",
                "XLK",
                "XLV",
                "XLE",
                "XLI",
                "XLY",
                "XLP",
                "XLB",
                "XLU",
                "XLRE",
                "XLC",
            ]:
                stocks = getattr(self.sector_stocks, sector_name, [])
                all_symbols.extend([s.symbol for s in stocks])
            return all_symbols

        if hasattr(self.sector_stocks, subgroup):
            stocks = getattr(self.sector_stocks, subgroup)
            return [s.symbol for s in stocks]

        logger.warning(
            "Symbol subgroup not found",
            group="sector_stocks",
            subgroup=subgroup,
        )
        return []


# Export all public symbols
__all__ = [
    "CommoditySymbol",
    "CurrencyPairSymbol",
    "IndexSymbol",
    "IndicesConfig",
    "Mag7Symbol",
    "ReturnPeriodsConfig",
    "SectorStockSymbol",
    "SectorStocksConfig",
    "SectorSymbol",
    "SymbolsConfig",
]
