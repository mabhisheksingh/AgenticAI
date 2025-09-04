from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
from typing import Any
import uuid
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph

from app.config.SqlLiteConfig import get_sql_lite_instance
from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
from app.utils.text import to_plain_text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def serialize(obj):
    if isinstance(obj, BaseMessage):
        return obj.dict()
    return str(obj)


class LangGraphService:
    def __init__(self, llm):
        self.llm = llm
        # Compile the graph once per service instance and reuse
        builder = self._get_langgraph()
        # Use sync checkpointer - simpler and works
        self.graph = builder.compile(checkpointer=self._get_sql_lite_memory())
        self._async_graph = None  # Will be lazily initialized

    @staticmethod
    def _get_session_and_thread_config(thread_id: UUID | str, session_id: str) -> Any:
        config = {"configurable": {"thread_id": str(thread_id), "session_id": str(session_id)}}
        logger.info("Config: %s", config)
        return config

    # get sql lite checkpointer
    @staticmethod
    def _get_sql_lite_memory() -> SqliteSaver:
        sql_lite_instance = get_sql_lite_instance()
        memory = SqliteSaver(sql_lite_instance)
        return memory

    # Node
    def _chat_model_node(self, state: MessagesState):
        # Ensure we append the generated AIMessage to the messages list
        return {"messages": [self.llm.invoke(state["messages"])]}

    def _get_langgraph(self) -> StateGraph:
        builder = StateGraph(MessagesState)
        builder.add_node("chat_model", self._chat_model_node)
        builder.add_edge(START, "chat_model")
        builder.add_edge("chat_model", END)
        return builder

    async def _get_async_graph(self):
        """Just return the sync graph for now - simpler approach."""
        return self.graph

    async def execute_async(
        self, message: str, thread_id: UUID | None, user_id: str
    ) -> dict[str, Any]:
        """Async version of execute with proper checkpointing."""
        chat_messages = []
        is_new_thread = thread_id is None
        if is_new_thread:
            thread_id = uuid.uuid4()
            # Persist mapping between session (user) and thread
            try:
                ThreadRepository.save(session_id=user_id, thread_id=str(thread_id))
            except Exception:
                # Do not break the flow if persistence fails; proceed without blocking chat
                logger.exception("Failed to persist session-thread mapping")
            chat_messages.append(
                AIMessage(
                    content="Hey! You are a helpful assistant expert in Crime and Law",
                    name="assistant",
                )
            )
        else:
            row = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
            if not row:
                raise NotFoundError("Thread not found or invalid thread id for this user")

        chat_messages.append(HumanMessage(content=message))

        # Use async graph with checkpointing
        async_graph = await self._get_async_graph()
        config = LangGraphService._get_session_and_thread_config(thread_id, user_id)

        output = await async_graph.ainvoke({"messages": chat_messages}, config)
        output_messages = output["messages"]
        # Extract only the model's final text output
        try:
            last_ai = None
            for m in reversed(output_messages):
                if isinstance(m, AIMessage):
                    last_ai = m
                    break
            if last_ai is not None:
                answer = to_plain_text(last_ai.content)
            # Fallbacks
            elif hasattr(output_messages, "content"):
                answer = to_plain_text(output_messages.content)  # type: ignore[attr-defined]
            else:
                answer = to_plain_text(str(output_messages))
            return {
                "threadId": thread_id,
                "userId": user_id,
                "message": message,
                "response": answer,
            }
        except Exception:
            return {
                "threadId": thread_id,
                "userId": user_id,
                "message": message,
                "response": to_plain_text(str(output_messages)),
            }

    async def async_execute(
        self,
        message: str,
        thread_id: UUID | None,
        user_id: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
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

            # Load existing conversation history from checkpointer
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

        # Add the new user message
        chat_messages.append(HumanMessage(content=message))

        # Initial metadata event
        yield f"data: {json.dumps({'threadId': str(thread_id), 'userId': user_id})}\n\n"

        # Stream directly from LLM for token-level streaming
        response_content = ""
        try:
            async for chunk in self.llm.astream(chat_messages):
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    response_content += content
                    logger.info(f">>> Streaming token: {content}")
                    # Send properly formatted SSE data
                    yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'node': 'chat_model'}})}\n\n"

            # After streaming is complete, save the conversation to checkpointer
            if response_content.strip():  # Only save if we got a response
                try:
                    # Add the AI response to messages
                    chat_messages.append(AIMessage(content=response_content))

                    # Save to checkpointer using sync graph
                    config = LangGraphService._get_session_and_thread_config(thread_id, user_id)

                    # Invoke the graph to save the conversation
                    self.graph.invoke({"messages": chat_messages}, config)
                    logger.info(f"Saved conversation to checkpointer for thread {thread_id}")
                except Exception as save_error:
                    logger.error(f"Failed to save conversation to checkpointer: {save_error}")
                    # Don't break the streaming - just log the error

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # End of stream marker
        yield "data: [DONE]\n\n"

    def get_thread_by_id_async(self, thread_id: UUID, user_id: str) -> dict[str, Any]:
        """Get thread state using sync operations for now."""
        config = LangGraphService._get_session_and_thread_config(thread_id, user_id)
        state = self.graph.get_state(config)
        return state
