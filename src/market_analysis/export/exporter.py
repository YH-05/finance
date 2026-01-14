"""Data exporter for market analysis results.

This module provides the DataExporter class for exporting market data
to various formats including JSON, CSV, SQLite, and AI agent-optimized JSON.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from market_analysis.errors import ExportError
from market_analysis.types import (
    AgentOutput,
    AgentOutputMetadata,
    AnalysisResult,
    MarketDataResult,
)
from market_analysis.utils import get_logger

logger = get_logger(__name__, module="export")

# Default date format for exports
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# Schema version for agent output
AGENT_OUTPUT_VERSION = "1.0"


class DataExporter:
    """Export market data to various formats.

    This class provides methods for exporting MarketDataResult and
    AnalysisResult objects to JSON, CSV, SQLite, and AI agent-optimized formats.

    Parameters
    ----------
    result : MarketDataResult | AnalysisResult
        The data result to export
    date_format : str
        Date format string for serialization (default: "%Y-%m-%d")

    Examples
    --------
    >>> from market_analysis import MarketDataResult, DataSource
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> data = pd.DataFrame({
    ...     "open": [100.0],
    ...     "high": [105.0],
    ...     "low": [99.0],
    ...     "close": [104.0],
    ...     "volume": [1000000],
    ... }, index=pd.DatetimeIndex(["2024-01-01"]))
    >>> result = MarketDataResult(
    ...     symbol="AAPL",
    ...     data=data,
    ...     source=DataSource.YFINANCE,
    ...     fetched_at=datetime.now(),
    ... )
    >>> exporter = DataExporter(result)
    >>> json_str = exporter.to_json()
    """

    def __init__(
        self,
        result: MarketDataResult | AnalysisResult,
        date_format: str = DEFAULT_DATE_FORMAT,
    ) -> None:
        self._result = result
        self._date_format = date_format
        logger.debug(
            "DataExporter initialized",
            symbol=result.symbol,
            result_type=type(result).__name__,
            date_format=date_format,
        )

    @property
    def result(self) -> MarketDataResult | AnalysisResult:
        """Get the underlying result object."""
        return self._result

    @property
    def data(self) -> pd.DataFrame:
        """Get the data DataFrame."""
        return self._result.data

    @property
    def symbol(self) -> str:
        """Get the symbol."""
        return self._result.symbol

    def to_json(
        self,
        output_path: str | Path | None = None,
        indent: int = 2,
        include_metadata: bool = True,
    ) -> str:
        """Export data to JSON format.

        Parameters
        ----------
        output_path : str | Path | None
            Optional file path to write JSON. If None, returns JSON string only.
        indent : int
            JSON indentation level (default: 2)
        include_metadata : bool
            Whether to include metadata in output (default: True)

        Returns
        -------
        str
            JSON string representation of the data

        Raises
        ------
        ExportError
            If JSON serialization or file writing fails

        Examples
        --------
        >>> exporter = DataExporter(result)
        >>> json_str = exporter.to_json()
        >>> exporter.to_json(output_path="./data/output.json")
        """
        logger.debug(
            "Exporting to JSON",
            symbol=self.symbol,
            output_path=str(output_path) if output_path else None,
            include_metadata=include_metadata,
        )

        try:
            export_data = self._prepare_export_data(include_metadata)
            json_str = json.dumps(export_data, indent=indent, ensure_ascii=False)

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json_str, encoding="utf-8")
                logger.info(
                    "JSON export completed",
                    symbol=self.symbol,
                    output_path=str(path),
                    size_bytes=len(json_str),
                )

            return json_str

        except (OSError, TypeError, ValueError) as e:
            logger.error(
                "JSON export failed",
                symbol=self.symbol,
                error=str(e),
                exc_info=True,
            )
            raise ExportError(
                f"Failed to export to JSON: {e}",
                format="json",
                path=str(output_path) if output_path else None,
                cause=e,
            ) from e

    def to_csv(
        self,
        output_path: str | Path | None = None,
        date_format: str | None = None,
        include_index: bool = True,
    ) -> str:
        """Export data to CSV format.

        Parameters
        ----------
        output_path : str | Path | None
            Optional file path to write CSV. If None, returns CSV string only.
        date_format : str | None
            Date format string. If None, uses instance default.
        include_index : bool
            Whether to include the index column (default: True)

        Returns
        -------
        str
            CSV string representation of the data

        Raises
        ------
        ExportError
            If CSV serialization or file writing fails

        Examples
        --------
        >>> exporter = DataExporter(result)
        >>> csv_str = exporter.to_csv()
        >>> exporter.to_csv(output_path="./data/output.csv")
        """
        date_fmt = date_format or self._date_format

        logger.debug(
            "Exporting to CSV",
            symbol=self.symbol,
            output_path=str(output_path) if output_path else None,
            date_format=date_fmt,
        )

        try:
            df = self.data.copy()

            if include_index and isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                if "index" in df.columns:
                    df = df.rename(columns={"index": "date"})
                if "date" in df.columns:
                    df["date"] = df["date"].dt.strftime(date_fmt)

            csv_str = df.to_csv(index=False)

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(csv_str, encoding="utf-8")
                logger.info(
                    "CSV export completed",
                    symbol=self.symbol,
                    output_path=str(path),
                    rows=len(df),
                )

            return csv_str

        except (OSError, ValueError) as e:
            logger.error(
                "CSV export failed",
                symbol=self.symbol,
                error=str(e),
                exc_info=True,
            )
            raise ExportError(
                f"Failed to export to CSV: {e}",
                format="csv",
                path=str(output_path) if output_path else None,
                cause=e,
            ) from e

    def to_sqlite(
        self,
        db_path: str | Path,
        table_name: str | None = None,
        if_exists: str = "upsert",
    ) -> int:
        """Export data to SQLite database with UPSERT support.

        Parameters
        ----------
        db_path : str | Path
            Path to SQLite database file
        table_name : str | None
            Table name. If None, uses "market_data_{symbol}".
        if_exists : str
            How to handle existing data:
            - "upsert": Update existing rows, insert new ones (default)
            - "replace": Drop and recreate table
            - "append": Append to existing table
            - "fail": Raise error if table exists

        Returns
        -------
        int
            Number of rows written/updated

        Raises
        ------
        ExportError
            If database operation fails

        Examples
        --------
        >>> exporter = DataExporter(result)
        >>> rows = exporter.to_sqlite("./data/market.db")
        >>> rows = exporter.to_sqlite("./data/market.db", if_exists="replace")
        """
        table = table_name or f"market_data_{self.symbol.lower().replace('^', '_')}"
        path = Path(db_path)

        logger.debug(
            "Exporting to SQLite",
            symbol=self.symbol,
            db_path=str(path),
            table_name=table,
            if_exists=if_exists,
        )

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            df = self._prepare_dataframe_for_sqlite()

            if if_exists == "upsert":
                rows_affected = self._upsert_to_sqlite(path, table, df)
            else:
                with sqlite3.connect(path) as conn:
                    df.to_sql(
                        table,
                        conn,
                        if_exists=if_exists,  # type: ignore[arg-type]
                        index=False,
                    )
                    rows_affected = len(df)

            logger.info(
                "SQLite export completed",
                symbol=self.symbol,
                db_path=str(path),
                table_name=table,
                rows_affected=rows_affected,
            )

            return rows_affected

        except (OSError, sqlite3.Error, ValueError) as e:
            logger.error(
                "SQLite export failed",
                symbol=self.symbol,
                db_path=str(path),
                error=str(e),
                exc_info=True,
            )
            raise ExportError(
                f"Failed to export to SQLite: {e}",
                format="sqlite",
                path=str(path),
                cause=e,
            ) from e

    def to_agent_json(
        self,
        output_path: str | Path | None = None,
        source_module: str = "market_analysis",
        include_recommendations: bool = True,
    ) -> AgentOutput:
        """Export data in AI agent-optimized JSON format.

        This format includes comprehensive metadata for AI agents including:
        - Generation timestamp and version
        - Data source and symbol information
        - Summary statistics
        - Optional recommendations

        Parameters
        ----------
        output_path : str | Path | None
            Optional file path to write JSON.
        source_module : str
            Source module identifier (default: "market_analysis")
        include_recommendations : bool
            Whether to generate recommendations (default: True)

        Returns
        -------
        AgentOutput
            Structured output object for AI agents

        Raises
        ------
        ExportError
            If export fails

        Examples
        --------
        >>> exporter = DataExporter(result)
        >>> agent_output = exporter.to_agent_json()
        >>> print(agent_output.summary)
        """
        logger.debug(
            "Exporting to agent JSON",
            symbol=self.symbol,
            output_path=str(output_path) if output_path else None,
            source_module=source_module,
        )

        try:
            metadata = self._build_agent_metadata(source_module)
            summary = self._generate_summary()
            data = self._prepare_agent_data()
            recommendations = (
                self._generate_recommendations() if include_recommendations else []
            )

            agent_output = AgentOutput(
                metadata=metadata,
                summary=summary,
                data=data,
                recommendations=recommendations,
            )

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                json_str = json.dumps(
                    agent_output.to_dict(),
                    indent=2,
                    ensure_ascii=False,
                )
                path.write_text(json_str, encoding="utf-8")
                logger.info(
                    "Agent JSON export completed",
                    symbol=self.symbol,
                    output_path=str(path),
                )

            return agent_output

        except (OSError, TypeError, ValueError) as e:
            logger.error(
                "Agent JSON export failed",
                symbol=self.symbol,
                error=str(e),
                exc_info=True,
            )
            raise ExportError(
                f"Failed to export to agent JSON: {e}",
                format="agent_json",
                path=str(output_path) if output_path else None,
                cause=e,
            ) from e

    def _prepare_export_data(self, include_metadata: bool) -> dict[str, Any]:
        """Prepare data dictionary for JSON export."""
        df = self.data.copy()

        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            if "index" in df.columns:
                df = df.rename(columns={"index": "date"})
            if "date" in df.columns:
                df["date"] = df["date"].dt.strftime(self._date_format)

        records = df.to_dict(orient="records")

        if not include_metadata:
            return {"symbol": self.symbol, "data": records}

        result_dict: dict[str, Any] = {
            "symbol": self.symbol,
            "data": records,
            "row_count": len(records),
            "columns": list(df.columns),
        }

        if isinstance(self._result, MarketDataResult):
            result_dict["source"] = self._result.source.value
            result_dict["fetched_at"] = self._result.fetched_at.isoformat()
            result_dict["from_cache"] = self._result.from_cache
            if self._result.metadata:
                result_dict["metadata"] = self._result.metadata

        elif isinstance(self._result, AnalysisResult):  # type: ignore[reportUnnecessaryIsInstance]
            result_dict["analyzed_at"] = self._result.analyzed_at.isoformat()
            if self._result.statistics:
                result_dict["statistics"] = self._result.statistics
            if self._result.indicators:
                result_dict["indicator_names"] = list(self._result.indicators.keys())

        return result_dict

    def _prepare_dataframe_for_sqlite(self) -> pd.DataFrame:
        """Prepare DataFrame for SQLite insertion."""
        df = self.data.copy()

        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            if "index" in df.columns:
                df = df.rename(columns={"index": "date"})
            if "date" in df.columns:
                df["date"] = df["date"].dt.strftime(self._date_format)

        df["symbol"] = self.symbol
        df["updated_at"] = datetime.now().isoformat()

        return df

    def _upsert_to_sqlite(
        self,
        db_path: Path,
        table_name: str,
        df: pd.DataFrame,
    ) -> int:
        """Perform UPSERT operation to SQLite."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            columns = list(df.columns)
            placeholders = ", ".join(["?" for _ in columns])
            column_names = ", ".join(columns)

            update_cols = [c for c in columns if c not in ("date", "symbol")]
            update_clause = ", ".join([f"{c} = excluded.{c}" for c in update_cols])

            create_sql = self._generate_create_table_sql(table_name, df)
            cursor.execute(create_sql)

            upsert_sql = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON CONFLICT(date, symbol) DO UPDATE SET {update_clause}
            """  # nosec B608

            rows = df.values.tolist()
            cursor.executemany(upsert_sql, rows)
            conn.commit()

            return len(rows)

    def _generate_create_table_sql(
        self,
        table_name: str,
        df: pd.DataFrame,
    ) -> str:
        """Generate CREATE TABLE SQL with appropriate types."""
        type_map = {
            "int64": "INTEGER",
            "float64": "REAL",
            "object": "TEXT",
            "datetime64[ns]": "TEXT",
            "bool": "INTEGER",
        }

        columns_sql = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sql_type = type_map.get(dtype, "TEXT")
            columns_sql.append(f"{col} {sql_type}")

        columns_def = ", ".join(columns_sql)

        return f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns_def},
                PRIMARY KEY (date, symbol)
            )
        """

    def _build_agent_metadata(self, source_module: str) -> AgentOutputMetadata:
        """Build metadata for agent output."""
        period = ""
        if not self.data.empty and isinstance(self.data.index, pd.DatetimeIndex):
            start = self.data.index.min().strftime(self._date_format)
            end = self.data.index.max().strftime(self._date_format)
            period = f"{start} to {end}"

        return AgentOutputMetadata(
            generated_at=datetime.now(),
            version=AGENT_OUTPUT_VERSION,
            source=source_module,
            symbols=[self.symbol],
            period=period,
        )

    def _prepare_agent_data(self) -> dict[str, Any]:
        """Prepare structured data for agent output."""
        df = self.data

        data: dict[str, Any] = {
            "symbol": self.symbol,
            "row_count": len(df),
            "columns": list(df.columns),
        }

        if not df.empty:
            latest = df.iloc[-1]
            data["latest"] = {
                col: (
                    float(latest[col])
                    if pd.notna(latest[col]) and col != "volume"
                    else (
                        int(latest[col])
                        if pd.notna(latest[col]) and col == "volume"
                        else None
                    )
                )
                for col in df.columns
            }

            if "close" in df.columns:
                closes = df["close"].dropna()
                if len(closes) >= 2:
                    data["price_change"] = {
                        "absolute": float(closes.iloc[-1] - closes.iloc[0]),
                        "percent": float(
                            (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
                        ),
                    }

                data["price_stats"] = {
                    "min": float(closes.min()),
                    "max": float(closes.max()),
                    "mean": float(closes.mean()),
                    "std": float(closes.std()) if len(closes) > 1 else 0.0,
                }

        if isinstance(self._result, MarketDataResult):
            data["source"] = self._result.source.value
            data["from_cache"] = self._result.from_cache

        elif isinstance(self._result, AnalysisResult):  # type: ignore[reportUnnecessaryIsInstance]
            if self._result.statistics:
                data["statistics"] = self._result.statistics
            if self._result.indicators:
                data["indicators"] = list(self._result.indicators.keys())

        return data

    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        df = self.data
        summary_parts = [f"Market data for {self.symbol}"]

        if not df.empty:
            summary_parts.append(f"containing {len(df)} data points")

            if isinstance(df.index, pd.DatetimeIndex):
                start = df.index.min().strftime(self._date_format)
                end = df.index.max().strftime(self._date_format)
                summary_parts.append(f"from {start} to {end}")

            if "close" in df.columns:
                closes = df["close"].dropna()
                if len(closes) >= 2:
                    change_pct = (
                        (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
                    )
                    direction = "up" if change_pct > 0 else "down"
                    summary_parts.append(
                        f"Price moved {direction} {abs(change_pct):.2f}% over the period"
                    )

        return ". ".join(summary_parts) + "."

    def _generate_recommendations(self) -> list[str]:
        """Generate basic recommendations based on data."""
        recommendations = []
        df = self.data

        if df.empty:
            recommendations.append("No data available for analysis.")
            return recommendations

        if "close" not in df.columns:
            return recommendations

        closes = df["close"].dropna()
        if len(closes) < 2:
            return recommendations

        change_pct = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100

        if change_pct > 10:
            recommendations.append(
                f"Strong upward trend detected ({change_pct:.1f}% gain)."
            )
        elif change_pct < -10:
            recommendations.append(
                f"Strong downward trend detected ({abs(change_pct):.1f}% loss)."
            )
        else:
            recommendations.append("Price has been relatively stable.")

        if len(closes) > 20:
            volatility = closes.pct_change().std() * 100
            if volatility > 3:
                recommendations.append(
                    f"High volatility detected (daily std: {volatility:.2f}%)."
                )

        return recommendations
