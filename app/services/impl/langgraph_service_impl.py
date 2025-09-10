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
from typing import cast
import uuid
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import StateSnapshot

from app.ai_core.agents.router import summarize_messages
from app.ai_core.llm_factory.llm_factory_interface import LLMFactoryInterface
from app.ai_core.state_graph_object import StateGraphObject
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.repositories import DatabaseConnectionProvider, ThreadRepositoryInterface
from app.services import (
    AgentExecutionInterface,
    ConversationStateInterface,
)

# Setup logging
logger = logging.getLogger(__name__)


def _content_to_text(content) -> str:
    """Normalize message content (str or content-part list) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return " ".join([p for p in parts if p])
    return str(content)


def _is_blank_message(msg: BaseMessage) -> bool:
    try:
        text = _content_to_text(getattr(msg, "content", ""))
        return not text or not text.strip()
    except Exception:
        return False


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
        chat_messages, actual_thread_id = self.load_and_update_thread(
            thread_id, user_id, thread_label
        )
        thread_id = actual_thread_id

        # Add the new user message as plain text content
        chat_messages.append(HumanMessage(content=message))

        # Summarize/prune messages if too long before streaming
        MAX_MESSAGES = 10
        if len(chat_messages) > MAX_MESSAGES:
            chat_messages = summarize_messages(chat_messages, inject(LLMFactoryInterface))
            logger.info(f"[SUPERVISOR] Summarized chat history due to length > {MAX_MESSAGES}")

        # Remove any blank messages to keep history clean
        if chat_messages:
            before = len(chat_messages)
            chat_messages = [m for m in chat_messages if not _is_blank_message(m)]
            after = len(chat_messages)
            if after != before:
                logger.info(f"Filtered {before - after} blank messages from history before streaming")

        # Initial metadata event
        yield f"data: {json.dumps({'threadId': str(thread_id), 'userId': user_id})}\n\n"

        # User message acknowledgment with processing indicator
        yield f"data: {json.dumps({'type': 'user', 'content': 'Got it 👍 you want ' + message})}\n\n"
        yield f"data: {json.dumps({'type': 'processing', 'content': 'Processing your request...'})}\n\n"

        try:
            if thread_id is None:
                raise ValueError("thread_id cannot be None at streaming time")

            config = self._get_session_and_thread_config(thread_id, user_id)
            logger.info("StateGraphObject: Starting streaming --> %s", chat_messages)

            # Create initial state with the messages
            # Note: We don't include the query or answer fields in the initial state to avoid
            # concurrent update errors. These are extracted from messages when needed.
            initial_state = {
                "messages": chat_messages,
            }

            # Stream through StateGraphObject
            logger.info(
                f"[SUPERVISOR] Starting graph streaming for thread_id={thread_id}, user_id={user_id}, initial_state={initial_state}"
            )
            for chunk in self.graph.stream(
                initial_state, config=config, stream_mode="updates", debug=True
            ):
                logger.info(f"[SUPERVISOR] Chunk received: {chunk}")
                # Handle streaming chunks
                if isinstance(chunk, dict):
                    for node_name, state_update in chunk.items():
                        logger.info(
                            f"[SUPERVISOR] Node {node_name} produced update: {state_update}"
                        )
                        # Check if the update is None (can happen with some graph configurations)
                        if state_update is None:
                            logger.warning(
                                f"[SUPERVISOR] Node {node_name} returned None update, skipping"
                            )
                            continue
                        # Check if the update contains new messages
                        if state_update.get("messages"):
                            messages = state_update["messages"]
                            if isinstance(messages, list) and len(messages) > 0:
                                latest_message = messages[-1]  # Get the last message
                                # Check if it's an AI message with content
                                if (
                                    hasattr(latest_message, "tool_calls")
                                    and latest_message.tool_calls
                                ):
                                    for tool_call in latest_message.tool_calls:
                                        logger.info(
                                            f"[SUPERVISOR] Tool call detected: {tool_call['name']} with args: {tool_call.get('args', {})}"
                                        )
                                        # Send tool call info to frontend
                                        tool_name = tool_call['name']
                                        yield f"data: {json.dumps({'type': 'tool_call', 'content': f'Executing {tool_name}...', 'metadata': {'node': node_name}})}\n\n"
                                if hasattr(latest_message, "content"):
                                    content = latest_message.content
                                    # Handle different content types
                                    if isinstance(content, list):
                                        # Extract human-readable text from content parts
                                        parts: list[str] = []
                                        for item in content:
                                            if isinstance(item, str):
                                                parts.append(item)
                                            elif isinstance(item, dict):
                                                if item.get("type") == "text":
                                                    parts.append(str(item.get("text", "")))
                                                else:
                                                    # Fallback to string for non-text parts
                                                    parts.append(str(item))
                                            else:
                                                parts.append(str(item))
                                        content = " ".join([p for p in parts if p])
                                    elif not isinstance(content, str):
                                        # If content is not a string, convert it to string
                                        content = str(content)

                                    # Check if content is not empty
                                    if content and content.strip():
                                        # For AIMessages, we should stream the content as tokens
                                        # Split the content into words and stream them one by one
                                        words = content.split()
                                        current_chunk = ""
                                        for i, word in enumerate(words):
                                            current_chunk += word + " "
                                            # Send a chunk every few words or at the end
                                            if (i + 1) % 10 == 0 or i == len(words) - 1:
                                                yield f"data: {json.dumps({'type': 'token', 'content': current_chunk.strip(), 'metadata': {'node': node_name}})}\n\n"
                                                current_chunk = ""
                                    elif (
                                        hasattr(latest_message, "tool_calls")
                                        and latest_message.tool_calls
                                    ):
                                        # This is a tool call, we don't stream it but log it
                                        logger.info(
                                            f"Tool call generated: {latest_message.tool_calls}"
                                        )
                        elif state_update.get("answer"):
                            # This is likely from one of the agent nodes
                            content = str(state_update["answer"])
                            # Split the content into words and stream them one by one
                            words = content.split()
                            current_chunk = ""
                            for i, word in enumerate(words):
                                current_chunk += word + " "
                                # Send a chunk every few words or at the end
                                if (i + 1) % 10 == 0 or i == len(words) - 1:
                                    yield f"data: {json.dumps({'type': 'token', 'content': current_chunk.strip(), 'metadata': {'node': node_name}})}\n\n"
                                    current_chunk = ""
                        else:
                            # Handle case where update doesn't contain expected fields
                            logger.warning(
                                f"Node {node_name} returned update without expected fields: {state_update}"
                            )

            logger.info(f"StateGraphObject streaming completed for thread {thread_id}")

        except Exception as e:
            logger.error(f"Error in StateGraphObject streaming: {e}", exc_info=True)
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
            # chat_messages.append(
            #     SystemMessage(content="Hey! You are a helpful assistant expert in Crime and Law")
            # )
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
                # else:
                # If no history found, start with system message
                # chat_messages.append(
                #     SystemMessage(
                #         content="Hey! You are a helpful assistant expert in Crime and Law"
                #     )
                # )
            except Exception as e:
                logger.error(f"Failed to load conversation history: {e}")
                # Fallback to system message if loading fails
                # chat_messages.append(
                #     SystemMessage(
                #         content="Hey! You are a helpful assistant expert in Crime and Law"
                #     )
                # )

        return chat_messages, thread_id