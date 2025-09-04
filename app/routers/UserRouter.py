import logging
from typing import Any, Annotated, Coroutine
from uuid import UUID
from fastapi import APIRouter,Header, Query

from app.core.response import ok
from app.services.UserService import UserService

user_router = APIRouter(prefix="/user", tags=["user"])
user_service = UserService()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@user_router.get("/get-all")
async def get_user() -> dict[str, Any]:
    logger.info("Getting user called")
    return ok(user_service.get_all_user())

@user_router.delete("/{user_id}")
async def delete_user_by_id(user_id: str) -> dict:
    logger.info("Getting user called")
    affected = user_service.delete_user_by_id(user_id)
    return ok({"deleted": affected > 0, "affected": affected})



# New endpoints: list and delete threads by session (user)
@user_router.get("/threads")
def list_threads_by_session(
    user_id: Annotated[str, Header(...)],
) -> dict[str, Any]:
    rows = user_service.list_threads_by_session(user_id)
    return ok(rows)


@user_router.get("/thread/{thread_id}")
def get_thread_by_id(
    thread_id: UUID,
    user_id: Annotated[str, Header(...)],
) -> dict[str, Any]:
    row = user_service.get_thread_by_id(user_id, thread_id)
    return ok(row)


@user_router.delete("/threads/{thread_id}")
def delete_thread_by_session_and_id(
    thread_id: UUID,
    user_id: Annotated[str, Header(...)],
) -> dict[str, Any]:
    affected = user_service.delete_thread_by_session_and_id(user_id, str(thread_id))
    return ok({"deleted": affected > 0, "affected": affected})


@user_router.patch("/rename-thread-label")
def rename_thread_label(
    threadId: Annotated[UUID, Query(alias="threadId")],
    label: Annotated[str, Query()],
    user_id: Annotated[str, Header(...)],
) -> dict[str, Any]:
    affected = user_service.rename_thread_label(user_id, str(threadId), label)
    return ok({"renamed": affected > 0, "affected": affected})
