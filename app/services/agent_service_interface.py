"""Agent service interfaces.

This module defines interfaces for AI agent services following
Interface Segregation Principle (ISP).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from collections.abc import AsyncGenerator
from uuid import UUID


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
    """
    
    @abstractmethod
    def get_conversation_state(
        self, 
        thread_id: UUID, 
        user_id: str
    ) -> Any:  # StateSnapshot type from langgraph
        """Retrieve conversation state for a specific thread."""
        pass