"""Repository layer for thread and session management.

This module provides data access methods for managing conversation threads
and their association with user sessions. It handles thread creation, retrieval,
labeling, and deletion operations using SQLite as the persistence layer.
"""
from __future__ import annotations

from typing import Any
import uuid

from app.config.SqlLiteConfig import get_sql_lite_instance


class ThreadRepository:
    """Repository for session-thread mapping and thread management operations.
    
    Provides static methods for CRUD operations on the session_threads table,
    which maintains the relationship between user sessions and conversation threads.
    
    Database Schema:
        session_threads table:
        - id: Primary key (UUID string)
        - thread_id: UUID string for conversation thread (unique per session)
        - thread_label: Optional display label for the thread
        - session_id: User/session identifier string
        - created_at: Timestamp when the thread was created
        
    Unique Constraint:
        (session_id, thread_id) - prevents duplicate threads per session
        
    Indexes:
        - idx_session_threads_session: On session_id for fast user queries
        - idx_session_threads_thread: On thread_id for fast thread lookups
    """

    @staticmethod
    def save(
        session_id: str, thread_id: str, thread_label: str | None = None, id: str | None = None
    ) -> dict[str, Any]:
        """Save or update a session-thread mapping.
        
        Creates a new session-thread mapping or retrieves existing one if the
        (session_id, thread_id) combination already exists. Uses INSERT OR IGNORE
        to handle duplicate entries gracefully.
        
        Args:
            session_id (str): User/session identifier
            thread_id (str): Conversation thread UUID
            thread_label (str, optional): Display label for the thread
            id (str, optional): Primary key UUID. Generated if not provided.
            
        Returns:
            dict[str, Any]: Thread record containing:
                - id: Primary key UUID
                - session_id: User/session identifier
                - thread_id: Thread UUID
                - thread_label: Thread display label
                - created_at: Creation timestamp (if retrieved from DB)
                
        Example:
            >>> ThreadRepository.save("user123", "thread-uuid", "My Chat")
            {
                "id": "record-uuid",
                "session_id": "user123",
                "thread_id": "thread-uuid",
                "thread_label": "My Chat",
                "created_at": "2024-01-01 12:00:00"
            }
        """
        conn = get_sql_lite_instance()
        if id is None:
            id = str(uuid.uuid4())
        cur = conn.cursor()
        # Insert or ignore on existing unique(session_id, thread_id)
        cur.execute(
            """
            INSERT OR IGNORE INTO session_threads (id, session_id, thread_id, thread_label)
            VALUES (?, ?, ?, ?)
            """,
            (id, session_id, thread_id, thread_label),
        )
        conn.commit()
        # Return the canonical stored row
        cur.execute(
            """
            SELECT id, session_id, thread_id, thread_label, created_at
            FROM session_threads
            WHERE session_id = ? AND thread_id = ?
            LIMIT 1
            """,
            (session_id, thread_id),
        )
        row = cur.fetchone()
        return (
            dict(row)
            if row
            else {
                "id": id,
                "session_id": session_id,
                "thread_id": thread_id,
                "thread_label": thread_label,
            }
        )

    @staticmethod
    def get_all_user() -> list[str]:
        """Get all unique user/session IDs that have created threads.
        
        Returns a sorted list of all session IDs that have at least one
        conversation thread. Useful for user management and admin interfaces.
        
        Returns:
            list[str]: Sorted list of unique session IDs
            
        Example:
            >>> ThreadRepository.get_all_user()
            ["admin", "user123", "user456"]
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT session_id
            FROM session_threads
            ORDER BY session_id
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def delete_user_by_id(user_id: str) -> int:
        """Delete all threads for a specific user/session.
        
        Removes all thread records associated with the given session ID.
        This effectively deletes all conversation history for a user.
        
        Args:
            user_id (str): Session ID of the user to delete
            
        Returns:
            int: Number of thread records deleted
            
        Example:
            >>> ThreadRepository.delete_user_by_id("user123")
            5  # Deleted 5 threads for user123
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM session_threads WHERE session_id = ?",
            (user_id,),
        )
        conn.commit()
        return cur.rowcount

    @staticmethod
    def get_thread_by_id(thread_id: str) -> dict[str, Any] | None:
        """Retrieve a thread record by its thread ID.
        
        Looks up a specific thread by its UUID, regardless of which
        session it belongs to.
        
        Args:
            thread_id (str): Thread UUID to look up
            
        Returns:
            dict[str, Any] | None: Thread record if found, None otherwise.
                Contains id, session_id, thread_id, thread_label, created_at
                
        Example:
            >>> ThreadRepository.get_thread_by_id("thread-uuid")
            {
                "id": "record-uuid",
                "session_id": "user123",
                "thread_id": "thread-uuid",
                "thread_label": "My Chat",
                "created_at": "2024-01-01 12:00:00"
            }
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, thread_label, created_at
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
        """Get all threads for a specific session/user.
        
        Retrieves all conversation threads associated with a given session ID,
        ordered by creation time (most recent first).
        
        Args:
            session_id (str): Session ID to get threads for
            
        Returns:
            list[dict[str, Any]]: List of thread records, ordered by created_at DESC.
                Each record contains id, session_id, thread_id, thread_label, created_at
                
        Example:
            >>> ThreadRepository.get_session_by_id("user123")
            [
                {
                    "id": "record-1",
                    "session_id": "user123",
                    "thread_id": "thread-2",
                    "thread_label": "Recent Chat",
                    "created_at": "2024-01-02 10:00:00"
                },
                {
                    "id": "record-2",
                    "session_id": "user123",
                    "thread_id": "thread-1",
                    "thread_label": "Older Chat",
                    "created_at": "2024-01-01 09:00:00"
                }
            ]
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, thread_label, created_at
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
        """Get a specific thread record by session and thread ID.
        
        Retrieves the thread record that matches both the session ID and thread ID.
        This is the most specific lookup method.
        
        Args:
            session_id (str): Session ID that owns the thread
            thread_id (str): Thread UUID to look up
            
        Returns:
            dict[str, Any] | None: Thread record if found, None otherwise.
                Contains id, session_id, thread_id, thread_label, created_at
                
        Example:
            >>> ThreadRepository.get_by_session_and_thread("user123", "thread-uuid")
            {
                "id": "record-uuid",
                "session_id": "user123",
                "thread_id": "thread-uuid",
                "thread_label": "My Chat",
                "created_at": "2024-01-01 12:00:00"
            }
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, thread_id, thread_label, created_at
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
        """Delete a specific thread mapping.
        
        Removes the thread record that matches both session ID and thread ID.
        This deletes the mapping but doesn't affect the actual conversation
        data stored by LangGraph.
        
        Args:
            session_id (str): Session ID that owns the thread
            thread_id (str): Thread UUID to delete
            
        Returns:
            int: Number of rows deleted (0 or 1)
            
        Example:
            >>> ThreadRepository.delete_by_session_and_thread("user123", "thread-uuid")
            1  # Successfully deleted
            
            >>> ThreadRepository.delete_by_session_and_thread("user123", "nonexistent")
            0  # Nothing to delete
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM session_threads WHERE session_id = ? AND thread_id = ?",
            (session_id, thread_id),
        )
        conn.commit()
        return cur.rowcount

    @staticmethod
    def rename_thread_label(session_id: str, thread_id: str, label: str) -> int:
        """Update the label for a specific thread.
        
        Changes the display label for a thread identified by session ID and thread ID.
        The label is used in the UI to help users identify different conversations.
        
        Args:
            session_id (str): Session ID that owns the thread
            thread_id (str): Thread UUID to update
            label (str): New label for the thread
            
        Returns:
            int: Number of rows updated (0 or 1)
            
        Example:
            >>> ThreadRepository.rename_thread_label("user123", "thread-uuid", "New Label")
            1  # Successfully updated
            
            >>> ThreadRepository.rename_thread_label("user123", "nonexistent", "Label")
            0  # Nothing to update
            
        Note:
            This method updates the thread_label field only. Other thread
            properties remain unchanged.
        """
        conn = get_sql_lite_instance()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE session_threads
            SET thread_label = ?
            WHERE session_id = ? AND thread_id = ?
            """,
            (label, session_id, thread_id),
        )
        conn.commit()
        return cur.rowcount
