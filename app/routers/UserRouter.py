import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query

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
    """
    Retrieve all user IDs in the system.
    
    Returns a list of all unique user IDs that have created threads.
    This endpoint is useful for user management and admin interfaces.
    
    Returns:
        dict[str, Any]: Standard response envelope containing:
            - success: True
            - data: List of user ID strings
            - meta: None
            
    Example Response:
        {
            "success": true,
            "data": ["user-123", "admin", "alice"],
            "meta": null
        }
    """
    logger.info("Getting user called")
    return ok(user_service.get_all_user())


@user_router.delete("/{user_id}")
async def delete_user_by_id(user_id: str) -> dict:
    """
    Delete a user and all associated threads.
    
    This endpoint removes a user completely from the system, including
    all their conversation threads and related data.
    
    Args:
        user_id (str): The unique identifier of the user to delete
        
    Returns:
        dict: Standard response envelope containing:
            - success: True
            - data: Object with deletion status
                - deleted: Boolean indicating if deletion occurred
                - affected: Number of records deleted
            - meta: None
            
    Example Response:
        {
            "success": true,
            "data": {"deleted": true, "affected": 5},
            "meta": null
        }
    """
    logger.info("Getting user called")
    affected = user_service.delete_user_by_id(user_id)
    return ok({"deleted": affected > 0, "affected": affected})


# New endpoints: list and delete threads by session (user)
@user_router.get("/threads")
def list_threads_by_session(
    user_id: Annotated[str, Header(...)],
) -> dict[str, Any]:
    """
    List all conversation threads for a specific user.
    
    Retrieves all threads associated with the user identified by the user-id header.
    Each thread includes metadata such as creation time and thread label.
    
    Headers:
        user-id (str): The unique identifier of the user whose threads to retrieve
        
    Returns:
        dict[str, Any]: Standard response envelope containing:
            - success: True
            - data: List of thread objects, each containing:
                - thread_id: Unique thread identifier (UUID)
                - thread_label: Human-readable thread name
                - created_at: Thread creation timestamp
                - session_id: Associated user session
            - meta: None
            
    Example Response:
        {
            "success": true,
            "data": [
                {
                    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                    "thread_label": "Planning Meeting",
                    "created_at": "2024-01-15T10:30:00Z",
                    "session_id": "user-123"
                }
            ],
            "meta": null
        }
    """
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
    """
    Update the label/name of a conversation thread.
    
    Allows users to rename their conversation threads with custom labels
    for better organization and identification.
    
    Query Parameters:
        threadId (UUID): The unique identifier of the thread to rename
        label (str): The new label/name for the thread
        
    Headers:
        user-id (str): The unique identifier of the user who owns the thread
        
    Returns:
        dict[str, Any]: Standard response envelope containing:
            - success: True
            - data: Object with rename operation status
                - renamed: Boolean indicating if rename was successful
                - affected: Number of records updated (should be 1 if successful)
            - meta: None
            
    Example Request:
        PATCH /v1/user/rename-thread-label?threadId=550e8400-e29b-41d4-a716-446655440000&label=My%20Chat
        Headers: user-id: user-123
        
    Example Response:
        {
            "success": true,
            "data": {"renamed": true, "affected": 1},
            "meta": null
        }
        
    Error Cases:
        - Thread not found: Returns success=true, renamed=false, affected=0
        - Thread belongs to different user: Returns success=true, renamed=false, affected=0
    """
    affected = user_service.rename_thread_label(user_id, str(threadId), label)
    return ok({"renamed": affected > 0, "affected": affected})
