from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
from typing import Any, List
import uuid
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import StateSnapshot

from app.agents.LLMFactory import LLMFactory
from app.config.SqlLiteConfig import get_sql_lite_instance, DB_PATH
from app.repositories.ThreadRepository import ThreadRepository

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
    def __init__(self):
        self.llm = LLMFactory.create()
        # Compile hybrid graph with sync checkpointer
        state_graph = self.prepare_state_graph()
        checkpointer = self._get_sql_lite_memory()
        self.graph = state_graph.compile(checkpointer=checkpointer)

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

    # Node for sync/hybrid approach
    def call_llm(self, state: MessagesState):
        # Ensure we append the generated AIMessage to the messages list
        return {"messages": [self.llm.invoke(state["messages"])]}


    def prepare_state_graph(self) -> StateGraph:
        """Build standard LangGraph for hybrid approach."""
        builder = StateGraph(MessagesState)
        builder.add_node("chat_model", self.call_llm)
        builder.add_edge(START, "chat_model")
        builder.add_edge("chat_model", END)
        return builder


    def get_thread_by_id_async(self, thread_id: UUID, user_id: str) -> StateSnapshot:
        """Get thread state using sync operations for now."""
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
        """Pure LangGraph streaming approach using LangGraph's native streaming capabilities."""
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
            config = LangGraphService._get_session_and_thread_config(thread_id, user_id)
            
            # Stream through LangGraph's native streaming system with messages mode
            for chunk in self.graph.stream(
                {"messages": chat_messages}, 
                config,
                stream_mode="messages"
            ):
                logger.info(f"Pure LangGraph chunk: {chunk}")
                
                # Handle the tuple format: (AIMessageChunk, metadata)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message_chunk, metadata = chunk
                    if hasattr(message_chunk, 'content') and message_chunk.content:
                        content = message_chunk.content
                        node_name = metadata.get('langgraph_node', 'unknown')
                        logger.info(f">>> Pure LangGraph streaming token: '{content}'")
                        # Send properly formatted SSE data for each token
                        yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'node': node_name, 'approach': 'pure_langgraph'}})}\n\n"
                elif hasattr(chunk, 'content') and chunk.content:
                    # Direct AIMessageChunk object
                    content = chunk.content
                    logger.info(f">>> Pure LangGraph streaming token: '{content}'")
                    yield f"data: {json.dumps({'type': 'token', 'content': content, 'metadata': {'approach': 'pure_langgraph'}})}\n\n"

            logger.info(f"Pure LangGraph streaming completed for thread {thread_id}")
            # LangGraph handles checkpointing automatically through its workflow

        except Exception as e:
            logger.error(f"Error in pure LangGraph streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'approach': 'pure_langgraph'})}\n\n"

        # End of stream marker
        yield "data: [DONE]\n\n"

    def load_and_update_thread(self, thread_id: UUID, user_id: str, thread_label: str) -> List[BaseMessage]:
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
