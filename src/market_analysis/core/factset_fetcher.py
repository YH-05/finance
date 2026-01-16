"""FactSet data fetcher for market data retrieval.

This module provides a concrete implementation of BaseDataFetcher
for fetching market data from FactSet data files.

Note
----
FactSet data is typically delivered as files (Excel, Parquet) rather than
via a real-time API. This fetcher primarily loads pre-downloaded data.
For testing without FactSet, use the MockFactSetFetcher from mock_fetchers.py.
"""

import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import pandas as pd

from ..errors import DataFetchError, ErrorCode
from ..types import (
    CacheConfig,
    DataSource,
    FetchOptions,
    MarketDataResult,
    RetryConfig,
)
from ..utils.logging_config import get_logger
from .base_fetcher import BaseDataFetcher

logger = get_logger(__name__, module="factset_fetcher")

# FactSet P_SYMBOL pattern (e.g., AAPL-US, 7203-JP)
FACTSET_SYMBOL_PATTERN = re.compile(
    r"^[A-Z0-9]+-[A-Z]{2}$",
    re.IGNORECASE,
)

# Check if FactSet is available
FACTSET_AVAILABLE = os.environ.get("FACTSET_AVAILABLE", "false").lower() == "true"


class FactSetFetcher(BaseDataFetcher):
    """Data fetcher for FactSet data files.

    Fetches market data and financial data from FactSet-provided
    data files (Parquet, SQLite, etc.).

    Parameters
    ----------
    data_dir : str | Path | None
        Base directory containing FactSet data files.
        If None, uses FACTSET_ROOT_DIR environment variable.
    db_path : str | Path | None
        Path to SQLite database with FactSet data.
        If None, uses file-based loading.
    cache : SQLiteCache | None
        Cache instance for storing fetched data.
        If None, caching is disabled.
    cache_config : CacheConfig | None
        Configuration for cache behavior.
    retry_config : RetryConfig | None
        Configuration for retry behavior.

    Attributes
    ----------
    source : DataSource
        Always returns DataSource.FACTSET

    Examples
    --------
    >>> fetcher = FactSetFetcher(data_dir="/path/to/factset/data")
    >>> constituents = fetcher.load_constituents("M_US500")
    >>> financials = fetcher.load_financial_data(["FF_ROIC", "FF_ROE"])
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        db_path: str | Path | None = None,
        cache: Any | None = None,
        cache_config: CacheConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._data_dir = Path(data_dir) if data_dir else self._get_default_data_dir()
        self._db_path = Path(db_path) if db_path else None
        self._cache = cache
        self._cache_config = cache_config
        self._retry_config = retry_config

        logger.debug(
            "Initializing FactSetFetcher",
            data_dir=str(self._data_dir) if self._data_dir else None,
            db_path=str(self._db_path) if self._db_path else None,
            cache_enabled=cache is not None,
        )

    @staticmethod
    def _get_default_data_dir() -> Path | None:
        """Get default data directory from environment.

        Returns
        -------
        Path | None
            Path from FACTSET_ROOT_DIR env var, or None if not set
        """
        env_dir = os.environ.get("FACTSET_ROOT_DIR")
        return Path(env_dir) if env_dir else None

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.FACTSET
        """
        return DataSource.FACTSET

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for FactSet.

        FactSet P_SYMBOL format: TICKER-COUNTRY (e.g., AAPL-US)

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol matches FactSet format

        Examples
        --------
        >>> fetcher.validate_symbol("AAPL-US")
        True
        >>> fetcher.validate_symbol("7203-JP")
        True
        >>> fetcher.validate_symbol("AAPL")
        False
        """
        if not symbol or not symbol.strip():
            return False

        return bool(FACTSET_SYMBOL_PATTERN.match(symbol.strip()))

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch market data for the given options.

        Note: FactSet typically uses file-based data. This method
        attempts to load data from the configured data directory
        or database.

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
        self._validate_options(options)

        logger.info(
            "Fetching market data",
            symbols=options.symbols,
            start_date=str(options.start_date),
            end_date=str(options.end_date),
        )

        if self._db_path and self._db_path.exists():
            return self._fetch_from_database(options)
        elif self._data_dir and self._data_dir.exists():
            return self._fetch_from_files(options)
        else:
            raise DataFetchError(
                "No data source configured. Set data_dir or db_path.",
                symbol=",".join(options.symbols),
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

    def load_constituents(
        self,
        universe_code: str,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
    ) -> pd.DataFrame:
        """Load index constituents for a given universe.

        Parameters
        ----------
        universe_code : str
            The universe/index code (e.g., M_US500, M_JAPAN)
        start_date : str | datetime | None
            Start date for filtering
        end_date : str | datetime | None
            End date for filtering

        Returns
        -------
        pd.DataFrame
            DataFrame with constituents data including:
            - date: observation date
            - P_SYMBOL: FactSet symbol
            - SEDOL: SEDOL identifier
            - Asset ID: Asset identifier
            - FG_COMPANY_NAME: Company name
            - GICS Sector: Sector classification
            - GICS Industry Group: Industry group
            - Weight (%): Portfolio weight

        Raises
        ------
        DataFetchError
            If loading fails

        Examples
        --------
        >>> df = fetcher.load_constituents(
        ...     universe_code="M_US500",
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ... )
        """
        logger.info(
            "Loading constituents",
            universe_code=universe_code,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        if self._db_path and self._db_path.exists():
            return self._load_constituents_from_db(universe_code, start_date, end_date)
        elif self._data_dir and self._data_dir.exists():
            return self._load_constituents_from_file(
                universe_code, start_date, end_date
            )
        else:
            raise DataFetchError(
                "No data source configured for constituents.",
                symbol=universe_code,
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

    def load_financial_data(
        self,
        factor_list: list[str],
        db_path: str | Path | None = None,
    ) -> pd.DataFrame:
        """Load financial data for specified factors.

        Parameters
        ----------
        factor_list : list[str]
            List of factor/field names to load (e.g., FF_ROIC, FF_ROE)
        db_path : str | Path | None
            Optional database path override

        Returns
        -------
        pd.DataFrame
            DataFrame with financial data in wide format, columns:
            - date: observation date
            - P_SYMBOL: FactSet symbol
            - [factor columns]: one column per factor

        Raises
        ------
        DataFetchError
            If loading fails

        Examples
        --------
        >>> df = fetcher.load_financial_data(
        ...     factor_list=["FF_ROIC", "FF_ROE", "FF_SALES"],
        ... )
        """
        logger.info(
            "Loading financial data",
            factor_count=len(factor_list),
            factors=factor_list[:5],  # Log first 5
        )

        target_db = Path(db_path) if db_path else self._db_path

        if target_db is None or not target_db.exists():
            raise DataFetchError(
                "Database path not configured or does not exist.",
                symbol=",".join(factor_list[:5]),
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        # Build UNION ALL query
        # nosec B608 - factor_list contains internal table names, not user input
        query = """
            SELECT `date`, `P_SYMBOL`, `variable`, `value` FROM {}
        """.format(
            "\n    UNION ALL\n    SELECT `date`, `P_SYMBOL`, `variable`, `value` FROM ".join(
                factor_list
            )
        )

        try:
            with sqlite3.connect(target_db) as conn:
                df = pd.read_sql(query, parse_dates=["date"], con=conn)

            # Adjust date to month end
            df["date"] = pd.to_datetime(df["date"]) + pd.offsets.MonthEnd(0)
            df = df.drop_duplicates(ignore_index=True)

            # Pivot to wide format
            df_wide = pd.pivot(
                df,
                index=["date", "P_SYMBOL"],
                columns="variable",
                values="value",
            ).reset_index()

            logger.info(
                "Financial data loaded",
                rows=len(df_wide),
                columns=list(df_wide.columns),
            )

            return df_wide

        except Exception as e:
            logger.error("Failed to load financial data", error=str(e))
            raise DataFetchError(
                f"Failed to load financial data: {e}",
                symbol=",".join(factor_list[:5]),
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
                cause=e,
            ) from e

    def _fetch_from_database(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch data from SQLite database.

        Parameters
        ----------
        options : FetchOptions
            Fetch options

        Returns
        -------
        list[MarketDataResult]
            List of results
        """
        results: list[MarketDataResult] = []

        assert self._db_path is not None  # nosec B101

        try:
            with sqlite3.connect(self._db_path) as conn:
                for symbol in options.symbols:
                    # Query for price data
                    query = """
                        SELECT date, value as close
                        FROM FG_PRICE
                        WHERE P_SYMBOL = ?
                    """
                    params: list[Any] = [symbol]

                    if options.start_date:
                        query += " AND date >= ?"
                        params.append(self._format_date(options.start_date))

                    if options.end_date:
                        query += " AND date <= ?"
                        params.append(self._format_date(options.end_date))

                    query += " ORDER BY date"

                    df = pd.read_sql(query, conn, params=params, parse_dates=["date"])

                    if df.empty:
                        logger.warning("No data found for symbol", symbol=symbol)
                        results.append(
                            self._create_result(
                                symbol=symbol,
                                data=pd.DataFrame(
                                    columns=pd.Index(
                                        ["open", "high", "low", "close", "volume"]
                                    )
                                ),
                                from_cache=False,
                            )
                        )
                        continue

                    df = df.set_index("date")
                    # Fill missing OHLCV columns with close or NaN
                    df["open"] = df["close"]
                    df["high"] = df["close"]
                    df["low"] = df["close"]
                    df["volume"] = pd.NA

                    normalized = self.normalize_dataframe(df, symbol)

                    results.append(
                        self._create_result(
                            symbol=symbol,
                            data=normalized,
                            from_cache=False,
                            metadata={"source": "factset_db"},
                        )
                    )

        except Exception as e:
            logger.error("Database fetch failed", error=str(e))
            raise DataFetchError(
                f"Failed to fetch from database: {e}",
                symbol=",".join(options.symbols),
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
                cause=e,
            ) from e

        return results

    def _fetch_from_files(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch data from Parquet files.

        Parameters
        ----------
        options : FetchOptions
            Fetch options

        Returns
        -------
        list[MarketDataResult]
            List of results
        """
        results: list[MarketDataResult] = []

        assert self._data_dir is not None  # nosec B101

        # Look for price data files
        price_files = list(self._data_dir.glob("**/Price*.parquet"))

        if not price_files:
            logger.warning("No price files found", data_dir=str(self._data_dir))

        for symbol in options.symbols:
            found = False

            for price_file in price_files:
                try:
                    df = pd.read_parquet(price_file)

                    if "P_SYMBOL" in df.columns and symbol in df["P_SYMBOL"].values:
                        mask = df["P_SYMBOL"] == symbol
                        df_symbol = df.loc[mask].copy()
                        assert isinstance(df_symbol, pd.DataFrame)

                        if "date" in df_symbol.columns:
                            df_symbol["date"] = pd.to_datetime(df_symbol["date"])
                            df_symbol = df_symbol.set_index("date")

                        # Apply date filters
                        if options.start_date:
                            start = pd.to_datetime(options.start_date)
                            df_symbol = df_symbol.loc[df_symbol.index >= start]

                        if options.end_date:
                            end = pd.to_datetime(options.end_date)
                            df_symbol = df_symbol.loc[df_symbol.index <= end]

                        if not df_symbol.empty:
                            # Prepare OHLCV format
                            if "value" in df_symbol.columns:
                                df_symbol["close"] = df_symbol["value"]
                                df_symbol["open"] = df_symbol["value"]
                                df_symbol["high"] = df_symbol["value"]
                                df_symbol["low"] = df_symbol["value"]
                            df_symbol["volume"] = pd.NA

                            normalized = self.normalize_dataframe(df_symbol, symbol)

                            results.append(
                                self._create_result(
                                    symbol=symbol,
                                    data=normalized,
                                    from_cache=False,
                                    metadata={"source": "factset_file"},
                                )
                            )
                            found = True
                            break

                except Exception as e:
                    logger.debug(
                        "Error reading price file",
                        file=str(price_file),
                        error=str(e),
                    )

            if not found:
                logger.warning("No data found for symbol", symbol=symbol)
                results.append(
                    self._create_result(
                        symbol=symbol,
                        data=pd.DataFrame(
                            columns=pd.Index(["open", "high", "low", "close", "volume"])
                        ),
                        from_cache=False,
                    )
                )

        return results

    def _load_constituents_from_db(
        self,
        universe_code: str,
        start_date: str | datetime | None,
        end_date: str | datetime | None,
    ) -> pd.DataFrame:
        """Load constituents from database.

        Parameters
        ----------
        universe_code : str
            Universe code
        start_date : str | datetime | None
            Start date
        end_date : str | datetime | None
            End date

        Returns
        -------
        pd.DataFrame
            Constituents data
        """
        assert self._db_path is not None  # nosec B101

        # nosec B608 - universe_code is internal index name, not user input
        query = f"""
            SELECT
                `date`, `P_SYMBOL`, `SEDOL`, `Asset ID`, `FG_COMPANY_NAME`,
                `GICS Sector`, `GICS Industry Group`,
                `Weight (%)`
            FROM
                {universe_code}
        """

        with sqlite3.connect(self._db_path) as conn:
            df: pd.DataFrame = pd.read_sql(query, con=conn, parse_dates=["date"])

        # Apply date filters
        if start_date:
            start = pd.to_datetime(start_date)
            df = df.loc[df["date"] >= start]

        if end_date:
            end = pd.to_datetime(end_date)
            df = df.loc[df["date"] <= end]

        logger.info(
            "Constituents loaded from database",
            universe_code=universe_code,
            rows=len(df),
        )

        return df

    def _load_constituents_from_file(
        self,
        universe_code: str,
        start_date: str | datetime | None,
        end_date: str | datetime | None,
    ) -> pd.DataFrame:
        """Load constituents from Parquet file.

        Parameters
        ----------
        universe_code : str
            Universe code
        start_date : str | datetime | None
            Start date
        end_date : str | datetime | None
            End date

        Returns
        -------
        pd.DataFrame
            Constituents data
        """
        assert self._data_dir is not None  # nosec B101

        # Look for constituents file
        patterns = [
            f"**/{universe_code}*Constituents*.parquet",
            f"**/Index_Constituents/{universe_code}*.parquet",
            f"**/*{universe_code}*.parquet",
        ]

        file_path = None
        for pattern in patterns:
            files = list(self._data_dir.glob(pattern))
            if files:
                file_path = files[0]
                break

        if file_path is None:
            raise DataFetchError(
                f"No constituents file found for {universe_code}",
                symbol=universe_code,
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        df: pd.DataFrame = pd.read_parquet(file_path)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

            if start_date:
                start = pd.to_datetime(start_date)
                df = df.loc[df["date"] >= start]

            if end_date:
                end = pd.to_datetime(end_date)
                df = df.loc[df["date"] <= end]

        logger.info(
            "Constituents loaded from file",
            universe_code=universe_code,
            file=str(file_path),
            rows=len(df),
        )

        return df

    def _format_date(self, date: datetime | str | None) -> str | None:
        """Format a date for database queries.

        Parameters
        ----------
        date : datetime | str | None
            Date to format

        Returns
        -------
        str | None
            Formatted date string (YYYY-MM-DD) or None
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)

    @contextmanager
    def database_connection(
        self,
        db_path: str | Path | None = None,
    ) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connection.

        Parameters
        ----------
        db_path : str | Path | None
            Optional override for database path

        Yields
        ------
        sqlite3.Connection
            Database connection

        Examples
        --------
        >>> with fetcher.database_connection() as conn:
        ...     df = pd.read_sql("SELECT * FROM table", conn)
        """
        target_path = Path(db_path) if db_path else self._db_path

        if target_path is None:
            raise DataFetchError(
                "No database path configured",
                symbol="",
                source=self.source.value,
                code=ErrorCode.DATA_NOT_FOUND,
            )

        conn = sqlite3.connect(target_path)
        try:
            yield conn
        finally:
            conn.close()


__all__ = [
    "FACTSET_AVAILABLE",
    "FACTSET_SYMBOL_PATTERN",
    "FactSetFetcher",
]
