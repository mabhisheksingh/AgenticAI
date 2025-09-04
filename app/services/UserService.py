from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
from app.services.LangGraphService import LangGraphService

logger = logging.getLogger(__name__)
langgraph_service = LangGraphService()


class UserService:
    """
    Service class for user and thread management operations.
    
    This service provides business logic for user management, thread operations,
    and serves as an interface between the API routes and data repositories.
    It handles thread listing, deletion, renaming, and retrieval operations.
    """
    
    def __init__(self):
        """Initialize the UserService."""
        pass

    @classmethod
    def get_all_user(cls) -> list[str]:
        """
        Retrieve all unique user IDs from the system.
        
        Returns:
            list[str]: List of all user IDs that have created threads
            
        Example:
            >>> users = UserService.get_all_user()
            >>> print(users)  # ['user-123', 'user-456', 'admin']
        """
        all_user = ThreadRepository.get_all_user()
        return all_user

    @classmethod
    def delete_user_by_id(cls, user_id: str) -> int:
        """
        Delete a user and all associated threads from the system.
        
        Args:
            user_id (str): The unique identifier of the user to delete
            
        Returns:
            int: Number of records affected by the deletion
            
        Example:
            >>> affected = UserService.delete_user_by_id('user-123')
            >>> print(f"Deleted {affected} records")
        """
        status = ThreadRepository.delete_user_by_id(user_id)
        return status

    @classmethod
    def list_threads_by_session(cls, user_id: str) -> list[dict[str, Any]]:
        """
        List all threads belonging to a specific user.
        
        Args:
            user_id (str): The unique identifier of the user
            
        Returns:
            list[dict[str, Any]]: List of thread objects containing:
                - thread_id: Unique thread identifier
                - thread_label: Human-readable thread name
                - created_at: Thread creation timestamp
                - session_id: Associated user session ID
                
        Example:
            >>> threads = UserService.list_threads_by_session('user-123')
            >>> for thread in threads:
            ...     print(f"{thread['thread_label']}: {thread['thread_id']}")
        """
        return ThreadRepository.get_session_by_id(user_id)

    @classmethod
    def delete_thread_by_session_and_id(cls, user_id: str, thread_id: str) -> int:
        """
        Delete a specific thread belonging to a user.
        
        Args:
            user_id (str): The unique identifier of the user
            thread_id (str): The unique identifier of the thread to delete
            
        Returns:
            int: Number of records affected (0 if thread not found, 1 if deleted)
            
        Example:
            >>> affected = UserService.delete_thread_by_session_and_id(
            ...     'user-123', 'thread-uuid-456'
            ... )
            >>> if affected > 0:
            ...     print("Thread deleted successfully")
        """
        return ThreadRepository.delete_by_session_and_thread(user_id, thread_id)

    @classmethod
    def rename_thread_label(cls, user_id: str, thread_id: str, label: str) -> dict[str, Any] | None:
        """
        Update the label/name of a specific thread.
        
        Args:
            user_id (str): The unique identifier of the user
            thread_id (str): The unique identifier of the thread
            label (str): The new label/name for the thread
            
        Returns:
            dict[str, Any] | None: Updated thread information or None if not found
            
        Example:
            >>> result = UserService.rename_thread_label(
            ...     'user-123', 'thread-uuid-456', 'My Important Chat'
            ... )
            >>> if result:
            ...     print(f"Thread renamed to: {result['thread_label']}")
        """
        return ThreadRepository.rename_thread_label(user_id, thread_id, label)

    @classmethod
    def get_thread_by_id(cls, user_id: str, thread_id: UUID) -> dict[str, Any]:
        """
        Retrieve detailed information about a specific thread including messages.
        
        This method combines database thread metadata with LangGraph conversation
        history to provide a complete thread view with all messages.
        
        Args:
            user_id (str): The unique identifier of the user
            thread_id (UUID): The unique identifier of the thread
            
        Returns:
            dict[str, Any]: Complete thread information containing:
                - thread_id: Thread UUID as string
                - user_id: User identifier
                - messages: List of conversation messages with role and content
                - created_at: Thread creation timestamp
                - thread_label: Human-readable thread name
                
        Raises:
            NotFoundError: If the thread doesn't exist or doesn't belong to the user
            
        Example:
            >>> from uuid import UUID
            >>> thread_data = UserService.get_thread_by_id(
            ...     'user-123', UUID('550e8400-e29b-41d4-a716-446655440000')
            ... )
            >>> print(f"Thread: {thread_data['thread_label']}")
            >>> for msg in thread_data['messages']:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        logger.info("Getting thread by id")
        db_response = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
        if not db_response:
            raise NotFoundError("Thread not found")
        response_data = langgraph_service.get_thread_by_id_async(thread_id, user_id)

        # Return thread details with messages
        messages = []
        if response_data and response_data.values and "messages" in response_data.values:
            messages = [
                {
                    "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                    "content": msg.content,
                }
                for msg in response_data.values["messages"]
                if hasattr(msg, "content") and msg.content
            ]

        return {
            "thread_id": str(thread_id),
            "user_id": user_id,
            "messages": messages,
            "created_at": db_response.get("created_at"),
            "thread_label": db_response.get("thread_label"),
        }
