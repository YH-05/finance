"""Database connection management for cross-package access."""

from pathlib import Path

from finance.types import DatabaseType

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def get_db_path(db_type: DatabaseType, name: str) -> Path:
    """Get database file path.

    Parameters
    ----------
    db_type : DatabaseType
        Type of database ('sqlite' or 'duckdb')
    name : str
        Name of the database (without extension)

    Returns
    -------
    Path
        Full path to the database file

    Examples
    --------
    >>> path = get_db_path("sqlite", "market")
    >>> path.name
    'market.db'
    >>> path = get_db_path("duckdb", "analytics")
    >>> path.name
    'analytics.duckdb'
    """
    if db_type == "sqlite":
        return DATA_DIR / "sqlite" / f"{name}.db"
    return DATA_DIR / "duckdb" / f"{name}.duckdb"


def ensure_data_dirs() -> None:
    """Ensure all data directories exist.

    Creates the complete data directory structure if it doesn't exist.
    """
    dirs = [
        DATA_DIR / "sqlite",
        DATA_DIR / "duckdb",
        DATA_DIR / "raw" / "yfinance" / "stocks",
        DATA_DIR / "raw" / "yfinance" / "forex",
        DATA_DIR / "raw" / "yfinance" / "indices",
        DATA_DIR / "raw" / "fred" / "indicators",
        DATA_DIR / "processed" / "daily",
        DATA_DIR / "processed" / "aggregated",
        DATA_DIR / "exports" / "csv",
        DATA_DIR / "exports" / "json",
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
