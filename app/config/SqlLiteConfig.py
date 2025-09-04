import os
from pathlib import Path
import sqlite3

# Resolve an absolute path for the SQLite DB
# Prefer env var SQLITE_DB_PATH; otherwise resolve relative to this file: app/db/chat.db
_DEFAULT_DB_PATH = (Path(__file__).resolve().parent.parent / "db" / "chat.db").resolve()
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(_DEFAULT_DB_PATH))).resolve()

_CREATE_SESSION_THREAD_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS session_threads (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    thread_label TEXT,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, thread_id)
);
CREATE INDEX IF NOT EXISTS idx_session_threads_session ON session_threads(session_id);
CREATE INDEX IF NOT EXISTS idx_session_threads_thread ON session_threads(thread_id);
"""


def migrate_add_thread_label(conn: sqlite3.Connection) -> None:
    """Add thread_label column to session_threads table if it doesn't exist."""
    try:
        conn.execute("ALTER TABLE session_threads ADD COLUMN thread_label TEXT")
        conn.commit()
        print("Added thread_label column to session_threads table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("thread_label column already exists")
        else:
            raise


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Initialize database schema if needed."""
    # Enable WAL for better concurrency with LangGraph checkpointer
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.executescript(_CREATE_SESSION_THREAD_TABLE_SQL)
    migrate_add_thread_label(conn)  # Run migration
    conn.commit()


# Module-level singleton connection (avoid 'global' by using a state dict)
_STATE: dict[str, sqlite3.Connection | None] = {"conn": None}


def get_sql_lite_instance() -> sqlite3.Connection:
    """Return a SQLite connection and ensure required tables exist.

    Note: row_factory is set to sqlite3.Row for dict-like access.
    """
    conn = _STATE["conn"]
    if conn is not None:
        return conn
    # Ensure parent directory exists (fixes 'unable to open database file' for relative paths)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    _STATE["conn"] = conn
    return conn


def close_sql_lite_instance() -> None:
    """Close the singleton SQLite connection if open."""
    conn = _STATE.get("conn")
    try:
        if conn is not None:
            conn.close()
    finally:
        _STATE["conn"] = None
