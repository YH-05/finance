"""Base data fetcher abstract class for market data retrieval.

This module provides the abstract base class for all data fetchers,
defining the common interface and shared functionality for fetching
market data from various sources (yfinance, FRED, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import pandas as pd

from ..errors import DataFetchError, ErrorCode, ValidationError
from ..types import DataSource, FetchOptions, Interval, MarketDataResult


# Lazy logger initialization to avoid circular imports
def _get_logger() -> Any:
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="base_fetcher")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# Standard OHLCV column names
STANDARD_COLUMNS = ["open", "high", "low", "close", "volume"]


class BaseDataFetcher(ABC):
    """Abstract base class for market data fetchers.

    This class defines the common interface for all data fetchers
    and provides shared functionality for data normalization.

    Subclasses must implement:
    - fetch(): Retrieve data from the source
    - validate_symbol(): Validate symbol format for the source

    Attributes
    ----------
    source : DataSource
        The data source type (YFINANCE, FRED, etc.)
    default_interval : Interval
        Default data interval for this fetcher

    Examples
    --------
    >>> class MyFetcher(BaseDataFetcher):
    ...     @property
    ...     def source(self) -> DataSource:
    ...         return DataSource.YFINANCE
    ...
    ...     def fetch(self, options: FetchOptions) -> list[MarketDataResult]:
    ...         # Implementation here
    ...         pass
    ...
    ...     def validate_symbol(self, symbol: str) -> bool:
    ...         return bool(symbol and symbol.isalnum())
    """

    @property
    @abstractmethod
    def source(self) -> DataSource:
        """Return the data source type for this fetcher.

        Returns
        -------
        DataSource
            The data source enum value
        """
        ...

    @property
    def default_interval(self) -> Interval:
        """Return the default data interval.

        Returns
        -------
        Interval
            The default interval (DAILY by default)
        """
        return Interval.DAILY

    @abstractmethod
    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch market data for the given options.

        Parameters
        ----------
        options : FetchOptions
            Options specifying symbols, date range, and other parameters

        Returns
        -------
        list[MarketDataResult]
            List of results for each requested symbol

        Raises
        ------
        DataFetchError
            If fetching fails for any symbol
        ValidationError
            If options contain invalid parameters
        """
        ...

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for this data source.

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol is valid, False otherwise

        Examples
        --------
        >>> fetcher.validate_symbol("AAPL")
        True
        >>> fetcher.validate_symbol("")
        False
        """
        ...

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """Normalize a DataFrame to standard OHLCV format.

        This method standardizes column names to lowercase and ensures
        the DataFrame has the expected OHLCV columns. Missing columns
        are filled with NaN values.

        Parameters
        ----------
        df : pd.DataFrame
            The raw DataFrame to normalize
        symbol : str
            The symbol for logging purposes

        Returns
        -------
        pd.DataFrame
            Normalized DataFrame with standard column names

        Raises
        ------
        DataFetchError
            If the DataFrame cannot be normalized

        Examples
        --------
        >>> raw_df = pd.DataFrame({"Open": [100], "High": [105], ...})
        >>> normalized = fetcher.normalize_dataframe(raw_df, "AAPL")
        >>> list(normalized.columns)
        ['open', 'high', 'low', 'close', 'volume']
        """
        logger.debug(
            "Normalizing DataFrame",
            symbol=symbol,
            original_columns=list(df.columns),
            row_count=len(df),
        )

        if df.empty:
            logger.warning(
                "Empty DataFrame received",
                symbol=symbol,
            )
            return pd.DataFrame(columns=pd.Index(STANDARD_COLUMNS))

        # Create a copy to avoid modifying the original
        normalized = df.copy()

        # Normalize column names to lowercase
        normalized.columns = normalized.columns.str.lower()

        # Handle multi-level columns (common in yfinance)
        if isinstance(normalized.columns, pd.MultiIndex):
            logger.debug(
                "Flattening multi-level columns",
                symbol=symbol,
                levels=normalized.columns.nlevels,
            )
            normalized.columns = normalized.columns.get_level_values(0)

        # Map common column name variations
        column_mapping = {
            "adj close": "close",
            "adjusted close": "close",
            "adj_close": "close",
            "vol": "volume",
        }

        for old_name, new_name in column_mapping.items():
            if old_name in normalized.columns and new_name not in normalized.columns:
                normalized = normalized.rename(columns={old_name: new_name})
                logger.debug(
                    "Renamed column",
                    symbol=symbol,
                    old_name=old_name,
                    new_name=new_name,
                )

        # Ensure all standard columns exist
        for col in STANDARD_COLUMNS:
            if col not in normalized.columns:
                logger.debug(
                    "Adding missing column with NaN",
                    symbol=symbol,
                    column=col,
                )
                normalized[col] = pd.NA

        # Select only standard columns in order
        try:
            selected = normalized[STANDARD_COLUMNS]
            # When indexing with a list, pandas returns a DataFrame
            assert isinstance(selected, pd.DataFrame)
            normalized = selected
        except KeyError as e:
            logger.error(
                "Failed to select standard columns",
                symbol=symbol,
                available_columns=list(df.columns),
                error=str(e),
            )
            raise DataFetchError(
                f"Failed to normalize DataFrame for {symbol}: missing required columns",
                symbol=symbol,
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
                cause=e,
            ) from e

        # Ensure index is DatetimeIndex
        if not isinstance(normalized.index, pd.DatetimeIndex):
            logger.debug(
                "Converting index to DatetimeIndex",
                symbol=symbol,
                original_type=type(normalized.index).__name__,
            )
            try:
                normalized.index = pd.to_datetime(normalized.index)
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Failed to convert index to DatetimeIndex",
                    symbol=symbol,
                    error=str(e),
                )

        # Sort by date
        normalized = normalized.sort_index()

        logger.debug(
            "DataFrame normalization completed",
            symbol=symbol,
            final_columns=list(normalized.columns),
            row_count=len(normalized),
            date_range=(
                f"{normalized.index.min()} to {normalized.index.max()}"
                if not normalized.empty
                else "empty"
            ),
        )

        return normalized

    def _validate_options(self, options: FetchOptions) -> None:
        """Validate fetch options before processing.

        Parameters
        ----------
        options : FetchOptions
            The options to validate

        Raises
        ------
        ValidationError
            If options are invalid
        """
        logger.debug(
            "Validating fetch options",
            symbol_count=len(options.symbols),
            start_date=options.start_date,
            end_date=options.end_date,
            interval=options.interval.value,
        )

        if not options.symbols:
            logger.error("No symbols provided")
            raise ValidationError(
                "At least one symbol must be provided",
                field="symbols",
                value=options.symbols,
                code=ErrorCode.INVALID_PARAMETER,
            )

        # Validate each symbol
        invalid_symbols = [s for s in options.symbols if not self.validate_symbol(s)]
        if invalid_symbols:
            logger.error(
                "Invalid symbols found",
                invalid_symbols=invalid_symbols,
                source=self.source.value,
            )
            raise ValidationError(
                f"Invalid symbols for {self.source.value}: {invalid_symbols}",
                field="symbols",
                value=invalid_symbols,
                code=ErrorCode.INVALID_SYMBOL,
            )

        logger.debug("Fetch options validated successfully")

    def _create_result(
        self,
        symbol: str,
        data: pd.DataFrame,
        from_cache: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> MarketDataResult:
        """Create a MarketDataResult from fetched data.

        Parameters
        ----------
        symbol : str
            The symbol that was fetched
        data : pd.DataFrame
            The fetched and normalized data
        from_cache : bool
            Whether data was retrieved from cache
        metadata : dict[str, Any] | None
            Additional metadata to include

        Returns
        -------
        MarketDataResult
            The result object
        """
        result = MarketDataResult(
            symbol=symbol,
            data=data,
            source=self.source,
            fetched_at=datetime.now(),
            from_cache=from_cache,
            metadata=metadata or {},
        )

        logger.debug(
            "Created MarketDataResult",
            symbol=symbol,
            row_count=result.row_count,
            from_cache=from_cache,
            source=self.source.value,
        )

        return result


__all__ = [
    "BaseDataFetcher",
    "STANDARD_COLUMNS",
]
