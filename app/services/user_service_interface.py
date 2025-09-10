"""User service interfaces.

This module defines interfaces for user management services following
Interface Segregation Principle (ISP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class UserServiceInterface(ABC):
    """High-level interface for user service operations.

    Provides the main contract for user and thread management operations
    without exposing internal implementation details.
    """

    @abstractmethod
    def get_all_users(self) -> list[str]:
        """Get all users."""
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> int:
        """Delete a user and all associated data."""
        pass

    @abstractmethod
    def list_threads_by_session(self, user_id: str) -> list[dict[str, Any]]:
        """List all threads for a specific user."""
        pass

    @abstractmethod
    def get_thread_by_id(self, user_id: str, thread_id: UUID) -> dict[str, Any]:
        """Get detailed thread information including messages."""
        pass

    @abstractmethod
    def delete_thread_by_session_and_id(self, user_id: str, thread_id: str) -> int:
        """Delete a specific thread."""
        pass

    @abstractmethod
    def rename_thread_label(self, user_id: str, thread_id: str, label: str) -> int:
        """Update thread label."""
        pass
