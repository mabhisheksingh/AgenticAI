from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Header
from fastapi.responses import StreamingResponse

from app.core.enums import RouterTag
from app.schemas.ChatRequest import ChatRequest
from app.services.AgentService import AgentService

agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])
agent_service = AgentService()


@agentic_router.post("/chat")
async def create_and_update_chat(
    user_id: str = Header(...),
    body: ChatRequest = Body(...),
) -> StreamingResponse:
    message: str = body.message
    thread_id: UUID | None = body.thread_id
    thread_label: str = body.thread_label  # Now mandatory
    response = agent_service.stream_chat_tokens(user_id, thread_id, message, thread_label)
    return StreamingResponse(
        response,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
