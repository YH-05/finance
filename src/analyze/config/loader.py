"""Configuration loader for symbol groups.

This module provides functions to load and access symbol group definitions
from YAML configuration files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from analyze.config.models import (
    CommoditySymbol,
    CurrencyPairSymbol,
    IndexSymbol,
    IndicesConfig,
    Mag7Symbol,
    ReturnPeriodsConfig,
    SectorStocksConfig,
    SectorStockSymbol,
    SectorSymbol,
    SymbolsConfig,
)
from utils_core.logging import get_logger

logger = get_logger(__name__, module="config")

# Path to the symbols configuration file
CONFIG_DIR = Path(__file__).parent
SYMBOLS_CONFIG_PATH = CONFIG_DIR / "symbols.yaml"


@lru_cache(maxsize=1)
def load_symbols_config() -> dict[str, Any]:
    """Load symbols configuration from YAML file.

    Returns
    -------
    dict[str, Any]
        Parsed configuration dictionary

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist
    yaml.YAMLError
        If the YAML file is malformed

    Examples
    --------
    >>> config = load_symbols_config()
    >>> config["mag7"][0]["symbol"]
    'AAPL'
    """
    logger.debug("Loading symbols config", path=str(SYMBOLS_CONFIG_PATH))

    if not SYMBOLS_CONFIG_PATH.exists():
        msg = f"Symbols config file not found: {SYMBOLS_CONFIG_PATH}"
        raise FileNotFoundError(msg)

    with SYMBOLS_CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info(
        "Symbols config loaded",
        groups=list(config.keys()) if config else [],
    )

    return config or {}


def get_symbols(group: str, subgroup: str | None = None) -> list[str]:
    """Get list of ticker symbols for a group.

    Parameters
    ----------
    group : str
        Group name (e.g., "mag7", "sectors", "indices")
    subgroup : str | None, optional
        Subgroup name for nested groups (e.g., "us", "global" for indices)

    Returns
    -------
    list[str]
        List of ticker symbols

    Examples
    --------
    >>> get_symbols("mag7")
    ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

    >>> get_symbols("indices", "us")
    ['^GSPC', '^DJI', '^IXIC', '^RUT']
    """
    config = _load_symbols_config()
    return config.get_symbols(group, subgroup)


def get_symbol_group(
    group: str,
    subgroup: str | None = None,
) -> list[dict[str, str]]:
    """Get full symbol group data including names.

    Parameters
    ----------
    group : str
        Group name (e.g., "mag7", "sectors", "indices")
    subgroup : str | None, optional
        Subgroup name for nested groups

    Returns
    -------
    list[dict[str, str]]
        List of symbol dictionaries with 'symbol' and 'name' keys

    Examples
    --------
    >>> get_symbol_group("mag7")[0]
    {'symbol': 'AAPL', 'name': 'Apple'}
    """
    config = _load_symbols_config()
    return config.get_symbol_group(group, subgroup)


def get_return_periods() -> dict[str, int | str]:
    """Get return period definitions.

    Returns
    -------
    dict[str, int | str]
        Dictionary mapping period names to number of days or special strings

    Examples
    --------
    >>> periods = get_return_periods()
    >>> periods["1W"]
    5
    >>> periods["YTD"]
    'ytd'
    """
    config = _load_symbols_config()
    return config.get_return_periods_dict()


@lru_cache(maxsize=1)
def _load_symbols_config() -> SymbolsConfig:
    """Load symbols configuration as a Pydantic model.

    This function loads the YAML configuration file and parses it into a
    type-safe SymbolsConfig Pydantic model. The result is cached using
    @lru_cache to ensure the file is only read once.

    Returns
    -------
    SymbolsConfig
        Parsed configuration as a Pydantic model with type-safe access.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    yaml.YAMLError
        If the YAML file is malformed.
    pydantic.ValidationError
        If the YAML data does not match the expected schema.

    Examples
    --------
    >>> config = _load_symbols_config()
    >>> config.get_symbols("mag7")
    ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

    >>> config.get_symbols("indices", "us")
    ['^GSPC', '^DJI', '^IXIC', ...]
    """
    logger.debug(
        "Loading symbols config as Pydantic model", path=str(SYMBOLS_CONFIG_PATH)
    )

    if not SYMBOLS_CONFIG_PATH.exists():
        msg = f"Symbols config file not found: {SYMBOLS_CONFIG_PATH}"
        raise FileNotFoundError(msg)

    with SYMBOLS_CONFIG_PATH.open(encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    if raw_data is None:
        raw_data = {}

    # Parse indices config
    indices_data = raw_data.get("indices", {})
    indices_config = IndicesConfig(
        us=[IndexSymbol(**item) for item in indices_data.get("us", [])],
        global_=[IndexSymbol(**item) for item in indices_data.get("global", [])],
    )

    # Parse mag7
    mag7 = [Mag7Symbol(**item) for item in raw_data.get("mag7", [])]

    # Parse commodities
    commodities = [CommoditySymbol(**item) for item in raw_data.get("commodities", [])]

    # Parse currencies
    currencies_data = raw_data.get("currencies", {})
    currencies: dict[str, list[CurrencyPairSymbol]] = {}
    for subgroup, pairs in currencies_data.items():
        currencies[subgroup] = [CurrencyPairSymbol(**item) for item in pairs]

    # Parse sectors
    sectors = [SectorSymbol(**item) for item in raw_data.get("sectors", [])]

    # Parse sector_stocks
    sector_stocks_data = raw_data.get("sector_stocks", {})
    sector_stocks_kwargs: dict[str, list[SectorStockSymbol]] = {}
    for sector_key, stocks in sector_stocks_data.items():
        sector_stocks_kwargs[sector_key] = [
            SectorStockSymbol(**item) for item in stocks
        ]
    sector_stocks = SectorStocksConfig(**sector_stocks_kwargs)

    # Parse return_periods
    return_periods_data = raw_data.get("return_periods", {})
    return_periods = ReturnPeriodsConfig(
        d1=return_periods_data.get("1D", 1),
        wow=return_periods_data.get("WoW", "prev_tue"),
        w1=return_periods_data.get("1W", 5),
        mtd=return_periods_data.get("MTD", "mtd"),
        m1=return_periods_data.get("1M", 21),
        m3=return_periods_data.get("3M", 63),
        m6=return_periods_data.get("6M", 126),
        ytd=return_periods_data.get("YTD", "ytd"),
        y1=return_periods_data.get("1Y", 252),
        y3=return_periods_data.get("3Y", 756),
        y5=return_periods_data.get("5Y", 1260),
    )

    config = SymbolsConfig(
        indices=indices_config,
        mag7=mag7,
        commodities=commodities,
        currencies=currencies,
        sectors=sectors,
        sector_stocks=sector_stocks,
        return_periods=return_periods,
    )

    logger.info(
        "Symbols config loaded as Pydantic model",
        groups=[
            "indices",
            "mag7",
            "commodities",
            "currencies",
            "sectors",
            "sector_stocks",
            "return_periods",
        ],
    )

    return config
