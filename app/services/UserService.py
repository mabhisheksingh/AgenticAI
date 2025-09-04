from __future__ import annotations

from typing import Any
from uuid import UUID
import logging

from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
from app.services.LangGraphService import LangGraphService

logger = logging.getLogger(__name__)
langgraph_service = LangGraphService()
class UserService:
    def __init__(self):
        pass

    @classmethod
    def get_all_user(cls) -> list[str]:
        all_user = ThreadRepository.get_all_user()
        return all_user

    @classmethod
    def delete_user_by_id(cls,user_id: str) -> int:
        status = ThreadRepository.delete_user_by_id(user_id)
        return status


    @classmethod
    def list_threads_by_session(cls, user_id: str) -> list[dict[str, Any]]:
        return ThreadRepository.get_session_by_id(user_id)

    @classmethod
    def delete_thread_by_session_and_id(cls, user_id: str, thread_id: str) -> int:
        return ThreadRepository.delete_by_session_and_thread(user_id, thread_id)

    @classmethod
    def rename_thread_label(cls, user_id: str, thread_id: str, label: str) -> dict[str, Any] | None:
        return ThreadRepository.rename_thread_label(user_id, thread_id, label)

    @classmethod
    def get_thread_by_id(cls, user_id: str, thread_id: UUID) -> dict[str, Any]:
        logger.info("Getting thread by id")
        db_response = ThreadRepository.get_by_session_and_thread(user_id, str(thread_id))
        if not db_response:
            raise NotFoundError("Thread not found")
        response_data = langgraph_service.get_thread_by_id_async(thread_id, user_id)

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
