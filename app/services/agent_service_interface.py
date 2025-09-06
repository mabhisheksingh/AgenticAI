"""Agent service interfaces.

This module defines interfaces for AI agent services following
Interface Segregation Principle (ISP). These interfaces support
StateGraphObject-based implementations for workflow orchestration.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from uuid import UUID

from langgraph.types import StateSnapshot


class AgentServiceInterface(ABC):
    """High-level interface for agent service operations.
    
    Provides the main contract for agent interactions without
    exposing internal implementation details.
    """
    
    @abstractmethod
    def stream_chat_tokens(
        self,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,
    ) -> AsyncGenerator[str, None]:
        """Stream AI agent response tokens for real-time chat."""
        pass


class AgentExecutionInterface(ABC):
    """Interface for AI agent execution operations.
    
    Segregated interface focusing only on agent execution,
    separate from configuration and setup concerns.
    """
    
    @abstractmethod
    def execute_agent(
        self,
        message: str,
        thread_id: UUID | None,
        user_id: str,
        thread_label: str,
    ) -> AsyncGenerator[str, None]:
        """Execute AI agent and stream response tokens."""
        pass


class ConversationStateInterface(ABC):
    """Interface for conversation state management.
    
    Separated from execution to follow ISP, allowing clients
    that only need state access to depend on this interface.
    Supports StateGraphObject-based conversation persistence.
    """
    
    @abstractmethod
    def get_conversation_state(
        self, 
        thread_id: UUID, 
        user_id: str
    ) -> StateSnapshot:
        """Retrieve conversation state for a specific thread.
        
        Args:
            thread_id: Thread identifier to retrieve state for
            user_id: User/session identifier for context
            
        Returns:
            StateSnapshot: Current state of the conversation thread
        """
        pass