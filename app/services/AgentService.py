from __future__ import annotations

import logging
from typing import Any
import uuid
from uuid import UUID



from app.agents.LLMFactory import LLMFactory
from app.config.SqlLiteConfig import get_sql_lite_instance
from app.core.enums import LLMProvider
from app.core.errors import NotFoundError
from app.repositories.ThreadRepository import ThreadRepository
from app.services.LangGraphService import LangGraphService
from app.utils.text import to_plain_text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        pass

    @classmethod
    def create_and_update_chat(
        cls, user_id: str, thread_id: UUID | None, message: str
    ) -> dict[str, Any]:
        logger.info("Creating and updating chat")
        llm = LLMFactory.create()
        logger.info("LLM: %s", llm)

        # response = llm.invoke(message)
        logger.info("Invoking llm")
        lg = LangGraphService(llm)
        response = lg.execute(message, thread_id, user_id)
        # logger.info("Response: %s", response)
        return response

    @classmethod
    def list_threads_by_session(cls, user_id: str) -> list[dict[str, Any]]:
        return ThreadRepository.get_session_by_id(user_id)

    @classmethod
    def delete_thread_by_session_and_id(cls, user_id: str, thread_id: str) -> int:
        return ThreadRepository.delete_by_session_and_thread(user_id, thread_id)

    @classmethod
    def rename_thread_label(cls, user_id: str, thread_id: str, label: str) -> int:
        return ThreadRepository.rename_thread_label(user_id, thread_id, label)

