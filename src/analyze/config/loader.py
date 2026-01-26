"""Configuration loader for symbol groups.

This module provides functions to load and access symbol group definitions
from YAML configuration files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from database.utils.logging_config import get_logger

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
    config = load_symbols_config()

    if group not in config:
        logger.warning("Symbol group not found", group=group)
        return []

    group_data = config[group]

    # Handle nested groups (like indices.us, indices.global)
    if subgroup is not None:
        if not isinstance(group_data, dict) or subgroup not in group_data:
            logger.warning(
                "Symbol subgroup not found",
                group=group,
                subgroup=subgroup,
            )
            return []
        group_data = group_data[subgroup]

    # Extract symbols from list of dicts
    if isinstance(group_data, list):
        return [item["symbol"] for item in group_data if "symbol" in item]

    return []


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
    config = load_symbols_config()

    if group not in config:
        logger.warning("Symbol group not found", group=group)
        return []

    group_data = config[group]

    # Handle nested groups
    if subgroup is not None:
        if not isinstance(group_data, dict) or subgroup not in group_data:
            logger.warning(
                "Symbol subgroup not found",
                group=group,
                subgroup=subgroup,
            )
            return []
        group_data = group_data[subgroup]

    if isinstance(group_data, list):
        return group_data

    return []


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
    config = load_symbols_config()
    return config.get("return_periods", {})
