"""Bloomberg data processor for market data collection.

This module provides a concrete implementation of the DataCollector interface
for processing Bloomberg data from Excel files and storing to SQLite databases.

The BloombergDataProcessor class handles:
- Reading Bloomberg data from Excel files
- Filtering data by symbols
- Validating DataFrame structure
- Storing data to SQLite databases

Examples
--------
>>> from market.bloomberg_processor import BloombergDataProcessor
>>> processor = BloombergDataProcessor()
>>> df = processor.fetch(symbols=["AAPL", "GOOGL"], excel_path="/path/to/data.xlsx")
>>> if processor.validate(df):
...     processor.save_to_sqlite(df, "/path/to/db.sqlite", "bloomberg_data")
"""

import sqlite3
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from market.base_collector import DataCollector
from utils_core.logging import get_logger

logger = get_logger(__name__, module="market.bloomberg_processor")

# Required columns for valid Bloomberg data
REQUIRED_COLUMNS = {"symbol", "date", "price"}


class BloombergDataProcessor(DataCollector):
    """Data processor for Bloomberg market data.

    This class implements the DataCollector interface for processing
    Bloomberg data exported to Excel files. It provides functionality
    for reading, validating, and storing market data.

    Attributes
    ----------
    name : str
        The name of the data processor (returns class name)

    Examples
    --------
    >>> processor = BloombergDataProcessor()
    >>> df = processor.fetch(symbols=["AAPL"], excel_path="/path/to/data.xlsx")
    >>> processor.validate(df)
    True
    >>> processor.save_to_sqlite(df, "/path/to/db.sqlite", "prices")

    Notes
    -----
    The Excel file should contain at minimum the following columns:
    - symbol: Stock ticker symbol
    - date: Date of the price data
    - price: Price value
    """

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch Bloomberg data from an Excel file.

        This method reads data from an Excel file and optionally filters
        it by the specified symbols. If no excel_path is provided,
        returns an empty DataFrame.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments including:
            - symbols : list[str]
                List of stock symbols to fetch data for
            - excel_path : str | Path, optional
                Path to the Excel file containing Bloomberg data

        Returns
        -------
        pd.DataFrame
            DataFrame containing the fetched data, filtered by symbols
            if provided. Returns empty DataFrame if no excel_path is
            provided or symbols list is empty.

        Raises
        ------
        FileNotFoundError
            If the specified excel_path does not exist.

        Examples
        --------
        >>> processor = BloombergDataProcessor()
        >>> df = processor.fetch(symbols=["AAPL"], excel_path="/path/to/data.xlsx")
        >>> len(df)
        100
        """
        symbols: list[str] = kwargs.get("symbols", [])
        excel_path: str | Path | None = kwargs.get("excel_path")

        logger.debug(
            "Fetching Bloomberg data",
            symbols=symbols,
            excel_path=str(excel_path) if excel_path else None,
        )

        if not excel_path:
            logger.debug("No excel_path provided, returning empty DataFrame")
            return pd.DataFrame()

        if not symbols:
            logger.debug("No symbols provided, returning empty DataFrame")
            return pd.DataFrame()

        # Read and filter data
        df = self.read_excel(excel_path, symbols=symbols)

        logger.info(
            "Bloomberg data fetched successfully",
            row_count=len(df),
            symbols=symbols,
        )

        return df

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched Bloomberg data.

        This method checks that the DataFrame is not empty and contains
        the required columns for Bloomberg data (symbol, date, price).

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.

        Returns
        -------
        bool
            True if the DataFrame is valid (non-empty and has required
            columns), False otherwise.

        Examples
        --------
        >>> processor = BloombergDataProcessor()
        >>> df = pd.DataFrame({"symbol": ["AAPL"], "date": ["2024-01-01"], "price": [150.0]})
        >>> processor.validate(df)
        True
        >>> processor.validate(pd.DataFrame())
        False
        """
        logger.debug(
            "Validating Bloomberg data",
            row_count=len(df),
            columns=list(df.columns) if not df.empty else [],
        )

        if df.empty:
            logger.debug("Validation failed: DataFrame is empty")
            return False

        # Check for required columns
        missing_columns = REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            logger.debug(
                "Validation failed: missing required columns",
                missing_columns=list(missing_columns),
            )
            return False

        logger.debug("Validation passed")
        return True

    def read_excel(
        self,
        excel_path: str | Path,
        *,
        symbols: list[str] | None = None,
    ) -> pd.DataFrame:
        """Read Bloomberg data from an Excel file.

        Parameters
        ----------
        excel_path : str | Path
            Path to the Excel file.
        symbols : list[str] | None, optional
            List of symbols to filter by. If None, returns all data.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the Excel data, optionally filtered
            by symbols.

        Raises
        ------
        FileNotFoundError
            If the Excel file does not exist.

        Examples
        --------
        >>> processor = BloombergDataProcessor()
        >>> df = processor.read_excel("/path/to/data.xlsx", symbols=["AAPL"])
        """
        path = Path(excel_path)

        if not path.exists():
            logger.error("Excel file not found", path=str(path))
            msg = f"Excel file not found: {path}"
            raise FileNotFoundError(msg)

        logger.debug("Reading Excel file", path=str(path))

        df = pd.read_excel(path)

        logger.debug(
            "Excel file read successfully",
            row_count=len(df),
            columns=list(df.columns),
        )

        # Filter by symbols if provided
        if symbols and "symbol" in df.columns:
            mask = df["symbol"].isin(symbols)
            filtered_df = df.loc[mask, :]
            logger.debug(
                "Filtered by symbols",
                symbols=symbols,
                filtered_row_count=len(filtered_df),
            )
            return filtered_df

        return df

    def save_to_sqlite(
        self,
        df: pd.DataFrame,
        db_path: str | Path,
        table_name: str,
        *,
        if_exists: Literal["fail", "replace", "append"] = "replace",
    ) -> None:
        """Save DataFrame to SQLite database.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to save.
        db_path : str | Path
            Path to the SQLite database file.
        table_name : str
            Name of the table to save data to.
        if_exists : {'fail', 'replace', 'append'}, default 'replace'
            How to behave if the table already exists:
            - fail: Raise a ValueError
            - replace: Drop the table before inserting new values
            - append: Insert new values to the existing table

        Examples
        --------
        >>> processor = BloombergDataProcessor()
        >>> df = pd.DataFrame({"symbol": ["AAPL"], "price": [150.0]})
        >>> processor.save_to_sqlite(df, "/path/to/db.sqlite", "prices")
        """
        path = Path(db_path)

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving data to SQLite",
            db_path=str(path),
            table_name=table_name,
            row_count=len(df),
            if_exists=if_exists,
        )

        with sqlite3.connect(path) as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)

        logger.info(
            "Data saved to SQLite successfully",
            db_path=str(path),
            table_name=table_name,
        )


__all__ = ["BloombergDataProcessor"]
