from typing import Any


def ok(data: Any | None = None, meta: dict[str, Any] | None = None) -> dict:
    """Standard success envelope (HTTP 200 by default).

    Usage in route:
        @router.get("/items")
        async def list_items():
            return ok(data)
    """
    return {"success": True, "data": data, "meta": meta}


def error(
    code: str, message: str, details: dict[str, Any] | None = None, status: int | None = None
) -> dict:
    """Standard error envelope. Prefer raising AppError; this is for manual shaping if needed."""
    # 'status' is informational only in this envelope; actual HTTP code should be set via exception or decorator
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    payload: dict[str, Any] = {"success": False, "error": body}
    if status is not None:
        payload["status"] = status
    return payload


def paginate(items: list[Any], total: int, page: int, size: int) -> dict:
    """Helper for paginated responses."""
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
