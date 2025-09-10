"""ASGI middleware components for request processing and observability.

This module provides middleware for correlation ID tracking and request logging,
enhancing observability and traceability across the application.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware for correlation ID management across requests.

    Ensures every request has a unique correlation ID for tracing and debugging.
    The correlation ID is either extracted from incoming request headers or
    automatically generated if not present.

    Features:
    - Reads X-Correlation-ID from request headers
    - Generates new UUID if correlation ID not provided
    - Adds correlation ID to response headers
    - Stores correlation ID in request state for downstream access

    Usage:
        app.add_middleware(CorrelationIdMiddleware)

    Access in handlers:
        correlation_id = request.state.correlation_id
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the correlation ID middleware.

        Args:
            app (ASGIApp): The ASGI application to wrap
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with correlation ID handling.

        Args:
            request (Request): The incoming HTTP request
            call_next (RequestResponseEndpoint): The next middleware/handler in chain

        Returns:
            Response: HTTP response with correlation ID header added
        """
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        # Stash on scope for downstream use (handlers can read request.state.correlation_id)
        request.state.correlation_id = cid
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request logging and performance monitoring.

    Logs all incoming requests with method, path, status code, duration,
    and correlation ID for observability and debugging.

    Features:
    - Logs request method and path
    - Measures and logs request duration in milliseconds
    - Includes response status code
    - Associates logs with correlation ID
    - Handles exceptions gracefully with proper logging

    Args:
        app (ASGIApp): The ASGI application to wrap
        logger (logging.Logger, optional): Custom logger instance.
            Defaults to logger named 'api'

    Usage:
        app.add_middleware(RequestLoggingMiddleware)

    Log Format:
        method=GET path=/api/v1/users status=200 duration_ms=45.23 cid=uuid-here
    """

    def __init__(self, app: ASGIApp, logger: logging.Logger | None = None) -> None:
        """Initialize the request logging middleware.

        Args:
            app (ASGIApp): The ASGI application to wrap
            logger (logging.Logger, optional): Custom logger. Defaults to 'api' logger.
        """
        super().__init__(app)
        self.logger = logger or logging.getLogger("api")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with timing and logging.

        Measures request duration and logs comprehensive request information
        including method, path, status, duration, and correlation ID.

        Args:
            request (Request): The incoming HTTP request
            call_next (RequestResponseEndpoint): The next middleware/handler in chain

        Returns:
            Response: The HTTP response from downstream handlers
        """
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            method = request.method
            path = request.url.path
            status = getattr(locals().get("response", None), "status_code", "-")
            cid = getattr(request.state, "correlation_id", "-")
            self.logger.info(
                "method=%s path=%s status=%s duration_ms=%.2f cid=%s",
                method,
                path,
                status,
                duration_ms,
                cid,
            )
