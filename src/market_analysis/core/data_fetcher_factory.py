"""Factory class for creating data fetcher instances.

This module provides a factory pattern implementation for creating
data fetcher instances based on the specified data source.
"""

from types import MappingProxyType
from typing import Any

from ..types import DataSource
from ..utils.logging_config import get_logger
from .base_fetcher import BaseDataFetcher
from .bloomberg_fetcher import BloombergFetcher
from .factset_fetcher import FactSetFetcher
from .fred_fetcher import FREDFetcher
from .mock_fetchers import MockBloombergFetcher, MockFactSetFetcher
from .yfinance_fetcher import YFinanceFetcher

logger = get_logger(__name__, module="data_fetcher_factory")

# Immutable mapping of source names to fetcher classes
_FETCHER_REGISTRY: MappingProxyType[str, type[BaseDataFetcher]] = MappingProxyType(
    {
        DataSource.YFINANCE.value: YFinanceFetcher,
        DataSource.FRED.value: FREDFetcher,
        DataSource.BLOOMBERG.value: BloombergFetcher,
        DataSource.FACTSET.value: FactSetFetcher,
    }
)

# Mock fetchers for testing (use "mock_bloomberg" or "mock_factset")
_MOCK_FETCHER_REGISTRY: MappingProxyType[str, type[BaseDataFetcher]] = MappingProxyType(
    {
        "mock_bloomberg": MockBloombergFetcher,
        "mock_factset": MockFactSetFetcher,
    }
)


class DataFetcherFactory:
    """Factory class for creating data fetcher instances.

    This class provides a static factory method to create the appropriate
    data fetcher based on the specified data source.

    Examples
    --------
    >>> fetcher = DataFetcherFactory.create("yfinance")
    >>> isinstance(fetcher, YFinanceFetcher)
    True

    >>> fetcher = DataFetcherFactory.create("fred", api_key="my_key")
    >>> isinstance(fetcher, FREDFetcher)
    True
    """

    @staticmethod
    def create(source: str, **kwargs: Any) -> BaseDataFetcher:
        """Create a data fetcher instance for the specified source.

        Parameters
        ----------
        source : str
            The data source identifier. Supported values:
            - "yfinance": Yahoo Finance data
            - "fred": Federal Reserve Economic Data
            - "bloomberg": Bloomberg Terminal data
            - "factset": FactSet data files
            - "mock_bloomberg": Mock Bloomberg for testing
            - "mock_factset": Mock FactSet for testing
        **kwargs : Any
            Additional arguments passed to the fetcher constructor.
            For YFinanceFetcher: cache, cache_config, retry_config
            For FREDFetcher: api_key, cache, cache_config, retry_config
            For BloombergFetcher: host, port, cache, cache_config, retry_config
            For FactSetFetcher: data_dir, db_path, cache, cache_config, retry_config
            For MockBloombergFetcher: base_price, volatility, seed
            For MockFactSetFetcher: base_price, volatility, n_constituents, seed

        Returns
        -------
        BaseDataFetcher
            An instance of the appropriate data fetcher

        Raises
        ------
        ValueError
            If the specified source is not supported

        Examples
        --------
        >>> fetcher = DataFetcherFactory.create("yfinance")
        >>> fetcher.source
        <DataSource.YFINANCE: 'yfinance'>

        >>> fetcher = DataFetcherFactory.create("fred", api_key="key")
        >>> fetcher.source
        <DataSource.FRED: 'fred'>

        >>> fetcher = DataFetcherFactory.create("mock_bloomberg", seed=42)
        >>> fetcher.source
        <DataSource.BLOOMBERG: 'bloomberg'>
        """
        source_lower = source.lower()

        logger.debug(
            "Creating data fetcher",
            source=source_lower,
            kwargs_keys=list(kwargs.keys()),
        )

        # Try mock fetchers first
        fetcher_class = _MOCK_FETCHER_REGISTRY.get(source_lower)

        # Then try regular fetchers
        if fetcher_class is None:
            fetcher_class = _FETCHER_REGISTRY.get(source_lower)

        if fetcher_class is None:
            supported = DataFetcherFactory.get_supported_sources()
            logger.error(
                "Unknown data source requested",
                source=source,
                supported_sources=supported,
            )
            raise ValueError(
                f"Unknown data source: '{source}'. Supported sources: {supported}"
            )

        fetcher = fetcher_class(**kwargs)

        logger.info(
            "Data fetcher created",
            source=source_lower,
            fetcher_type=type(fetcher).__name__,
        )

        return fetcher

    @staticmethod
    def get_supported_sources(include_mock: bool = True) -> list[str]:
        """Get list of supported data sources.

        Parameters
        ----------
        include_mock : bool
            Whether to include mock sources (default: True)

        Returns
        -------
        list[str]
            List of supported source identifiers

        Examples
        --------
        >>> sources = DataFetcherFactory.get_supported_sources()
        >>> "yfinance" in sources
        True
        >>> "fred" in sources
        True
        >>> "bloomberg" in sources
        True
        >>> "mock_bloomberg" in sources
        True
        """
        sources = list(_FETCHER_REGISTRY.keys())
        if include_mock:
            sources.extend(_MOCK_FETCHER_REGISTRY.keys())
        return sources


__all__ = [
    "DataFetcherFactory",
]
