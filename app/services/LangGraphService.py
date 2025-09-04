"""LangGraph service for AI agent orchestration and conversation management.

This module provides the core AI agent functionality using LangGraph for
workflow orchestration, message handling, and conversation state management
with SQLite persistence.
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

from app.agents.LLMFactory import LLMFactory
from app.config.SqlLiteConfig import get_sql_lite_instance
from app.repositories.ThreadRepository import ThreadRepository

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


class LangGraphService:
    """Service for AI agent orchestration using LangGraph workflows.
    
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
    - LLMFactory for language model instantiation
    - ThreadRepository for thread metadata management
    
    The service builds a simple workflow: START → chat_model → END
    where the chat_model node invokes the LLM with conversation history.
    """
    def __init__(self):
        """Initialize the LangGraphService with LLM and compiled graph.
        
        Sets up the complete LangGraph workflow including:
        - LLM instance from factory
        - State graph compilation
        - SQLite checkpointer configuration
        - Graph compilation with checkpointing enabled
        """
        self.llm = LLMFactory.create()
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

    # get sql lite checkpointer
    @staticmethod
    def _get_sql_lite_memory() -> SqliteSaver:
        """Create and configure SQLite-based conversation checkpointer.
        
        Sets up the LangGraph checkpointer using the application's SQLite
        database instance for persistent conversation state management.
        
        Returns:
            SqliteSaver: Configured SQLite checkpointer for LangGraph
            
        Note:
            Uses the same SQLite connection as the rest of the application
            for consistent data storage and transaction management.
        """
        sql_lite_instance = get_sql_lite_instance()
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

    def get_thread_by_id_async(self, thread_id: UUID, user_id: str) -> StateSnapshot:
        """Retrieve conversation state for a specific thread.
        
        Loads the current state of a conversation thread including all
        messages and metadata from the LangGraph checkpointer.
        
        Args:
            thread_id (UUID): Thread identifier to retrieve state for
            user_id (str): User/session identifier for context
            
        Returns:
            StateSnapshot: Current state of the conversation thread
            
        Note:
            Uses synchronous operations for now, but named with 'async'
            suffix for future async migration compatibility.
        """
        config = LangGraphService._get_session_and_thread_config(thread_id, user_id)
        state = self.graph.get_state(config)
        return state

    async def execute_agent(
        self,
        message: str,
        thread_id: UUID | None,
        user_id: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
        """Execute AI agent with streaming response generation.
        
        Orchestrates a complete AI agent interaction including thread management,
        conversation history loading, message processing, and streaming response
        generation using LangGraph's native streaming capabilities.
        
        Args:
            message (str): User's input message to process
            thread_id (UUID, optional): Existing thread ID to continue conversation.
                If None, creates a new thread.
            user_id (str): User/session identifier
            thread_label (str): Label for the thread (required for new threads)
            
        Yields:
            str: Server-Sent Events (SSE) formatted strings containing:
                - Initial metadata (thread ID, user ID)
                - Streaming response tokens with metadata
                - End-of-stream marker
                
        Workflow:
        1. Load or create conversation thread
        2. Load conversation history from checkpointer
        3. Add user message to conversation
        4. Stream AI response using LangGraph native streaming
        5. Automatic state persistence via checkpointer
        
        SSE Response Format:
            - data: {"threadId": "uuid", "userId": "user123"}
            - data: {"type": "token", "content": "Hello", "metadata": {...}}
            - data: [DONE]
            
        Error Handling:
        - Graceful fallback for conversation history loading failures
        - Error messages streamed in SSE format
        - Comprehensive logging for debugging
        
        Thread Management:
        - New threads: Auto-generated UUID, saved to ThreadRepository
        - Existing threads: Validated and history loaded from checkpointer
        - System message injection for new conversations
        
        Example:
            >>> async for chunk in service.execute_agent(
            ...     message="Hello",
            ...     thread_id=None,
            ...     user_id="user123",
            ...     thread_label="My Chat"
            ... ):
            ...     print(chunk)  # SSE-formatted response
        """
        logger.info("Thread ID: %s", thread_id)
        logger.info("User ID: %s", user_id)
        logger.info("Thread Label: %s", thread_label)
        logger.info("Message: %s", message)
        chat_messages = self.load_and_update_thread(thread_id, user_id, thread_label)
        logger.info("Chat Messages: %s", chat_messages)

        # if is_new_thread:
        #     thread_id = uuid.uuid4()
        #     # Always save thread_label since it's now mandatory
        #     ThreadRepository.save(
        #         session_id=user_id, thread_id=str(thread_id), thread_label=thread_label
        #     )
        #     chat_messages.append(
        #         SystemMessage(content="Hey! You are a helpful assistant expert in Crime and Law")
        #     )
        # else:
        #     row = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
        #     if not row:
        #         raise Exception("Thread not found")
        #
        #     # Load existing conversation history from LangGraph checkpointer
        #     try:
        #         config = LangGraphService._get_session_and_thread_config(thread_id, user_id)
        #         state = self.graph.get_state(config)
        #
        #         if state and state.values and "messages" in state.values:
        #             chat_messages = state.values["messages"]
        #             logger.info(f"Loaded {len(chat_messages)} messages from thread history")
        #         else:
        #             # If no history found, start with system message
        #             chat_messages.append(
        #                 SystemMessage(
        #                     content="Hey! You are a helpful assistant expert in Crime and Law"
        #                 )
        #             )
        #     except Exception as e:
        #         logger.error(f"Failed to load conversation history: {e}")
        #         # Fallback to system message if loading fails
        #         chat_messages.append(
        #             SystemMessage(
        #                 content="Hey! You are a helpful assistant expert in Crime and Law"
        #             )
        #         )

        # Add the new user message
        chat_messages.append(HumanMessage(content=message))

        # Initial metadata event
        yield f"data: {json.dumps({'threadId': str(thread_id), 'userId': user_id})}\n\n"

        # Pure LangGraph approach: Use LangGraph's astream for workflow-native streaming

        try:
            # Use the existing streaming graph (sync version works with stream_mode="messages")
            # Ensure thread_id is not None at this point
            if thread_id is None:
                raise ValueError("thread_id cannot be None at streaming time")
            
            config = LangGraphService._get_session_and_thread_config(thread_id, user_id)

            # Stream through LangGraph's native streaming system with messages mode
            for chunk in self.graph.stream(
                {"messages": chat_messages}, config, stream_mode="messages"
            ):
                logger.info(f"Pure LangGraph chunk: {chunk}")

                # Handle the tuple format: (AIMessageChunk, metadata)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message_chunk, metadata = chunk
                    if hasattr(message_chunk, "content") and getattr(message_chunk, "content", None):
                        content = str(message_chunk.content)
                        node_name = metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
                        logger.info(f">>> Pure LangGraph streaming token: '{content}'")
                        # Send properly formatted SSE data for each token
                        yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'node': node_name, 'approach': 'pure_langgraph'}})}\n\n"
                elif hasattr(chunk, "content") and getattr(chunk, "content", None):
                    # Direct AIMessageChunk object
                    content = str(getattr(chunk, "content", ""))
                    logger.info(f">>> Pure LangGraph streaming token: '{content}'")
                    yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'approach': 'pure_langgraph'}})}\n\n"

            logger.info(f"Pure LangGraph streaming completed for thread {thread_id}")
            # LangGraph handles checkpointing automatically through its workflow

        except Exception as e:
            logger.error(f"Error in pure LangGraph streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'approach': 'pure_langgraph'})}\n\n"

        # End of stream marker
        yield "data: [DONE]\n\n"

    def load_and_update_thread(
        self, thread_id: UUID | None, user_id: str, thread_label: str
    ) -> list[BaseMessage]:
        """Load or create conversation thread with message history.
        
        Handles both new thread creation and existing thread loading,
        including conversation history retrieval from the LangGraph checkpointer.
        
        Args:
            thread_id (UUID, optional): Existing thread ID. If None, creates new thread.
            user_id (str): User/session identifier
            thread_label (str): Label for the thread (required for new threads)
            
        Returns:
            list[BaseMessage]: Conversation messages for the thread
            
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
            ThreadRepository.save(
                session_id=user_id, thread_id=str(thread_id), thread_label=thread_label
            )
            chat_messages.append(
                SystemMessage(content="Hey! You are a helpful assistant expert in Crime and Law")
            )
        else:
            row = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
            if not row:
                raise Exception("Thread not found")

            # Load existing conversation history from LangGraph checkpointer
            try:
                config = LangGraphService._get_session_and_thread_config(thread_id, user_id)
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

        return chat_messages
