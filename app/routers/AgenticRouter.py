from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header

from app.core.enums import RouterTag
from app.core.response import ok
from app.schemas.chat import ChatMessageBody, ChatMessageResponse
from app.services.AgentService import AgentService

agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])
agent_service = AgentService()


@agentic_router.post("/chat", response_model=ChatMessageResponse)
async def create_and_update_chat(
    payload: ChatMessageBody,
    userId: Annotated[str, Header(...)],
    threadId: Annotated[UUID | None, Header()] = None,
) -> ChatMessageResponse:
    return agent_service.create_and_update_chat(userId, threadId, payload.message)


# New endpoints: list and delete threads by session (user)
@agentic_router.get("/threads")
async def list_threads_by_session(
    userId: Annotated[str, Header(...)],
) -> dict[str, Any]:
    rows = agent_service.list_threads_by_session(userId)
    return ok(rows)


@agentic_router.delete("/threads/{threadId}")
async def delete_thread_by_session_and_id(
    threadId: UUID,
    userId: Annotated[str, Header(...)],
) -> dict[str, Any]:
    affected = agent_service.delete_thread_by_session_and_id(userId, str(threadId))
    return ok({"deleted": affected > 0, "affected": affected})
