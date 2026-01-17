"""Fixtures for factor regression tests.

This module provides expected value data and fixture loading utilities
for regression tests.
"""

from pathlib import Path

import pandas as pd

# Fixtures directory path
FIXTURES_DIR = Path(__file__).parent


def load_parquet_fixture(name: str) -> pd.DataFrame:
    """Load a parquet fixture file.

    Parameters
    ----------
    name : str
        Name of the fixture file (without .parquet extension)

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame
    """
    path = FIXTURES_DIR / f"{name}.parquet"
    return pd.read_parquet(path)


def save_parquet_fixture(df: pd.DataFrame, name: str) -> None:
    """Save a DataFrame as a parquet fixture file.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    name : str
        Name of the fixture file (without .parquet extension)
    """
    path = FIXTURES_DIR / f"{name}.parquet"
    df.to_parquet(path)


__all__ = ["FIXTURES_DIR", "load_parquet_fixture", "save_parquet_fixture"]
