"""Database module for cross-package data access."""

from finance.db.connection import DATA_DIR, PROJECT_ROOT, get_db_path
from finance.db.duckdb_client import DuckDBClient
from finance.db.sqlite_client import SQLiteClient

__all__ = [
    "DATA_DIR",
    "PROJECT_ROOT",
    "DuckDBClient",
    "SQLiteClient",
    "get_db_path",
]
