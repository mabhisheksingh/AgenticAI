"""Central router dispatch and API aggregation.

This module aggregates all domain-specific routers into a single dispatch router
with versioned endpoints and provides a catch-all handler for undefined routes.
"""

"""Central router dispatch and API aggregation.

This module aggregates all domain-specific routers into a single dispatch router
with versioned endpoints and provides a catch-all handler for undefined routes.
"""
from typing import NoReturn

from fastapi import APIRouter

from app.core.enums import APIVersion, RouterTag
from app.core.errors import NotFoundError
from app.routers.AgenticRouter import agentic_router
from app.routers.UserRouter import user_router

# Central dispatch router that aggregates all domain routers
dispatch_router = APIRouter()

# Aggregate domain routers with versioned prefixes and tags
# User management endpoints: /v1/user/*
dispatch_router.include_router(
    user_router, prefix=f"/{APIVersion.v1.value}", tags=[RouterTag.user.value]
)

# AI agent and chat endpoints: /v1/agent/*
dispatch_router.include_router(
    agentic_router, prefix=f"/{APIVersion.v1.value}", tags=[RouterTag.agent.value]
)


@dispatch_router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], response_model=None
)
async def catch_all(path: str) -> NoReturn:
    """Catch-all handler for undefined API routes.

    Provides a consistent 404 response for any route that doesn't match
    the defined API endpoints. This ensures all undefined routes return
    a standardized error response.

    Args:
        path (str): The requested path that didn't match any defined routes

    Raises:
        NotFoundError: Always raises a 404 error with "Not Found" message

    Note:
        This handler matches all HTTP methods and paths, so it must be
        registered last to avoid intercepting valid routes.
    """
    raise NotFoundError("Not Found")
