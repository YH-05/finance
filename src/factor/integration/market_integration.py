"""Market package integration for factor analysis.

This module provides an adapter that wraps the market package's
YFinanceFetcher to conform to the factor package's DataProvider protocol.

Classes
-------
MarketDataProvider
    Adapter class implementing DataProvider protocol using market package

Functions
---------
create_market_provider
    Factory function to create a MarketDataProvider instance

Examples
--------
>>> from factor.integration.market_integration import create_market_provider
>>> provider = create_market_provider()
>>> df = provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")
"""

from datetime import datetime

import pandas as pd

from market.yfinance import FetchOptions, YFinanceFetcher
from market.yfinance.types import Interval
from utils_core.logging import get_logger

logger = get_logger(__name__)


class MarketDataProvider:
    """Adapter for market package's YFinanceFetcher.

    This class implements the factor package's DataProvider protocol
    by wrapping the market package's YFinanceFetcher. It allows factor
    calculations to use market data transparently.

    Parameters
    ----------
    fetcher : YFinanceFetcher | None
        Custom fetcher instance. If None, creates a default fetcher.

    Attributes
    ----------
    fetcher : YFinanceFetcher
        The underlying data fetcher

    Examples
    --------
    >>> provider = MarketDataProvider()
    >>> prices = provider.get_prices(
    ...     symbols=["AAPL", "GOOGL"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-12-31",
    ... )
    >>> isinstance(prices, pd.DataFrame)
    True
    """

    def __init__(
        self,
        fetcher: YFinanceFetcher | None = None,
    ) -> None:
        """Initialize MarketDataProvider.

        Parameters
        ----------
        fetcher : YFinanceFetcher | None
            Custom fetcher instance. If None, creates a default fetcher.
        """
        logger.debug("Initializing MarketDataProvider")
        self._fetcher = fetcher or YFinanceFetcher()
        logger.info("MarketDataProvider initialized")

    @property
    def fetcher(self) -> YFinanceFetcher:
        """Get the underlying fetcher instance.

        Returns
        -------
        YFinanceFetcher
            The data fetcher
        """
        return self._fetcher

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch OHLCV price data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
        start_date : datetime | str
            Start date for the data range.
        end_date : datetime | str
            End date for the data range.

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with price data.
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, price_type)

        Raises
        ------
        ValueError
            If symbols list is empty.

        Examples
        --------
        >>> provider = MarketDataProvider()
        >>> df = provider.get_prices(["AAPL"], "2024-01-01", "2024-01-31")
        >>> df.columns.names
        ['symbol', 'price_type']
        """
        if not symbols:
            logger.error("Empty symbols list provided")
            raise ValueError("symbols list cannot be empty")

        logger.debug(
            "Fetching price data via market package",
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Create fetch options
        options = FetchOptions(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=Interval.DAILY,
        )

        # Fetch data from market package
        results = self._fetcher.fetch(options)

        # Convert to MultiIndex DataFrame format expected by factor package
        data_frames: dict[str, pd.DataFrame] = {}
        for result in results:
            if not result.is_empty:
                data_frames[result.symbol] = result.data

        if not data_frames:
            logger.warning("No data returned for any symbol")
            return pd.DataFrame()

        # Build MultiIndex DataFrame
        combined = self._build_multiindex_dataframe(data_frames)

        logger.info(
            "Price data fetched successfully",
            symbols=symbols,
            rows=len(combined),
        )

        return combined

    def _build_multiindex_dataframe(
        self,
        data_frames: dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """Build a MultiIndex DataFrame from individual symbol DataFrames.

        Parameters
        ----------
        data_frames : dict[str, pd.DataFrame]
            Dictionary mapping symbol to its DataFrame

        Returns
        -------
        pd.DataFrame
            Combined MultiIndex DataFrame
        """
        if not data_frames:
            return pd.DataFrame()

        # Create MultiIndex columns
        columns_list: list[tuple[str, str]] = []
        data_dict: dict[tuple[str, str], pd.Series] = {}

        for symbol, df in data_frames.items():
            for col in df.columns:
                # Capitalize column names to match expected format
                col_name = col.capitalize() if isinstance(col, str) else str(col)
                key = (symbol, col_name)
                columns_list.append(key)
                # Ensure we have a Series
                col_data = df[col]
                if isinstance(col_data, pd.Series):
                    data_dict[key] = col_data
                else:
                    # If it's a DataFrame (unlikely), take the first column
                    data_dict[key] = (
                        col_data.iloc[:, 0]
                        if hasattr(col_data, "iloc")
                        else pd.Series(col_data)
                    )

        # Create DataFrame with MultiIndex columns
        result = pd.DataFrame(data_dict)
        result.columns = pd.MultiIndex.from_tuples(
            result.columns, names=["symbol", "price_type"]
        )
        result.index.name = "Date"

        return result

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch volume data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
        start_date : datetime | str
            Start date for the data range.
        end_date : datetime | str
            End date for the data range.

        Returns
        -------
        pd.DataFrame
            DataFrame with volume data.
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names

        Raises
        ------
        ValueError
            If symbols list is empty.

        Examples
        --------
        >>> provider = MarketDataProvider()
        >>> df = provider.get_volumes(["AAPL"], "2024-01-01", "2024-01-31")
        >>> "AAPL" in df.columns
        True
        """
        if not symbols:
            logger.error("Empty symbols list provided")
            raise ValueError("symbols list cannot be empty")

        logger.debug(
            "Fetching volume data via market package",
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Fetch price data (includes volume)
        prices = self.get_prices(symbols, start_date, end_date)

        # Extract volume column for each symbol
        volume_data: dict[str, pd.Series] = {}
        for symbol in symbols:
            volume_key = (symbol, "Volume")
            if volume_key in prices.columns:
                vol_data = prices[volume_key]
                if isinstance(vol_data, pd.Series):
                    volume_data[symbol] = vol_data
                else:
                    # Handle unlikely case of DataFrame
                    volume_data[symbol] = (
                        vol_data.iloc[:, 0]
                        if hasattr(vol_data, "iloc")
                        else pd.Series(vol_data)
                    )

        result = pd.DataFrame(volume_data)
        result.index.name = "Date"

        logger.info(
            "Volume data extracted successfully",
            symbols=symbols,
            rows=len(result),
        )

        return result

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch fundamental data for the specified symbols.

        Note: This method returns an empty DataFrame as the market package
        does not directly support fundamental data fetching. Use the
        factor package's YFinanceProvider for fundamental data.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        metrics : list[str]
            List of metrics to fetch
        start_date : datetime | str
            Start date
        end_date : datetime | str
            End date

        Returns
        -------
        pd.DataFrame
            Empty DataFrame (fundamental data not supported via market package)
        """
        logger.warning(
            "Fundamental data not supported via market package integration. "
            "Use factor.providers.YFinanceProvider instead."
        )
        return pd.DataFrame()

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch market capitalization data for the specified symbols.

        Note: This method returns an empty DataFrame as the market package
        does not directly support market cap data. Use the factor package's
        YFinanceProvider for market cap data.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        start_date : datetime | str
            Start date
        end_date : datetime | str
            End date

        Returns
        -------
        pd.DataFrame
            Empty DataFrame (market cap not supported via market package)
        """
        logger.warning(
            "Market cap data not supported via market package integration. "
            "Use factor.providers.YFinanceProvider instead."
        )
        return pd.DataFrame()


def create_market_provider(
    fetcher: YFinanceFetcher | None = None,
) -> MarketDataProvider:
    """Factory function to create a MarketDataProvider.

    Parameters
    ----------
    fetcher : YFinanceFetcher | None
        Optional custom fetcher instance

    Returns
    -------
    MarketDataProvider
        A new MarketDataProvider instance

    Examples
    --------
    >>> provider = create_market_provider()
    >>> isinstance(provider, MarketDataProvider)
    True
    """
    logger.debug("Creating MarketDataProvider via factory function")
    return MarketDataProvider(fetcher=fetcher)


__all__ = [
    "MarketDataProvider",
    "create_market_provider",
]
