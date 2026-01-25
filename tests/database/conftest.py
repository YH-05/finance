"""Pytest fixtures for finance package tests."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sqlite_path(temp_dir: Path) -> Path:
    """Get path for temporary SQLite database."""
    return temp_dir / "test.db"


@pytest.fixture
def duckdb_path(temp_dir: Path) -> Path:
    """Get path for temporary DuckDB database."""
    return temp_dir / "test.duckdb"
