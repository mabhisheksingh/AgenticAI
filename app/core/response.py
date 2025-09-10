"""Standardized response helpers for consistent API responses.

This module provides utility functions for creating consistent response
formats across all API endpoints, including success responses, error responses,
and paginated responses.
"""

from typing import Any


def ok(data: Any | None = None, meta: dict[str, Any] | None = None) -> dict:
    """Create a standardized success response envelope.

    Provides a consistent structure for all successful API responses
    with optional data payload and metadata.

    Args:
        data (Any, optional): The response data payload. Can be any JSON-serializable type.
        meta (dict[str, Any], optional): Additional metadata like pagination info,
            timestamps, or other contextual information.

    Returns:
        dict: Standardized success response with format:
            {
                "success": true,
                "data": <data>,
                "meta": <meta>
            }

    Example:
        >>> ok({"message": "Hello World"})
        {"success": True, "data": {"message": "Hello World"}, "meta": None}

        >>> ok([1, 2, 3], {"count": 3})
        {"success": True, "data": [1, 2, 3], "meta": {"count": 3}}

    Usage in FastAPI routes:
        @router.get("/items")
        async def list_items():
            items = get_items()
            return ok(items)
    """
    return {"success": True, "data": data, "meta": meta}


def error(
    code: str, message: str, details: dict[str, Any] | None = None, status: int | None = None
) -> dict:
    """Create a standardized error response envelope.

    Provides a consistent structure for error responses. However, it's recommended
    to use AppError exceptions instead of this function for better error handling.

    Args:
        code (str): Error code identifier (e.g., "VALIDATION_ERROR")
        message (str): Human-readable error message
        details (dict[str, Any], optional): Additional error details or context
        status (int, optional): HTTP status code (informational only in envelope)

    Returns:
        dict: Standardized error response with format:
            {
                "success": false,
                "error": {
                    "code": <code>,
                    "message": <message>,
                    "details": <details>  # optional
                },
                "status": <status>  # optional
            }

    Note:
        The 'status' field in the response is informational only.
        The actual HTTP status code should be set via exception handling
        or FastAPI response mechanisms.

    Example:
        >>> error("NOT_FOUND", "User not found", {"user_id": 123}, 404)
        {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "User not found",
                "details": {"user_id": 123}
            },
            "status": 404
        }

    Prefer using AppError:
        Instead of:
            return error("NOT_FOUND", "User not found")
        Use:
            raise NotFoundError("User not found")
    """
    # 'status' is informational only in this envelope; actual HTTP code should be set via exception or decorator
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    payload: dict[str, Any] = {"success": False, "error": body}
    if status is not None:
        payload["status"] = status
    return payload


def paginate(items: list[Any], total: int, page: int, size: int) -> dict:
    """Create a paginated response with metadata.

    Provides a standardized format for paginated API responses,
    including the data items and comprehensive pagination metadata.

    Args:
        items (list[Any]): The list of items for the current page
        total (int): Total number of items across all pages
        page (int): Current page number (typically 1-indexed)
        size (int): Number of items per page

    Returns:
        dict: Paginated response using ok() format with pagination metadata:
            {
                "success": true,
                "data": <items>,
                "meta": {
                    "pagination": {
                        "page": <page>,
                        "size": <size>,
                        "total": <total>,
                        "pages": <calculated_total_pages>
                    }
                }
            }

    Example:
        >>> paginate([{"id": 1}, {"id": 2}], total=10, page=1, size=2)
        {
            "success": True,
            "data": [{"id": 1}, {"id": 2}],
            "meta": {
                "pagination": {
                    "page": 1,
                    "size": 2,
                    "total": 10,
                    "pages": 5
                }
            }
        }

    Usage in FastAPI routes:
        @router.get("/users")
        async def list_users(page: int = 1, size: int = 10):
            users, total = get_users_page(page, size)
            return paginate(users, total, page, size)
    """
    return ok(
        data=items,
        meta={
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size if size else 0,
            }
        },
    )
