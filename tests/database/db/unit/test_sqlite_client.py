"""Unit tests for SQLiteClient."""

from pathlib import Path

import pytest
from database.db.sqlite_client import SQLiteClient


class TestSQLiteClient:
    """Tests for SQLiteClient class."""

    def test_init_creates_parent_directory(self, temp_dir: Path) -> None:
        """Test that client creates parent directory if needed."""
        db_path = temp_dir / "subdir" / "test.db"
        client = SQLiteClient(db_path)
        assert client.path.parent.exists()

    def test_connection_context_manager(self, sqlite_path: Path) -> None:
        """Test connection context manager works correctly."""
        client = SQLiteClient(sqlite_path)
        with client.connection() as conn:
            cursor = conn.execute("SELECT 1 as value")
            result = cursor.fetchone()
            assert result["value"] == 1

    def test_execute_returns_results(self, sqlite_path: Path) -> None:
        """Test execute method returns query results."""
        client = SQLiteClient(sqlite_path)
        with client.connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")

        results = client.execute("SELECT * FROM test")
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["name"] == "test"

    def test_execute_with_params(self, sqlite_path: Path) -> None:
        """Test execute method with parameters."""
        client = SQLiteClient(sqlite_path)
        with client.connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'one')")
            conn.execute("INSERT INTO test VALUES (2, 'two')")

        results = client.execute("SELECT * FROM test WHERE id = ?", (1,))
        assert len(results) == 1
        assert results[0]["name"] == "one"

    def test_execute_many(self, sqlite_path: Path) -> None:
        """Test execute_many method."""
        client = SQLiteClient(sqlite_path)
        with client.connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        params = [(1, "one"), (2, "two"), (3, "three")]
        count = client.execute_many("INSERT INTO test VALUES (?, ?)", params)
        assert count == 3

        results = client.execute("SELECT COUNT(*) as cnt FROM test")
        assert results[0]["cnt"] == 3

    def test_execute_script(self, sqlite_path: Path) -> None:
        """Test execute_script method."""
        client = SQLiteClient(sqlite_path)
        script = """
        CREATE TABLE test1 (id INTEGER);
        CREATE TABLE test2 (id INTEGER);
        INSERT INTO test1 VALUES (1);
        INSERT INTO test2 VALUES (2);
        """
        client.execute_script(script)

        results = client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [r["name"] for r in results]
        assert "test1" in table_names
        assert "test2" in table_names

    def test_transaction_rollback_on_error(self, sqlite_path: Path) -> None:
        """Test that transaction is rolled back on error."""
        client = SQLiteClient(sqlite_path)
        with client.connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER UNIQUE)")
            conn.execute("INSERT INTO test VALUES (1)")

        with pytest.raises(Exception), client.connection() as conn:  # noqa: B017
            conn.execute("INSERT INTO test VALUES (2)")
            conn.execute("INSERT INTO test VALUES (1)")  # Duplicate

        # Only the first insert should remain
        results = client.execute("SELECT COUNT(*) as cnt FROM test")
        assert results[0]["cnt"] == 1
