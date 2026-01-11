"""Unit tests for database migrations."""

import sqlite3
from pathlib import Path

from finance.db.migrations.runner import apply_migrations, get_migration_status


class TestMigrations:
    """Tests for migration functionality."""

    def test_apply_migrations_creates_schema(self, sqlite_path: Path) -> None:
        """Test that apply_migrations creates the initial schema."""
        count = apply_migrations(sqlite_path)
        assert count >= 1  # At least initial schema

        # Verify tables exist
        with sqlite3.connect(sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row["name"] for row in cursor.fetchall()]

        assert "assets" in tables
        assert "prices_daily" in tables
        assert "indicators" in tables
        assert "fetch_history" in tables
        assert "schema_migrations" in tables

    def test_apply_migrations_idempotent(self, sqlite_path: Path) -> None:
        """Test that running migrations twice doesn't cause errors."""
        count1 = apply_migrations(sqlite_path)
        count2 = apply_migrations(sqlite_path)

        assert count1 >= 1
        assert count2 == 0  # No new migrations on second run

    def test_get_migration_status(self, sqlite_path: Path) -> None:
        """Test get_migration_status returns correct info."""
        apply_migrations(sqlite_path)
        status = get_migration_status(sqlite_path)

        assert len(status) >= 1
        for migration in status:
            assert "filename" in migration
            assert "applied_at" in migration
            assert migration["applied_at"] is not None  # All should be applied
