"""Thread repository interfaces.

This module defines interfaces for thread data access operations following
Interface Segregation Principle (ISP).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ThreadRepositoryInterface(ABC):
    """Abstract interface for thread repository operations.
    
    Segregated interface focusing only on thread-related persistence
    operations, following ISP by not forcing clients to depend on
    methods they don't use.
    """
    
    @abstractmethod
    def save(
        self, 
        session_id: str, 
        thread_id: str, 
        thread_label: str | None = None, 
        id: str | None = None
    ) -> dict[str, Any]:
        """Save or update a session-thread mapping."""
        pass
    
    @abstractmethod
    def get_by_session_and_thread(
        self, 
        session_id: str, 
        thread_id: str
    ) -> dict[str, Any] | None:
        """Get a specific thread record by session and thread ID."""
        pass
    
    @abstractmethod
    def get_session_by_id(self, session_id: str) -> list[dict[str, Any]]:
        """Get all threads for a specific session/user."""
        pass
    
    @abstractmethod
    def delete_by_session_and_thread(self, session_id: str, thread_id: str) -> int:
        """Delete a specific thread mapping."""
        pass
    
    @abstractmethod
    def rename_thread_label(self, session_id: str, thread_id: str, label: str) -> int:
        """Update the label for a specific thread."""
        pass


class UserRepositoryInterface(ABC):
    """Abstract interface for user repository operations.
    
    Segregated interface for user-specific operations, separate from
    thread operations to follow ISP.
    """
    
    @abstractmethod
    def get_all_users(self) -> list[str]:
        """Get all unique user/session IDs."""
        pass
    
    @abstractmethod
    def delete_user_by_id(self, user_id: str) -> int:
        """Delete all data for a specific user."""
        pass


class ThreadQueryInterface(ABC):
    """Interface for thread query operations.
    
    Separated from modification operations to follow ISP,
    allowing read-only clients to depend only on query methods.
    """
    
    @abstractmethod
    def get_thread_by_id(self, thread_id: str) -> dict[str, Any] | None:
        """Retrieve a thread record by its thread ID."""
        pass