from typing import NoReturn

from fastapi import APIRouter

from app.core.enums import APIVersion, RouterTag
from app.core.errors import NotFoundError
from app.routers.AgenticRouter import agentic_router
from app.routers.UserRouter import user_router

dispatch_router = APIRouter()
# Aggregate domain routers here
dispatch_router.include_router(
    user_router, prefix=f"/{APIVersion.v1.value}", tags=[RouterTag.user.value]
)
dispatch_router.include_router(
    agentic_router, prefix=f"/{APIVersion.v1.value}", tags=[RouterTag.agent.value]
)


@dispatch_router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], response_model=None
)
async def catch_all(path: str) -> NoReturn:
    raise NotFoundError("Not Found")
