import sqlite3
from collections.abc import Generator
from pathlib import Path

from stamped.core.config import settings

_MIGRATIONS_DIR = Path(__file__).parent.parent.parent.parent / "migrations"


def _get_db_path() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "stamped.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _applied_versions(conn: sqlite3.Connection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def init_db() -> None:
    conn = get_connection()
    try:
        applied = _applied_versions(conn)
        scripts = sorted(_MIGRATIONS_DIR.glob("*.sql"))
        for script in scripts:
            version = script.stem
            if version not in applied:
                conn.executescript(script.read_text())
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
    finally:
        conn.close()
