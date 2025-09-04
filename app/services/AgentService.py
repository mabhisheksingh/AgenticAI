from __future__ import annotations

from collections.abc import AsyncGenerator
import logging
from typing import Any
from uuid import UUID

from app.agents.LLMFactory import LLMFactory
from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
from app.services.LangGraphService import LangGraphService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_get_langgraph_instance = lambda: LangGraphService(LLMFactory.create())


class AgentService:
    def __init__(self):
        pass

    @classmethod
    async def create_and_update_chat(
        cls,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
        logger.info("Creating and updating chat")
        lg = _get_langgraph_instance()
        async for chunk in lg.async_execute(message, thread_id, user_id, thread_label):
            yield chunk

    @classmethod
    def list_threads_by_session(cls, user_id: str) -> list[dict[str, Any]]:
        return ThreadRepository.get_session_by_id(user_id)

    @classmethod
    def delete_thread_by_session_and_id(cls, user_id: str, thread_id: str) -> int:
        return ThreadRepository.delete_by_session_and_thread(user_id, thread_id)

    @classmethod
    def rename_thread_label(cls, user_id: str, thread_id: str, label: str) -> int:
        return ThreadRepository.rename_thread_label(user_id, thread_id, label)

    @classmethod
    def get_thread_by_id(cls, user_id: str, thread_id: UUID) -> dict[str, Any]:
        logger.info("Getting thread by id")
        db_response = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
        if not db_response:
            raise NotFoundError("Thread not found")

        lg = _get_langgraph_instance()
        response_data = lg.get_thread_by_id_async(thread_id, user_id)

        # Return thread details with messages
        messages = []
        if response_data and response_data.values and "messages" in response_data.values:
            messages = [
                {
                    "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                    "content": msg.content,
                }
                for msg in response_data.values["messages"]
                if hasattr(msg, "content") and msg.content
            ]

        return {
            "thread_id": str(thread_id),
            "user_id": user_id,
            "messages": messages,
            "created_at": db_response.get("created_at"),
            "thread_label": db_response.get("thread_label"),
        }
