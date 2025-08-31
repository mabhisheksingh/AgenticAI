from __future__ import annotations

from typing import Any
import uuid

from app.config.SqlLiteConfig import get_sql_lite_instance


class ThreadRepository:
    """Repository for session-thread mapping.

    Table: session_threads(id, thread_id, session_id, created_at)
    - id: primary key (UUID string)
    - thread_id: UUID string for conversation thread
    - session_id: user/session identifier (string)
    """

    @staticmethod
    def save(session_id: str, thread_id: str, id: str | None = None) -> dict[str, Any]:
        conn = get_sql_lite_instance()
        if id is None:
            id = str(uuid.uuid4())
        cur = conn.cursor()
        # Insert or ignore on existing unique(session_id, thread_id)
        cur.execute(
            """
            INSERT OR IGNORE INTO session_threads (id, session_id, thread_id)
            VALUES (?, ?, ?)
            """,
            (id, session_id, thread_id),
        )
        conn.commit()
        # Return the canonical stored row
        cur.execute(
            """
            SELECT id, session_id, thread_id, created_at
            FROM session_threads
            WHERE session_id = ? AND thread_id = ?
            LIMIT 1
            """,
            (session_id, thread_id),
        )
        row = cur.fetchone()
        return dict(row) if row else {"id": id, "session_id": session_id, "thread_id": thread_id}

    @staticmethod
    def get_thread_by_id(thread_id: str) -> dict[str, Any] | None:
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, created_at
            FROM session_threads
            WHERE thread_id = ?
            LIMIT 1
            """,
            (thread_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_session_by_id(session_id: str) -> list[dict[str, Any]]:
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, created_at
            FROM session_threads
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_session_and_thread(session_id: str, thread_id: str) -> dict[str, Any] | None:
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, created_at
            FROM session_threads
            WHERE session_id = ? AND thread_id = ?
            LIMIT 1
            """,
            (session_id, thread_id),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete_by_session_and_thread(session_id: str, thread_id: str) -> int:
        """Delete a mapping; returns number of rows deleted."""
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM session_threads WHERE session_id = ? AND thread_id = ?",
            (session_id, thread_id),
        )
        conn.commit()
        return cur.rowcount

