"""DuckDB client for analytics."""

from pathlib import Path

import duckdb
import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__)


class DuckDBClient:
    """DuckDB analytics client.

    Parameters
    ----------
    db_path : Path
        Path to DuckDB database file

    Examples
    --------
    >>> from database.db import DuckDBClient, get_db_path
    >>> client = DuckDBClient(get_db_path("duckdb", "analytics"))
    >>> df = client.query_df("SELECT 1 as value")
    >>> df['value'].iloc[0]
    1
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("DuckDBClient initialized", db_path=str(db_path))

    @property
    def path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    def query_df(self, sql: str) -> pd.DataFrame:
        """Execute query and return DataFrame.

        Parameters
        ----------
        sql : str
            SQL query to execute

        Returns
        -------
        pd.DataFrame
            Query results as DataFrame
        """
        logger.debug("Executing DuckDB query", sql_preview=sql[:100])
        with duckdb.connect(str(self._db_path)) as conn:
            result = conn.execute(sql).fetchdf()
            logger.debug("Query completed", row_count=len(result))
            return result

    def execute(self, sql: str) -> None:
        """Execute SQL without returning results.

        Parameters
        ----------
        sql : str
            SQL to execute
        """
        logger.debug("Executing DuckDB SQL", sql_preview=sql[:100])
        with duckdb.connect(str(self._db_path)) as conn:
            conn.execute(sql)

    def read_parquet(self, pattern: str) -> pd.DataFrame:
        """Read Parquet files matching pattern.

        Parameters
        ----------
        pattern : str
            Glob pattern for Parquet files

        Returns
        -------
        pd.DataFrame
            Combined data from matching files

        Examples
        --------
        >>> client = DuckDBClient(get_db_path("duckdb", "analytics"))
        >>> df = client.read_parquet("data/raw/yfinance/stocks/*.parquet")
        """
        sql = f"SELECT * FROM read_parquet('{pattern}')"  # nosec B608
        return self.query_df(sql)

    def write_parquet(self, df: pd.DataFrame, path: str | Path) -> None:
        """Write DataFrame to Parquet file.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to write
        path : str | Path
            Output path for Parquet file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Writing Parquet file", path=str(path), row_count=len(df))
        with duckdb.connect(str(self._db_path)) as conn:
            conn.execute(f"COPY df TO '{path}' (FORMAT PARQUET)")
        logger.info("Parquet file written", path=str(path))
