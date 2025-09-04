from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Header
from fastapi.responses import StreamingResponse

from app.core.enums import RouterTag
from app.core.response import ok
from app.schemas.ChatRequest import ChatRequest
from app.services.AgentService import AgentService

agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])
agent_service = AgentService()


@agentic_router.post("/chat")
async def create_and_update_chat(
    userId: str = Header(...),
    body: ChatRequest = Body(...),
) -> StreamingResponse:
    message: str = body.message
    thread_id: UUID | None = body.thread_id
    thread_label: str = body.thread_label  # Now mandatory
    response = agent_service.create_and_update_chat(userId, thread_id, message, thread_label)
    return StreamingResponse(
        response,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# New endpoints: list and delete threads by session (user)
@agentic_router.get("/threads")
def list_threads_by_session(
    userId: Annotated[str, Header(...)],
) -> dict[str, Any]:
    rows = agent_service.list_threads_by_session(userId)
    return ok(rows)


@agentic_router.get("/thread/{thread_id}")
def get_thread_by_id(
    thread_id: UUID,
    userId: Annotated[str, Header(...)],
) -> dict[str, Any]:
    row = agent_service.get_thread_by_id(userId, thread_id)
    return ok(row)


@agentic_router.delete("/threads/{threadId}")
def delete_thread_by_session_and_id(
    threadId: UUID,
    userId: Annotated[str, Header(...)],
) -> dict[str, Any]:
    affected = agent_service.delete_thread_by_session_and_id(userId, str(threadId))
    return ok({"deleted": affected > 0, "affected": affected})


@agentic_router.patch("/rename-thread-label")
def rename_thread_label(
    threadId: UUID,
    userId: Annotated[str, Header(...)],
    label: str,
) -> dict[str, Any]:
    affected = agent_service.rename_thread_label(userId, str(threadId), label)
    return ok({"renamed": affected > 0, "affected": affected})
