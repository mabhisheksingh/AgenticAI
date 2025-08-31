from typing import Any

from fastapi import APIRouter

from app.core.enums import RouterTag
from app.services.UserService import get_user_service

agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])


@agentic_router.get("/")
async def get_user() -> dict[str, Any]:
    return get_user_service()
