"""Factory class for creating data fetcher instances.

This module provides a factory pattern implementation for creating
data fetcher instances based on the specified data source.
"""

from typing import Any

from ..types import DataSource
from ..utils.logging_config import get_logger
from .base_fetcher import BaseDataFetcher
from .fred_fetcher import FREDFetcher
from .yfinance_fetcher import YFinanceFetcher

logger = get_logger(__name__, module="data_fetcher_factory")

# Mapping of source names to fetcher classes
_FETCHER_REGISTRY: dict[str, type[BaseDataFetcher]] = {
    DataSource.YFINANCE.value: YFinanceFetcher,
    DataSource.FRED.value: FREDFetcher,
}


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
            The data source identifier ("yfinance" or "fred")
        **kwargs : Any
            Additional arguments passed to the fetcher constructor.
            For YFinanceFetcher: cache, cache_config, retry_config
            For FREDFetcher: api_key, cache, cache_config, retry_config

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
        """
        source_lower = source.lower()

        logger.debug(
            "Creating data fetcher",
            source=source_lower,
            kwargs_keys=list(kwargs.keys()),
        )

        fetcher_class = _FETCHER_REGISTRY.get(source_lower)

        if fetcher_class is None:
            supported = DataFetcherFactory.get_supported_sources()
            logger.error(
                "Unknown data source requested",
                source=source,
                supported_sources=supported,
            )
            raise ValueError(
                f"Unknown data source: '{source}'. " f"Supported sources: {supported}"
            )

        fetcher = fetcher_class(**kwargs)

        logger.info(
            "Data fetcher created",
            source=source_lower,
            fetcher_type=type(fetcher).__name__,
        )

        return fetcher

    @staticmethod
    def get_supported_sources() -> list[str]:
        """Get list of supported data sources.

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
        """
        return list(_FETCHER_REGISTRY.keys())


__all__ = [
    "DataFetcherFactory",
]
