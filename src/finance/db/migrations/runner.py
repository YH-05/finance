"""Database migration runner."""

import sqlite3
from pathlib import Path

from finance.types import MigrationInfo
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "versions"


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create schema_migrations table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get set of applied migration filenames."""
    _ensure_migrations_table(conn)
    cursor = conn.execute("SELECT filename FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def get_migration_status(db_path: Path) -> list[MigrationInfo]:
    """Get status of all migrations.

    Parameters
    ----------
    db_path : Path
        Path to SQLite database

    Returns
    -------
    list[MigrationInfo]
        List of migration info with applied status
    """
    with sqlite3.connect(db_path) as conn:
        _ensure_migrations_table(conn)
        cursor = conn.execute("SELECT filename, applied_at FROM schema_migrations")
        applied = {row[0]: row[1] for row in cursor.fetchall()}

    result: list[MigrationInfo] = []
    if MIGRATIONS_DIR.exists():
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            result.append(
                {
                    "filename": migration_file.name,
                    "applied_at": applied.get(migration_file.name),
                }
            )
    return result


def apply_migrations(db_path: Path) -> int:
    """Apply pending migrations to database.

    Parameters
    ----------
    db_path : Path
        Path to SQLite database

    Returns
    -------
    int
        Number of migrations applied

    Examples
    --------
    >>> from finance.db import get_db_path
    >>> from finance.db.migrations import apply_migrations
    >>> count = apply_migrations(get_db_path("sqlite", "market"))
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Starting migration", db_path=str(db_path))

    applied_count = 0

    with sqlite3.connect(db_path) as conn:
        applied = _get_applied_migrations(conn)
        logger.debug("Applied migrations", count=len(applied))

        if not MIGRATIONS_DIR.exists():
            logger.warning("Migrations directory not found", path=str(MIGRATIONS_DIR))
            return 0

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        pending = [f for f in migration_files if f.name not in applied]

        logger.info(
            "Migration status",
            applied=len(applied),
            pending=len(pending),
        )

        for migration_file in pending:
            logger.info("Applying migration", filename=migration_file.name)
            try:
                sql = migration_file.read_text()
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (?)",
                    (migration_file.name,),
                )
                conn.commit()
                applied_count += 1
                logger.info("Migration applied", filename=migration_file.name)
            except sqlite3.Error as e:
                logger.error(
                    "Migration failed",
                    filename=migration_file.name,
                    error=str(e),
                )
                raise

    logger.info("Migration completed", applied_count=applied_count)
    return applied_count
