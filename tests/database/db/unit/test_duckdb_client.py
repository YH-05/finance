"""Unit tests for DuckDBClient."""

from pathlib import Path

import pandas as pd
from database.db.duckdb_client import DuckDBClient


class TestDuckDBClient:
    """Tests for DuckDBClient class."""

    def test_init_creates_parent_directory(self, temp_dir: Path) -> None:
        """Test that client creates parent directory if needed."""
        db_path = temp_dir / "subdir" / "test.duckdb"
        client = DuckDBClient(db_path)
        assert client.path.parent.exists()

    def test_query_df_returns_dataframe(self, duckdb_path: Path) -> None:
        """Test query_df returns pandas DataFrame."""
        client = DuckDBClient(duckdb_path)
        df = client.query_df("SELECT 1 as value, 'test' as name")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df["value"].iloc[0] == 1
        assert df["name"].iloc[0] == "test"

    def test_execute_creates_table(self, duckdb_path: Path) -> None:
        """Test execute method creates table."""
        client = DuckDBClient(duckdb_path)
        client.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        client.execute("INSERT INTO test VALUES (1, 'test')")

        df = client.query_df("SELECT * FROM test")
        assert len(df) == 1
        assert df["id"].iloc[0] == 1

    def test_write_parquet(self, temp_dir: Path, duckdb_path: Path) -> None:
        """Test write_parquet method."""
        client = DuckDBClient(duckdb_path)
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        parquet_path = temp_dir / "output" / "test.parquet"

        client.write_parquet(df, parquet_path)
        assert parquet_path.exists()

    def test_read_parquet(self, temp_dir: Path, duckdb_path: Path) -> None:
        """Test read_parquet method."""
        # First write a parquet file
        client = DuckDBClient(duckdb_path)
        df_original = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        parquet_path = temp_dir / "test.parquet"
        client.write_parquet(df_original, parquet_path)

        # Then read it back
        df_read = client.read_parquet(str(parquet_path))
        assert len(df_read) == 3
        assert list(df_read["id"]) == [1, 2, 3]

    def test_complex_query(self, duckdb_path: Path) -> None:
        """Test complex analytical query."""
        client = DuckDBClient(duckdb_path)
        client.execute("""
            CREATE TABLE prices (
                symbol VARCHAR,
                date DATE,
                close DOUBLE
            )
        """)
        client.execute("""
            INSERT INTO prices VALUES
            ('AAPL', '2024-01-01', 100.0),
            ('AAPL', '2024-01-02', 102.0),
            ('AAPL', '2024-01-03', 101.0),
            ('GOOGL', '2024-01-01', 200.0),
            ('GOOGL', '2024-01-02', 205.0)
        """)

        df = client.query_df("""
            SELECT
                symbol,
                AVG(close) as avg_price,
                COUNT(*) as days
            FROM prices
            GROUP BY symbol
            ORDER BY symbol
        """)

        assert len(df) == 2
        assert df["symbol"].tolist() == ["AAPL", "GOOGL"]
        assert df["days"].tolist() == [3, 2]
