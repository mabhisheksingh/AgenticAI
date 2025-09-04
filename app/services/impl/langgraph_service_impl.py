"""LangGraph service implementation for AI agent orchestration and conversation management.

This module provides the core AI agent functionality using LangGraph for
workflow orchestration, message handling, and conversation state management
with SQLite persistence.

Implements multiple interfaces following ISP and uses dependency injection
following DIP principles.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
from typing import Any, cast
import uuid
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import StateSnapshot
from langchain_core.runnables import RunnableConfig

from app.services import (
    AgentExecutionInterface,
    ConversationStateInterface,
)
from app.agents import LLMProviderInterface
from app.repositories import ThreadRepositoryInterface
from app.repositories import DatabaseConnectionProvider

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def serialize(obj: Any) -> dict[str, Any] | str:
    """Serialize objects for logging and debugging purposes.
    
    Converts LangChain message objects and other types to serializable formats.
    
    Args:
        obj (Any): Object to serialize
        
    Returns:
        dict[str, Any] | str: Serialized representation of the object
    """
    if isinstance(obj, BaseMessage):
        return obj.dict()
    return str(obj)


class LangGraphServiceImpl(AgentExecutionInterface, ConversationStateInterface):
    """Service implementation for AI agent orchestration using LangGraph workflows.
    
    Implements AgentExecutionInterface and ConversationStateInterface following
    ISP (Interface Segregation Principle) and uses dependency injection following
    DIP (Dependency Inversion Principle).
    
    This service manages AI agent interactions using LangGraph's workflow system,
    providing conversation state management, message handling, and streaming
    response capabilities with SQLite persistence.
    
    Features:
    - LangGraph workflow orchestration
    - SQLite-based conversation checkpointing
    - Streaming response generation
    - Thread and session management
    - Message history loading and persistence
    - AI agent state management
    
    Architecture:
    - Uses LangGraph StateGraph for workflow definition
    - SqliteSaver for conversation checkpointing
    - LLMProviderInterface for language model instantiation
    - ThreadRepositoryInterface for thread metadata management
    
    The service builds a simple workflow: START → chat_model → END
    where the chat_model node invokes the LLM with conversation history.
    """
    
    def __init__(
        self,
        llm_provider: LLMProviderInterface,
        thread_repository: ThreadRepositoryInterface,
        db_provider: DatabaseConnectionProvider,
    ):
        """Initialize the LangGraphService with dependency injection.
        
        Sets up the complete LangGraph workflow including:
        - LLM instance from provider
        - State graph compilation
        - SQLite checkpointer configuration
        - Graph compilation with checkpointing enabled
        
        Args:
            llm_provider: Provider for creating LLM instances
            thread_repository: Repository for thread management
            db_provider: Database connection provider
        """
        self.thread_id = None
        self._llm_provider = llm_provider
        self._thread_repository = thread_repository
        self._db_provider = db_provider
        
        # Initialize LLM and graph
        self.llm = self._llm_provider.create_model()
        # Compile hybrid graph with sync checkpointer
        state_graph = self.prepare_state_graph()
        checkpointer = self._get_sql_lite_memory()
        self.graph = state_graph.compile(checkpointer=checkpointer)

    @staticmethod
    def _get_session_and_thread_config(thread_id: UUID | str, session_id: str) -> RunnableConfig:
        """Create LangGraph configuration for thread and session context.
        
        Builds the configuration object required by LangGraph for conversation
        context, including thread ID and session ID for proper state management.
        
        Args:
            thread_id (UUID | str): Thread identifier for conversation context
            session_id (str): Session identifier for user context
            
        Returns:
            RunnableConfig: LangGraph configuration with configurable parameters
            
        Example:
            >>> config = LangGraphService._get_session_and_thread_config(
            ...     "thread-123", "user-456"
            ... )
            >>> print(config)
            {"configurable": {"thread_id": "thread-123", "session_id": "user-456"}}
        """
        config = {"configurable": {"thread_id": str(thread_id), "session_id": str(session_id)}}
        logger.info("Config: %s", config)
        return cast(RunnableConfig, config)

    def _get_sql_lite_memory(self) -> SqliteSaver:
        """Create and configure SQLite-based conversation checkpointer.
        
        Sets up the LangGraph checkpointer using the application's SQLite
        database instance for persistent conversation state management.
        
        Returns:
            SqliteSaver: Configured SQLite checkpointer for LangGraph
            
        Note:
            Uses the same SQLite connection as the rest of the application
            for consistent data storage and transaction management.
        """
        sql_lite_instance = self._db_provider.get_connection()
        memory = SqliteSaver(sql_lite_instance)
        return memory

    # Node for sync/hybrid approach
    def call_llm(self, state: MessagesState) -> dict[str, list[BaseMessage]]:
        """LangGraph node function for invoking the language model.
        
        This is the core node in the LangGraph workflow that processes
        the conversation messages and generates AI responses.
        
        Args:
            state (MessagesState): Current state containing conversation messages
            
        Returns:
            dict[str, list[BaseMessage]]: Updated state with AI response message
            
        Note:
            This function is designed to be used as a LangGraph node and follows
            the LangGraph node function pattern of receiving state and returning
            state updates.
        """
        # Ensure we append the generated AIMessage to the messages list
        return {"messages": [self.llm.invoke(state["messages"])]}

    def prepare_state_graph(self) -> StateGraph:
        """Build and configure the LangGraph state graph workflow.
        
        Creates a simple linear workflow for chat interactions:
        START → chat_model → END
        
        The workflow uses MessagesState to maintain conversation context
        and provides a single node for LLM interaction.
        
        Returns:
            StateGraph: Configured LangGraph workflow ready for compilation
            
        Workflow Structure:
        - MessagesState: Maintains list of conversation messages
        - chat_model node: Invokes LLM with current message history
        - Linear flow: START → chat_model → END
        """
        builder = StateGraph(MessagesState)
        builder.add_node("chat_model", self.call_llm)
        builder.add_edge(START, "chat_model")
        builder.add_edge("chat_model", END)
        return builder

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
        logger.info("Pure LangGraph approach: Starting agent execution")
        
        # Load thread history and update with new message
        chat_messages, actual_thread_id = self.load_and_update_thread(thread_id, user_id, thread_label)
        thread_id = actual_thread_id  # Use the actual thread_id (might be newly created)
        
        # Add the new user message
        chat_messages.append(HumanMessage(content=message))

        # Initial metadata event
        yield f"data: {json.dumps({'threadId': str(thread_id), 'userId': user_id})}\n\n"

        try:
            # Ensure thread_id is not None at this point
            if thread_id is None:
                raise ValueError("thread_id cannot be None at streaming time")
            
            config = LangGraphServiceImpl._get_session_and_thread_config(thread_id, user_id)

            # Stream through LangGraph's native streaming system with messages mode
            for chunk in self.graph.stream(
                {"messages": chat_messages}, config, stream_mode="messages"
            ):

                # Handle the tuple format: (AIMessageChunk, metadata)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message_chunk, metadata = chunk
                    if hasattr(message_chunk, "content") and getattr(message_chunk, "content", None):
                        content = str(message_chunk.content)
                        node_name = metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
                        # Send properly formatted SSE data for each token
                        yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'node': node_name, 'approach': 'pure_langgraph'}})}\n\n"
                elif hasattr(chunk, "content") and getattr(chunk, "content", None):
                    # Direct AIMessageChunk object
                    content = str(getattr(chunk, "content", ""))
                    yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'approach': 'pure_langgraph'}})}\n\n"

            logger.info(f"Pure LangGraph streaming completed for thread {thread_id}")

        except Exception as e:
            logger.error(f"Error in pure LangGraph streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'approach': 'pure_langgraph'})}\n\n"

        # End of stream marker
        yield "data: [DONE]\n\n"

    def load_and_update_thread(
        self, thread_id: UUID | None, user_id: str, thread_label: str
    ) -> tuple[list[BaseMessage], UUID]:
        """Load or create conversation thread with message history.
        
        Handles both new thread creation and existing thread loading,
        including conversation history retrieval from the LangGraph checkpointer.
        
        Args:
            thread_id (UUID, optional): Existing thread ID. If None, creates new thread.
            user_id (str): User/session identifier
            thread_label (str): Label for the thread (required for new threads)
            
        Returns:
            tuple[list[BaseMessage], UUID]: Conversation messages and thread ID
            
        Side Effects:
            - For new threads: Updates thread_id parameter and saves to ThreadRepository
            - For existing threads: Validates thread exists
            
        Thread Creation (thread_id is None):
        1. Generate new UUID for thread
        2. Save thread metadata to ThreadRepository
        3. Initialize with system message
        
        Existing Thread Loading:
        1. Validate thread exists in ThreadRepository
        2. Load conversation history from LangGraph checkpointer
        3. Fallback to system message if history loading fails
        
        Error Handling:
        - Raises exception if existing thread not found
        - Graceful fallback for checkpointer failures
        - Logging for debugging conversation loading issues
        
        System Message:
            All conversations start with a system message defining the AI's role:
            "Hey! You are a helpful assistant expert in Crime and Law"
            
        Example:
            >>> messages = service.load_and_update_thread(
            ...     thread_id=None,
            ...     user_id="user123",
            ...     thread_label="Legal Questions"
            ... )
            >>> print(f"Loaded {len(messages)} messages")
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
                config = LangGraphServiceImpl._get_session_and_thread_config(thread_id, user_id)
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