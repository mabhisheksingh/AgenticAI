"""SQLite database configuration and connection management.

This module provides a singleton pattern for SQLite database connections,
schema initialization, and migration management for the AgenticAI application.
It handles database setup, table creation, and ensures proper connection lifecycle.
"""
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
    """Add thread_label column to session_threads table if it doesn't exist.
    
    This migration function safely adds the thread_label column to support
    thread labeling functionality. It handles the case where the column
    already exists gracefully.
    
    Args:
        conn (sqlite3.Connection): Active SQLite database connection
        
    Raises:
        sqlite3.OperationalError: If the migration fails for reasons other
            than duplicate column (which is handled gracefully)
            
    Example:
        >>> conn = sqlite3.connect("test.db")
        >>> migrate_add_thread_label(conn)
        Added thread_label column to session_threads table
    """
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
    """Initialize and migrate database schema to latest version.
    
    Ensures all required tables, indexes, and columns exist in the database.
    This function is idempotent and safe to run multiple times.
    
    Features:
    - Enables WAL (Write-Ahead Logging) mode for better concurrency
    - Creates session_threads table with proper indexes
    - Runs all necessary migrations
    - Commits all changes atomically
    
    Args:
        conn (sqlite3.Connection): Active SQLite database connection
        
    Note:
        WAL mode is enabled to improve concurrent access, which is particularly
        beneficial when used with LangGraph's SQLite checkpointer.
    """
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
    """Get or create a singleton SQLite database connection.
    
    Returns a configured SQLite connection with proper schema initialization.
    Uses a module-level singleton pattern to ensure connection reuse and
    avoid connection overhead.
    
    Features:
    - Singleton pattern for connection reuse
    - Automatic directory creation for database file
    - Row factory set to sqlite3.Row for dict-like access
    - Automatic schema initialization and migration
    - Thread-safe connection (check_same_thread=False)
    
    Returns:
        sqlite3.Connection: Configured SQLite database connection with:
            - Row factory set to sqlite3.Row
            - All required tables and indexes created
            - All migrations applied
            
    Environment Variables:
        SQLITE_DB_PATH: Custom path for SQLite database file.
            Defaults to app/db/chat.db relative to this module.
            
    Example:
        >>> conn = get_sql_lite_instance()
        >>> cursor = conn.execute("SELECT * FROM session_threads")
        >>> rows = cursor.fetchall()
        >>> print(rows[0]["thread_id"])  # Dict-like access thanks to Row factory
        
    Note:
        The connection is configured with check_same_thread=False to allow
        usage across multiple threads, which is necessary for FastAPI's
        async execution model.
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
    """Close the singleton SQLite connection gracefully.
    
    Safely closes the database connection and resets the singleton state.
    This function should be called during application shutdown to ensure
    proper resource cleanup.
    
    Features:
    - Graceful handling of already-closed connections
    - Proper singleton state reset
    - Exception-safe cleanup (connection always reset even if close fails)
    
    Example:
        >>> # During application startup
        >>> conn = get_sql_lite_instance()
        >>> # ... use connection ...
        >>> # During application shutdown
        >>> close_sql_lite_instance()
        
    Note:
        This function is typically called from FastAPI's shutdown event handler
        or application cleanup routines.
    """
    conn = _STATE.get("conn")
    try:
        if conn is not None:
            conn.close()
    finally:
        _STATE["conn"] = None
