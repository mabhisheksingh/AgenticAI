"""Agent service implementation for chat interactions and AI agent orchestration.

This module provides high-level agent services that coordinate between
the API layer and the underlying LangGraph service for AI chat interactions.

Implements AgentServiceInterface following ISP and uses dependency injection
following DIP principles.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
import logging
from uuid import UUID

from app.services import AgentServiceInterface, AgentExecutionInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AgentServiceImpl(AgentServiceInterface):
    """Service implementation for AI agent interactions and chat orchestration.
    
    Implements AgentServiceInterface following ISP (Interface Segregation Principle)
    and uses dependency injection following DIP (Dependency Inversion Principle).
    
    Provides high-level methods for coordinating chat interactions between
    users and AI agents, acting as a bridge between the API layer and the
    agent execution service.
    
    Features:
    - Streaming chat token generation
    - Thread management integration
    - Logging and monitoring of agent interactions
    - Coordination with agent execution service
    """
    
    def __init__(self, agent_executor: AgentExecutionInterface):
        """Initialize the AgentService with dependency injection.
        
        Args:
            agent_executor: Service responsible for executing AI agents
        """
        self._agent_executor = agent_executor

    def stream_chat_tokens(
        self,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
        """Stream AI agent response tokens for real-time chat experience.
        
        Implements the AgentServiceInterface contract for streaming chat responses.
        Provides a streaming interface for AI agent responses, enabling real-time
        chat experiences in the frontend.
        
        Args:
            user_id (str): Unique identifier for the user/session
            thread_id (UUID, optional): Existing thread ID to continue a conversation.
                If None, a new thread will be created.
            message (str): The user's chat message to send to the AI agent
            thread_label (str): Label for the thread (mandatory for new threads)
            
        Yields:
            str: Server-Sent Events (SSE) formatted strings containing:
                - Metadata about the thread and user
                - Individual response tokens as they're generated
                - End-of-stream marker
        """
        return self._stream_chat_tokens_impl(user_id, thread_id, message, thread_label)
    
    async def _stream_chat_tokens_impl(
        self,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,
    ) -> AsyncGenerator[str, None]:
        logger.info("Streaming chat tokens")
        logger.info("Agent executor service executing agent....")
        
        # Get the async generator by calling execute_agent
        agent_generator = self._agent_executor.execute_agent(
            message, thread_id, user_id, thread_label
        )
        
        # Iterate through the async generator
        async for chunk in agent_generator:
            yield chunk