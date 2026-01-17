"""Base module for data providers.

This module defines the DataProvider Protocol, which provides an abstract
interface for fetching financial data from various sources.

Examples
--------
>>> from datetime import datetime
>>> from factor.providers.base import DataProvider
>>> # Check if a class implements the protocol
>>> class MyProvider:
...     def get_prices(self, symbols, start_date, end_date):
...         ...
...     def get_volumes(self, symbols, start_date, end_date):
...         ...
...     def get_fundamentals(self, symbols, metrics, start_date, end_date):
...         ...
...     def get_market_cap(self, symbols, start_date, end_date):
...         ...
>>> isinstance(MyProvider(), DataProvider)
True
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DataProvider(Protocol):
    """Protocol for data providers.

    This protocol defines the interface for data providers that fetch
    financial data such as prices, volumes, fundamentals, and market cap.

    All implementations must provide the following methods:
    - get_prices: Fetch OHLCV price data
    - get_volumes: Fetch volume data
    - get_fundamentals: Fetch fundamental metrics
    - get_market_cap: Fetch market capitalization data

    The protocol is marked as @runtime_checkable, allowing isinstance()
    checks to verify if an object implements the required interface.

    Notes
    -----
    Date parameters accept both datetime objects and ISO format strings
    (e.g., "2024-01-01") for flexibility.

    DataFrame Return Schemas:

    get_prices:
        - Index: DatetimeIndex named "Date"
        - Columns: MultiIndex with levels (symbol, price_type)
        - price_type values: ["Open", "High", "Low", "Close", "Volume"]

    get_volumes:
        - Index: DatetimeIndex named "Date"
        - Columns: symbol names

    get_fundamentals:
        - Index: DatetimeIndex named "Date"
        - Columns: MultiIndex with levels (symbol, metric)

    get_market_cap:
        - Index: DatetimeIndex named "Date"
        - Columns: symbol names

    Examples
    --------
    >>> class YFinanceProvider:
    ...     def get_prices(
    ...         self,
    ...         symbols: list[str],
    ...         start_date: datetime | str,
    ...         end_date: datetime | str,
    ...     ) -> pd.DataFrame:
    ...         # Implementation using yfinance
    ...         ...
    ...
    ...     def get_volumes(
    ...         self,
    ...         symbols: list[str],
    ...         start_date: datetime | str,
    ...         end_date: datetime | str,
    ...     ) -> pd.DataFrame:
    ...         # Implementation using yfinance
    ...         ...
    ...
    ...     def get_fundamentals(
    ...         self,
    ...         symbols: list[str],
    ...         metrics: list[str],
    ...         start_date: datetime | str,
    ...         end_date: datetime | str,
    ...     ) -> pd.DataFrame:
    ...         # Implementation using yfinance
    ...         ...
    ...
    ...     def get_market_cap(
    ...         self,
    ...         symbols: list[str],
    ...         start_date: datetime | str,
    ...         end_date: datetime | str,
    ...     ) -> pd.DataFrame:
    ...         # Implementation using yfinance
    ...         ...
    >>> provider = YFinanceProvider()
    >>> isinstance(provider, DataProvider)
    True
    """

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
            Examples: ["AAPL", "GOOGL", "MSFT"]
        start_date : datetime | str
            Start date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, price_type)
            - price_type values: ["Open", "High", "Low", "Close", "Volume"]

        Examples
        --------
        >>> provider = SomeDataProvider()
        >>> df = provider.get_prices(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ... )
        >>> df.columns.names
        ['symbol', 'price_type']
        >>> df.index.name
        'Date'
        >>> list(df.columns.get_level_values("price_type").unique())
        ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        ...

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
            Examples: ["AAPL", "GOOGL", "MSFT"]
        start_date : datetime | str
            Start date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names (e.g., ["AAPL", "GOOGL"])

        Examples
        --------
        >>> provider = SomeDataProvider()
        >>> df = provider.get_volumes(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31),
        ... )
        >>> list(df.columns)
        ['AAPL', 'GOOGL']
        >>> df.index.name
        'Date'
        """
        ...

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch fundamental data for the specified symbols and metrics.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
            Examples: ["AAPL", "GOOGL", "MSFT"]
        metrics : list[str]
            List of fundamental metrics to fetch.
            Common metrics: ["per", "pbr", "roe", "roa", "eps", "dividend_yield"]
        start_date : datetime | str
            Start date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: MultiIndex with levels (symbol, metric)

        Examples
        --------
        >>> provider = SomeDataProvider()
        >>> df = provider.get_fundamentals(
        ...     symbols=["AAPL", "GOOGL"],
        ...     metrics=["per", "pbr", "roe"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ... )
        >>> df.columns.names
        ['symbol', 'metric']
        >>> list(df.columns.get_level_values("metric").unique())
        ['per', 'pbr', 'roe']
        """
        ...

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Fetch market capitalization data for the specified symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch data for.
            Examples: ["AAPL", "GOOGL", "MSFT"]
        start_date : datetime | str
            Start date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the data range.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            DataFrame with the following structure:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names (e.g., ["AAPL", "GOOGL"])

        Examples
        --------
        >>> provider = SomeDataProvider()
        >>> df = provider.get_market_cap(
        ...     symbols=["AAPL", "GOOGL"],
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31),
        ... )
        >>> list(df.columns)
        ['AAPL', 'GOOGL']
        >>> df.index.name
        'Date'
        """
        ...
