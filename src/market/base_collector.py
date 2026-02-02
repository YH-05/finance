"""Base data collector abstract class for market data collection.

This module provides the abstract base class for all data collectors,
defining the common interface for fetching and validating market data
from various external sources.

Examples
--------
>>> from market.base_collector import DataCollector
>>> class MyDataCollector(DataCollector):
...     def fetch(self, symbol: str = "DEFAULT", **kwargs) -> pd.DataFrame:
...         # Fetch data from external source
...         return pd.DataFrame({"value": [1, 2, 3]})
...
...     def validate(self, df: pd.DataFrame) -> bool:
...         return not df.empty and "value" in df.columns
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


class DataCollector(ABC):
    """Abstract base class for data collectors.

    This class defines the common interface for all data collectors,
    providing a standardized way to fetch and validate data from
    various external sources.

    Subclasses must implement:
    - fetch(): Retrieve data from the source
    - validate(): Validate the fetched data

    Attributes
    ----------
    name : str
        The name of the data collector (defaults to class name)

    Examples
    --------
    >>> class TSAPassengerDataCollector(DataCollector):
    ...     def fetch(self, **kwargs) -> pd.DataFrame:
    ...         # Fetch TSA passenger data
    ...         return pd.DataFrame({"passengers": [1000, 2000]})
    ...
    ...     def validate(self, df: pd.DataFrame) -> bool:
    ...         return not df.empty and "passengers" in df.columns
    ...
    >>> collector = TSAPassengerDataCollector()
    >>> data = collector.collect()  # Fetches and validates data
    """

    @property
    def name(self) -> str:
        """Return the name of this data collector.

        Returns
        -------
        str
            The collector name (defaults to class name)

        Examples
        --------
        >>> collector = MyDataCollector()
        >>> collector.name
        'MyDataCollector'
        """
        return self.__class__.__name__

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch data from the external source.

        This method should retrieve raw data from the external source
        and return it as a pandas DataFrame. The implementation should
        handle any necessary API calls, authentication, and error handling.

        Parameters
        ----------
        **kwargs : Any
            Additional keyword arguments specific to the data source.
            Common arguments include:
            - start_date: Start date for data range
            - end_date: End date for data range
            - symbol: Symbol or identifier for the data

        Returns
        -------
        pd.DataFrame
            The fetched data as a DataFrame. The structure depends on
            the specific data source.

        Raises
        ------
        DataCollectionError
            If the data cannot be fetched from the source.
        ConnectionError
            If there is a network connectivity issue.

        Examples
        --------
        >>> collector = MyDataCollector()
        >>> df = collector.fetch(start_date="2024-01-01")
        >>> df.head()
           date       value
        0  2024-01-01  100.0
        1  2024-01-02  105.5
        """
        ...

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched data.

        This method should verify that the fetched data meets the
        expected format and quality requirements. It checks for
        required columns, data types, and data integrity.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = MyDataCollector()
        >>> df = pd.DataFrame({"value": [1, 2, 3]})
        >>> collector.validate(df)
        True
        >>> collector.validate(pd.DataFrame())
        False
        """
        ...

    def collect(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch and validate data in a single operation.

        This convenience method combines fetch() and validate() to
        provide a simple interface for data collection. It logs the
        collection process and raises an error if validation fails.

        Parameters
        ----------
        **kwargs : Any
            Additional keyword arguments passed to fetch().

        Returns
        -------
        pd.DataFrame
            The validated fetched data.

        Raises
        ------
        ValueError
            If the fetched data fails validation.

        Examples
        --------
        >>> collector = MyDataCollector()
        >>> df = collector.collect(start_date="2024-01-01")
        >>> print(f"Collected {len(df)} rows")
        Collected 30 rows
        """
        logger.info(
            "Starting data collection",
            collector=self.name,
            kwargs=str(kwargs) if kwargs else "none",
        )

        df = self.fetch(**kwargs)

        logger.debug(
            "Data fetched successfully",
            collector=self.name,
            row_count=len(df),
            columns=list(df.columns) if not df.empty else [],
        )

        if not self.validate(df):
            logger.error(
                "Data validation failed",
                collector=self.name,
                row_count=len(df),
            )
            msg = f"Data validation failed for {self.name}"
            raise ValueError(msg)

        logger.info(
            "Data collection completed",
            collector=self.name,
            row_count=len(df),
        )

        return df


__all__ = ["DataCollector"]
