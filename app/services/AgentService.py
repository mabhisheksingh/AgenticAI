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
    def __init__(self):
        pass

    @classmethod
    async def stream_chat_tokens(
        cls,
        user_id: str,
        thread_id: UUID | None,
        message: str,
        thread_label: str,  # Now mandatory
    ) -> AsyncGenerator[str, None]:
        logger.info("Streaming chat tokens")
        logger.info("langgraph instance created and now Executing agent....")
        async for chunk in langgraph_service.execute_agent(
            message, thread_id, user_id, thread_label
        ):
            yield chunk
