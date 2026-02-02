"""Configuration loader for the news package.

This module provides the ConfigLoader class for loading and managing
configuration from YAML and JSON files.

Examples
--------
>>> loader = ConfigLoader()
>>> config = loader.load("data/config/news_sources.yaml")
>>> config.settings.max_articles_per_source
10

>>> symbols = loader.load_symbols("src/analyze/config/symbols.yaml")
>>> symbols["mag7"][0]["symbol"]
'AAPL'
"""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from utils_core.logging import get_logger

from .errors import ConfigParseError
from .models import NewsConfig

logger = get_logger(__name__, module="config.loader")

# Default configuration file path
DEFAULT_CONFIG_PATH = Path("data/config/news_sources.yaml")


class ConfigLoader:
    """Configuration loader for news package.

    Loads configuration from YAML or JSON files and provides access to
    symbol definitions from symbols.yaml files.

    Examples
    --------
    >>> loader = ConfigLoader()
    >>> config = loader.load("config.yaml")
    >>> config.settings.max_articles_per_source
    10

    >>> symbols = loader.load_symbols("symbols.yaml", categories=["mag7"])
    >>> len(symbols["mag7"])
    7
    """

    def load(self, file_path: str | Path) -> NewsConfig:
        """Load configuration from a YAML or JSON file.

        Parameters
        ----------
        file_path : str | Path
            Path to the configuration file. Supports .yaml, .yml, and .json
            extensions.

        Returns
        -------
        NewsConfig
            Parsed and validated configuration object.

        Raises
        ------
        FileNotFoundError
            If the configuration file does not exist.
        ConfigParseError
            If the file format is unsupported or parsing fails.

        Examples
        --------
        >>> loader = ConfigLoader()
        >>> config = loader.load("config.yaml")
        >>> config.settings.max_articles_per_source
        10
        """
        path = Path(file_path)

        if not path.exists():
            logger.error("Configuration file not found", file_path=str(path))
            raise FileNotFoundError(f"Configuration file not found: {path}")

        logger.debug("Loading configuration", file_path=str(path))

        data = self._read_file(path)

        try:
            config = NewsConfig.model_validate(data or {})
            logger.info(
                "Configuration loaded successfully",
                file_path=str(path),
                sources_configured=config.sources.yfinance_ticker is not None
                or config.sources.yfinance_search is not None,
            )
            return config
        except PydanticValidationError as e:
            logger.error(
                "Configuration validation failed",
                file_path=str(path),
                error=str(e),
            )
            raise ConfigParseError(
                message=f"Invalid configuration: {e}",
                file_path=str(path),
                cause=e,
            ) from e

    def load_from_default(self) -> NewsConfig:
        """Load configuration from the default path.

        If the default configuration file does not exist, returns a
        default configuration object.

        Returns
        -------
        NewsConfig
            Parsed configuration or default configuration.

        Examples
        --------
        >>> loader = ConfigLoader()
        >>> config = loader.load_from_default()
        >>> config.settings.max_articles_per_source
        10
        """
        if DEFAULT_CONFIG_PATH.exists():
            logger.debug(
                "Loading from default path",
                file_path=str(DEFAULT_CONFIG_PATH),
            )
            return self.load(DEFAULT_CONFIG_PATH)

        logger.info(
            "Default configuration file not found, using defaults",
            default_path=str(DEFAULT_CONFIG_PATH),
        )
        return NewsConfig()

    def load_symbols(
        self,
        file_path: str | Path,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Load symbol definitions from a YAML file.

        Parameters
        ----------
        file_path : str | Path
            Path to the symbols YAML file.
        categories : list[str] | None, optional
            List of categories to load. If None, loads all categories.

        Returns
        -------
        dict[str, Any]
            Dictionary of symbol definitions by category.

        Raises
        ------
        FileNotFoundError
            If the symbols file does not exist.
        ConfigParseError
            If parsing fails.

        Examples
        --------
        >>> loader = ConfigLoader()
        >>> symbols = loader.load_symbols("symbols.yaml")
        >>> "mag7" in symbols
        True

        >>> symbols = loader.load_symbols("symbols.yaml", categories=["mag7"])
        >>> "indices" in symbols
        False
        """
        path = Path(file_path)

        if not path.exists():
            logger.error("Symbols file not found", file_path=str(path))
            raise FileNotFoundError(f"Symbols file not found: {path}")

        logger.debug(
            "Loading symbols",
            file_path=str(path),
            categories=categories,
        )

        data = self._read_yaml(path)

        if data is None:
            return {}

        if categories is None:
            return data

        # Filter by specified categories
        result = {}
        for category in categories:
            if category in data:
                result[category] = data[category]

        logger.debug(
            "Symbols loaded",
            file_path=str(path),
            loaded_categories=list(result.keys()),
        )
        return result

    def get_ticker_symbols(
        self,
        file_path: str | Path,
        categories: list[str] | None = None,
    ) -> list[str]:
        """Get a flat list of ticker symbols from a symbols file.

        Parameters
        ----------
        file_path : str | Path
            Path to the symbols YAML file.
        categories : list[str] | None, optional
            List of categories to include. If None, includes all categories.

        Returns
        -------
        list[str]
            Flat list of ticker symbols.

        Examples
        --------
        >>> loader = ConfigLoader()
        >>> tickers = loader.get_ticker_symbols("symbols.yaml", categories=["mag7"])
        >>> "AAPL" in tickers
        True
        """
        symbols_data = self.load_symbols(file_path, categories)
        tickers: list[str] = []

        for category_data in symbols_data.values():
            tickers.extend(self._extract_symbols(category_data))

        logger.debug(
            "Extracted ticker symbols",
            count=len(tickers),
            categories=categories,
        )
        return tickers

    def _read_file(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a configuration file.

        Parameters
        ----------
        path : Path
            Path to the file.

        Returns
        -------
        dict[str, Any] | None
            Parsed data or None if empty.

        Raises
        ------
        ConfigParseError
            If the file format is unsupported or parsing fails.
        """
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            return self._read_yaml(path)
        elif suffix == ".json":
            return self._read_json(path)
        else:
            raise ConfigParseError(
                message=f"Unsupported file format: {suffix}",
                file_path=str(path),
            )

    def _read_yaml(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a YAML file.

        Parameters
        ----------
        path : Path
            Path to the YAML file.

        Returns
        -------
        dict[str, Any] | None
            Parsed YAML data or None if empty.

        Raises
        ------
        ConfigParseError
            If YAML parsing fails.
        """
        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)

            if data is None:
                return None

            if not isinstance(data, dict):
                raise ConfigParseError(
                    message="YAML root must be a mapping",
                    file_path=str(path),
                )

            return data
        except yaml.YAMLError as e:
            raise ConfigParseError(
                message=f"Invalid YAML: {e}",
                file_path=str(path),
                cause=e,
            ) from e

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a JSON file.

        Parameters
        ----------
        path : Path
            Path to the JSON file.

        Returns
        -------
        dict[str, Any] | None
            Parsed JSON data or None if empty.

        Raises
        ------
        ConfigParseError
            If JSON parsing fails.
        """
        try:
            content = path.read_text(encoding="utf-8")

            if not content.strip():
                return None

            data = json.loads(content)

            if not isinstance(data, dict):
                raise ConfigParseError(
                    message="JSON root must be an object",
                    file_path=str(path),
                )

            return data
        except json.JSONDecodeError as e:
            raise ConfigParseError(
                message=f"Invalid JSON: {e}",
                file_path=str(path),
                cause=e,
            ) from e

    def _extract_symbols(self, data: Any) -> list[str]:
        """Extract symbol strings from nested data structures.

        Handles various formats:
        - List of dicts with 'symbol' key: [{"symbol": "AAPL", "name": "Apple"}]
        - Dict with nested lists: {"us": [{"symbol": "^GSPC"}], "global": [...]}

        Parameters
        ----------
        data : Any
            Symbol data structure.

        Returns
        -------
        list[str]
            List of extracted symbol strings.
        """
        symbols: list[str] = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "symbol" in item:
                    symbols.append(item["symbol"])
        elif isinstance(data, dict):
            for value in data.values():
                symbols.extend(self._extract_symbols(value))

        return symbols


# Export all public symbols
__all__ = [
    "DEFAULT_CONFIG_PATH",
    "ConfigLoader",
]
