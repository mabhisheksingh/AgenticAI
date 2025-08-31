from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header

from app.core.enums import RouterTag
from app.schemas.chat import ChatMessageBody, ChatMessageResponse
from app.services.AgentService import AgentService
from app.services.UserService import get_user_service

agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])
agent_service = AgentService()


@agentic_router.post("/chat", response_model=ChatMessageResponse)
async def create_and_update_chat(
    payload: ChatMessageBody,
    userId: Annotated[str, Header(...)],
    threadId: Annotated[UUID | None, Header()] = None,
) -> ChatMessageResponse:
    return agent_service.create_and_update_chat(userId, threadId, payload.message)


@agentic_router.get("/chat/history")
async def get_all_chat_history() -> dict[str, Any]:
    return get_user_service()


@agentic_router.delete("/chat/delete/{thread_id}")
async def delete_chat_by_thread_id() -> dict[str, Any]:
    return get_user_service()
