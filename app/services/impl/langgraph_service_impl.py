"""LangGraph service implementation using StateGraphObject for AI agent orchestration.

This module provides AI agent functionality using the StateGraphObject for
workflow orchestration, message handling, and conversation state management
with SQLite persistence.

Implements multiple interfaces following ISP and uses dependency injection
following DIP principles.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
import uuid
from typing import cast
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.types import StateSnapshot
from langchain_core.runnables import RunnableConfig

from app.core.enums import LLMProvider
from app.services import (
    AgentExecutionInterface,
    ConversationStateInterface,
)
from app.agents import LLMFactoryInterface
from app.agents.state_graph_object import StateGraphObject
from app.repositories import ThreadRepositoryInterface
from app.repositories import DatabaseConnectionProvider

# Setup logging
logger = logging.getLogger(__name__)





class LangGraphServiceImpl(AgentExecutionInterface, ConversationStateInterface):
    """Service implementation for AI agent orchestration using StateGraphObject.
    
    Implements AgentExecutionInterface and ConversationStateInterface following
    ISP (Interface Segregation Principle) and uses dependency injection following
    DIP (Dependency Inversion Principle).
    
    This service manages AI agent interactions using StateGraphObject for
    workflow orchestration, providing conversation state management, message
    handling, and streaming response capabilities with SQLite persistence.
    
    Features:
    - StateGraphObject-based workflow orchestration
    - SQLite-based conversation checkpointing
    - Streaming response generation
    - Thread and session management
    - Message history loading and persistence
    """
    
    def __init__(
        self,
        llm_provider: LLMFactoryInterface,
        thread_repository: ThreadRepositoryInterface,
        db_provider: DatabaseConnectionProvider,
    ):
        """Initialize the LangGraphService with StateGraphObject.
        
        Args:
            llm_provider: Provider for creating LLM instances
            thread_repository: Repository for thread management
            db_provider: Database connection provider
        """
        self._thread_repository = thread_repository
        
        # Initialize LLM and create StateGraphObject
        llm = llm_provider.create_model(LLMProvider.LLM_MEDIUM_MODEL)
        self.state_graph_obj = StateGraphObject(llm, db_provider)
        self.graph = self.state_graph_obj.prepare_state_graph()

    @staticmethod
    def _get_session_and_thread_config(thread_id: UUID | str, session_id: str) -> RunnableConfig:
        """Create LangGraph configuration for thread and session context.
        
        Args:
            thread_id (UUID | str): Thread identifier for conversation context
            session_id (str): Session identifier for user context
            
        Returns:
            RunnableConfig: LangGraph configuration with configurable parameters
        """
        config = {"configurable": {"thread_id": str(thread_id), "session_id": str(session_id)}}
        return cast(RunnableConfig, config)


    def get_conversation_state(self, thread_id: UUID, user_id: str) -> StateSnapshot:
        """Retrieve conversation state for a specific thread.
        
        Implements ConversationStateInterface contract for state retrieval.
        Loads the current state of a conversation thread including all
        messages and metadata from the LangGraph checkpointer.
        
        Args:
            thread_id (UUID): Thread identifier to retrieve state for
            user_id (str): User/session identifier for context
            
        Returns:
            StateSnapshot: Current state of the conversation thread
        """
        config = LangGraphServiceImpl._get_session_and_thread_config(thread_id, user_id)
        state = self.graph.get_state(config)
        return state

    def execute_agent(
        self,
        message: str,
        thread_id: UUID | None,
        user_id: str,
        thread_label: str,
    ) -> AsyncGenerator[str, None]:
        """Execute AI agent and stream response tokens.
        
        Implements AgentExecutionInterface contract for agent execution.
        Coordinates the complete agent execution pipeline including thread
        management, message processing, and response streaming.
        
        Args:
            message (str): User's input message
            thread_id (UUID, optional): Existing thread ID or None for new thread
            user_id (str): User/session identifier
            thread_label (str): Label for the thread (mandatory for new threads)
            
        Yields:
            str: Server-Sent Events (SSE) formatted response chunks
            
        Process Flow:
        1. Load or create conversation thread
        2. Add user message to conversation
        3. Stream AI response through LangGraph
        4. Format responses as SSE events
        5. Handle errors gracefully
        """
        return self._execute_agent_impl(message, thread_id, user_id, thread_label)
    
    async def _execute_agent_impl(
        self,
        message: str,
        thread_id: UUID | None,
        user_id: str,
        thread_label: str,
    ) -> AsyncGenerator[str, None]:
        """Execute AI agent using StateGraphObject and stream response tokens."""
        logger.info("StateGraphObject: Starting agent execution")
        
        # Load thread history and update with new message
        chat_messages, actual_thread_id = self.load_and_update_thread(thread_id, user_id, thread_label)
        thread_id = actual_thread_id
        
        # Add the new user message
        chat_messages.append(HumanMessage(content=message))

        # Initial metadata event
        yield f"data: {json.dumps({'threadId': str(thread_id), 'userId': user_id})}\n\n"

        # User message acknowledgment
        yield f"data: {json.dumps({'type': 'user','content': 'Got it 👍 you want ' + ' '.join(message)})}\n\n"

        try:
            if thread_id is None:
                raise ValueError("thread_id cannot be None at streaming time")
            
            config = self._get_session_and_thread_config(thread_id, user_id)
            logger.info("StateGraphObject: Starting streaming --> %s",chat_messages)
            # Stream through StateGraphObject
            for chunk in self.graph.stream(
                {"messages": chat_messages}, config, stream_mode="messages"
            ):
                # Handle streaming chunks
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message_chunk, metadata = chunk
                    if hasattr(message_chunk, "content") and getattr(message_chunk, "content", None):
                        content = str(message_chunk.content)
                        node_name = metadata.get("langgraph_node", "assistant") if isinstance(metadata, dict) else "assistant"
                        yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'node': node_name}})}\n\n"
                elif hasattr(chunk, "content") and getattr(chunk, "content", None):
                    content = str(getattr(chunk, "content", ""))
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

            logger.info(f"StateGraphObject streaming completed for thread {thread_id}")

        except Exception as e:
            logger.error(f"Error in StateGraphObject streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # End of stream marker
        yield "data: [DONE]\n\n"

    def load_and_update_thread(
        self, thread_id: UUID | None, user_id: str, thread_label: str
    ) -> tuple[list[BaseMessage], UUID]:
        """Load or create conversation thread with message history.
        
        Args:
            thread_id (UUID, optional): Existing thread ID. If None, creates new thread.
            user_id (str): User/session identifier
            thread_label (str): Label for the thread (required for new threads)
            
        Returns:
            tuple[list[BaseMessage], UUID]: Conversation messages and thread ID
        """
        chat_messages = []
        is_new_thread = thread_id is None
        if is_new_thread:
            thread_id = uuid.uuid4()
            # Always save thread_label since it's now mandatory
            self._thread_repository.save(
                session_id=user_id, thread_id=str(thread_id), thread_label=thread_label
            )
            chat_messages.append(
                SystemMessage(content="Hey! You are a helpful assistant expert in Crime and Law")
            )
        else:
            row = self._thread_repository.get_by_session_and_thread(user_id, str(thread_id))
            if not row:
                raise Exception("Thread not found")

            # Load existing conversation history from LangGraph checkpointer
            try:
                config = self._get_session_and_thread_config(thread_id, user_id)
                state = self.graph.get_state(config)

                if state and state.values and "messages" in state.values:
                    chat_messages = state.values["messages"]
                    logger.info(f"Loaded {len(chat_messages)} messages from thread history")
                else:
                    # If no history found, start with system message
                    chat_messages.append(
                        SystemMessage(
                            content="Hey! You are a helpful assistant expert in Crime and Law"
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to load conversation history: {e}")
                # Fallback to system message if loading fails
                chat_messages.append(
                    SystemMessage(
                        content="Hey! You are a helpful assistant expert in Crime and Law"
                    )
                )

        return chat_messages, thread_id