"""Database module for cross-package data access."""

from database.db.connection import DATA_DIR, PROJECT_ROOT, get_db_path
from database.db.duckdb_client import DuckDBClient
from database.db.sqlite_client import SQLiteClient

__all__ = [
    "DATA_DIR",
    "PROJECT_ROOT",
    "DuckDBClient",
    "SQLiteClient",
    "get_db_path",
]
