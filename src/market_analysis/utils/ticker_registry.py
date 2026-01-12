"""Ticker registry for managing yfinance symbols.

This module provides a centralized registry for managing yfinance ticker symbols
with metadata including names, categories, and descriptions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from market_analysis.utils.logging_config import get_logger

logger = get_logger(__name__)

# Default configuration file path
# ticker_registry.py is in src/market_analysis/utils/
# data/config/ is at the project root
DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data"
    / "config"
    / "yfinance_tickers.json"
)


TickerCategory = Literal[
    "index",
    "forex",
    "commodity",
    "etf",
    "volatility",
]


@dataclass(frozen=True)
class TickerInfo:
    """Information about a ticker symbol.

    Parameters
    ----------
    symbol : str
        The ticker symbol (e.g., "^GSPC", "USDJPY=X")
    name_ja : str
        Japanese name
    name_en : str
        English name
    category : str
        Category (index, forex, commodity, etf, etc.)
    group : str
        Group within the configuration file
    description : str
        Description of the ticker
    metadata : dict[str, Any]
        Additional metadata from the config

    Examples
    --------
    >>> info = TickerInfo(
    ...     symbol="^GSPC",
    ...     name_ja="S&P 500",
    ...     name_en="S&P 500 Index",
    ...     category="index",
    ...     group="Stock Indices",
    ...     description="米国大型株500銘柄の時価総額加重平均指数。",
    ... )
    """

    symbol: str
    name_ja: str
    name_en: str
    category: str
    group: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TickerRegistry:
    """Registry for managing yfinance ticker symbols.

    Provides centralized access to ticker information with filtering
    and lookup capabilities.

    Parameters
    ----------
    config_path : Path | str | None
        Path to the configuration JSON file.
        If None, uses the default path.

    Examples
    --------
    >>> registry = TickerRegistry()
    >>> info = registry.get("^GSPC")
    >>> info.name_ja
    'S&P 500'

    >>> forex_tickers = registry.get_by_category("forex")
    >>> len(forex_tickers)
    9

    >>> symbols = registry.get_symbols(category="commodity")
    >>> "GC=F" in symbols
    True
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize the ticker registry.

        Parameters
        ----------
        config_path : Path | str | None
            Path to the configuration JSON file
        """
        self._config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._tickers: dict[str, TickerInfo] = {}
        self._groups: dict[str, list[str]] = {}
        self._categories: dict[str, list[str]] = {}
        self._loaded = False

        logger.debug(
            "TickerRegistry initialized",
            config_path=str(self._config_path),
        )

    def _load(self) -> None:
        """Load ticker configuration from file."""
        if self._loaded:
            return

        if not self._config_path.exists():
            logger.warning(
                "Ticker config file not found",
                path=str(self._config_path),
            )
            self._loaded = True
            return

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)

            for group_name, tickers in data.items():
                self._groups[group_name] = []
                for symbol, info in tickers.items():
                    category = info.get("category", "unknown")
                    ticker_info = TickerInfo(
                        symbol=symbol,
                        name_ja=info.get("name_ja", ""),
                        name_en=info.get("name_en", ""),
                        category=category,
                        group=group_name,
                        description=info.get("description", ""),
                        metadata={
                            k: v
                            for k, v in info.items()
                            if k
                            not in ("name_ja", "name_en", "category", "description")
                        },
                    )
                    self._tickers[symbol] = ticker_info
                    self._groups[group_name].append(symbol)

                    if category not in self._categories:
                        self._categories[category] = []
                    self._categories[category].append(symbol)

            logger.info(
                "Ticker config loaded",
                ticker_count=len(self._tickers),
                group_count=len(self._groups),
            )
            self._loaded = True

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse ticker config",
                path=str(self._config_path),
                error=str(e),
            )
            self._loaded = True
        except Exception as e:
            logger.error(
                "Failed to load ticker config",
                path=str(self._config_path),
                error=str(e),
                exc_info=True,
            )
            self._loaded = True

    def get(self, symbol: str) -> TickerInfo | None:
        """Get ticker information by symbol.

        Parameters
        ----------
        symbol : str
            The ticker symbol

        Returns
        -------
        TickerInfo | None
            Ticker information if found, None otherwise

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> info = registry.get("^GSPC")
        >>> info.name_en
        'S&P 500 Index'
        """
        self._load()
        return self._tickers.get(symbol)

    def get_by_category(self, category: str) -> list[TickerInfo]:
        """Get all tickers in a category.

        Parameters
        ----------
        category : str
            Category name (e.g., "index", "forex", "commodity")

        Returns
        -------
        list[TickerInfo]
            List of ticker information

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> commodities = registry.get_by_category("commodity")
        >>> len(commodities)
        10
        """
        self._load()
        symbols = self._categories.get(category, [])
        return [self._tickers[s] for s in symbols]

    def get_by_group(self, group: str) -> list[TickerInfo]:
        """Get all tickers in a group.

        Parameters
        ----------
        group : str
            Group name (e.g., "Stock Indices", "Forex", "Commodities")

        Returns
        -------
        list[TickerInfo]
            List of ticker information

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> forex = registry.get_by_group("Forex")
        >>> len(forex)
        9
        """
        self._load()
        symbols = self._groups.get(group, [])
        return [self._tickers[s] for s in symbols]

    def get_symbols(
        self,
        category: str | None = None,
        group: str | None = None,
    ) -> list[str]:
        """Get ticker symbols with optional filtering.

        Parameters
        ----------
        category : str | None
            Filter by category
        group : str | None
            Filter by group

        Returns
        -------
        list[str]
            List of ticker symbols

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> all_symbols = registry.get_symbols()
        >>> len(all_symbols) > 0
        True

        >>> index_symbols = registry.get_symbols(category="index")
        >>> "^GSPC" in index_symbols
        True
        """
        self._load()

        if category:
            return list(self._categories.get(category, []))
        if group:
            return list(self._groups.get(group, []))
        return list(self._tickers.keys())

    def list_categories(self) -> list[str]:
        """List all available categories.

        Returns
        -------
        list[str]
            List of category names

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> categories = registry.list_categories()
        >>> "index" in categories
        True
        """
        self._load()
        return list(self._categories.keys())

    def list_groups(self) -> list[str]:
        """List all available groups.

        Returns
        -------
        list[str]
            List of group names

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> groups = registry.list_groups()
        >>> "Stock Indices" in groups
        True
        """
        self._load()
        return list(self._groups.keys())

    def contains(self, symbol: str) -> bool:
        """Check if a symbol is registered.

        Parameters
        ----------
        symbol : str
            The ticker symbol

        Returns
        -------
        bool
            True if symbol is registered

        Examples
        --------
        >>> registry = TickerRegistry()
        >>> registry.contains("^GSPC")
        True
        >>> registry.contains("INVALID_TICKER")
        False
        """
        self._load()
        return symbol in self._tickers

    def __len__(self) -> int:
        """Return the number of registered tickers."""
        self._load()
        return len(self._tickers)

    def __contains__(self, symbol: str) -> bool:
        """Check if a symbol is registered."""
        return self.contains(symbol)

    def __iter__(self):
        """Iterate over all ticker symbols."""
        self._load()
        return iter(self._tickers.keys())


# Singleton instance for convenience
_default_registry: TickerRegistry | None = None


def get_ticker_registry() -> TickerRegistry:
    """Get the default ticker registry instance.

    Returns
    -------
    TickerRegistry
        The default registry instance

    Examples
    --------
    >>> registry = get_ticker_registry()
    >>> info = registry.get("^GSPC")
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = TickerRegistry()
    return _default_registry
