"""Market package integration for strategy package.

This module provides an adapter that wraps the market package's
YFinanceFetcher to provide price data for strategy analysis.

Classes
-------
StrategyMarketDataProvider
    Adapter class implementing market data access for strategy package

Functions
---------
create_strategy_market_provider
    Factory function to create a StrategyMarketDataProvider instance

Examples
--------
>>> from strategy.integration import create_strategy_market_provider
>>> provider = create_strategy_market_provider()
>>> df = provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")
"""

from datetime import datetime
from typing import Any

import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__)


class StrategyMarketDataProvider:
    """Adapter for market package's YFinanceFetcher.

    This class provides a unified interface for fetching market data
    within the strategy package context. It wraps the market package's
    YFinanceFetcher to provide price and volume data.

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
    >>> provider = StrategyMarketDataProvider()
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
        fetcher: Any | None = None,
    ) -> None:
        """Initialize StrategyMarketDataProvider.

        Parameters
        ----------
        fetcher : YFinanceFetcher | None
            Custom fetcher instance. If None, creates a default fetcher.
        """
        logger.debug("Initializing StrategyMarketDataProvider")

        if fetcher is not None:
            self._fetcher = fetcher
        else:
            # Lazy import to avoid circular dependencies
            from market.yfinance import YFinanceFetcher

            self._fetcher = YFinanceFetcher()

        logger.info("StrategyMarketDataProvider initialized")

    @property
    def fetcher(self) -> Any:
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
            DataFrame with price data.
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, price_type)

        Raises
        ------
        ValueError
            If symbols list is empty.

        Examples
        --------
        >>> provider = StrategyMarketDataProvider()
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

        # Import here to avoid circular dependencies
        from market.yfinance import FetchOptions
        from market.yfinance.types import Interval

        # Create fetch options
        options = FetchOptions(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=Interval.DAILY,
        )

        # Fetch data from market package
        results = self._fetcher.fetch(options)

        # Convert to MultiIndex DataFrame format expected by strategy package
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

    def get_returns(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch and calculate daily returns for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols.
        start_date : datetime | str
            Start date.
        end_date : datetime | str
            End date.

        Returns
        -------
        pd.DataFrame
            DataFrame with daily returns.
        """
        logger.debug("Fetching returns", symbols=symbols)

        prices = self.get_prices(symbols, start_date, end_date)

        if prices.empty:
            return pd.DataFrame()

        # Extract close prices and calculate returns
        returns_data: dict[str, pd.Series] = {}
        for symbol in symbols:
            close_key = (symbol, "Close")
            if close_key in prices.columns:
                close_data = prices[close_key]
                if isinstance(close_data, pd.Series):
                    returns_data[symbol] = close_data.pct_change()

        result = pd.DataFrame(returns_data)
        result.index.name = "Date"

        logger.info("Returns calculated", symbols=symbols, rows=len(result))

        return result


def create_strategy_market_provider(
    fetcher: Any | None = None,
) -> StrategyMarketDataProvider:
    """Factory function to create a StrategyMarketDataProvider.

    Parameters
    ----------
    fetcher : YFinanceFetcher | None
        Optional custom fetcher instance

    Returns
    -------
    StrategyMarketDataProvider
        A new StrategyMarketDataProvider instance

    Examples
    --------
    >>> provider = create_strategy_market_provider()
    >>> isinstance(provider, StrategyMarketDataProvider)
    True
    """
    logger.debug("Creating StrategyMarketDataProvider via factory function")
    return StrategyMarketDataProvider(fetcher=fetcher)


__all__ = [
    "StrategyMarketDataProvider",
    "create_strategy_market_provider",
]
