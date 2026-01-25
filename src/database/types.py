"""Common type definitions for the finance package."""

from collections.abc import Mapping
from typing import Literal, TypedDict

# Database types
type DatabaseType = Literal["sqlite", "duckdb"]
type DataSource = Literal["yfinance", "fred"]
type AssetCategory = Literal["stocks", "forex", "indices", "indicators"]

# File format types
type FileFormat = Literal["parquet", "csv", "json"]


class DatabaseConfig(TypedDict):
    """Database configuration."""

    db_type: DatabaseType
    name: str
    path: str


class FetchResult(TypedDict):
    """Result of a data fetch operation."""

    source: DataSource
    symbol: str
    start_date: str
    end_date: str
    row_count: int
    success: bool
    error: str | None


class MigrationInfo(TypedDict):
    """Migration file information."""

    filename: str
    applied_at: str | None


# JSON types (shared with market_analysis)
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# Log types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
