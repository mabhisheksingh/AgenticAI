"""Agent service layer for chat interactions and AI agent orchestration.

This module provides high-level agent services that coordinate between
the API layer and the underlying LangGraph service for AI chat interactions.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
import logging
from uuid import UUID

from app.services.LangGraphService import LangGraphService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

langgraph_service = LangGraphService()


class AgentService:
    """Service class for AI agent interactions and chat orchestration.
    
    Provides high-level methods for coordinating chat interactions between
    users and AI agents, acting as a bridge between the API layer and the
    LangGraph service.
    
    Features:
    - Streaming chat token generation
    - Thread management integration
    - Logging and monitoring of agent interactions
    - Coordination with LangGraph service
    """
    def __init__(self):
        """Initialize the AgentService.
        
        Currently performs basic initialization. The actual LangGraph service
        is instantiated as a module-level singleton.
        """
        pass

    @classmethod
    async def stream_chat_tokens(
        cls,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
        """Stream AI agent response tokens for real-time chat experience.
        
        Provides a streaming interface for AI agent responses, enabling real-time
        chat experiences in the frontend. Coordinates with the LangGraph service
        to execute the AI agent and stream response tokens.
        
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
                
        Example:
            >>> async for token in AgentService.stream_chat_tokens(
            ...     user_id="user123",
            ...     thread_id=None,
            ...     message="Hello, how are you?",
            ...     thread_label="My First Chat"
            ... ):
            ...     print(token)  # SSE-formatted response tokens
            
        SSE Response Format:
            The method yields Server-Sent Events formatted strings:
            - data: {"threadId": "uuid", "userId": "user123"}
            - data: {"type": "token", "content": "Hello"}
            - data: {"type": "token", "content": "!"}
            - data: [DONE]
            
        Logging:
            - Logs the start of streaming operations
            - Delegates detailed logging to LangGraph service
            - Monitors agent execution progress
            
        Note:
            This method serves as a coordination layer between the API endpoints
            and the LangGraph service, providing consistent logging and error
            handling for chat interactions.
        """
        logger.info("Streaming chat tokens")
        logger.info("langgraph instance created and now Executing agent....")
        async for chunk in langgraph_service.execute_agent(
            message, thread_id, user_id, thread_label
        ):
            yield chunk
