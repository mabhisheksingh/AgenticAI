import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensures every request/response has a correlation ID.

    - Reads X-Correlation-ID from incoming request headers, or generates one.
    - Adds X-Correlation-ID to the response headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        # Stash on scope for downstream use (handlers can read request.state.correlation_id)
        request.state.correlation_id = cid
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Lightweight request logging with duration and status code."""

    def __init__(self, app: ASGIApp, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self.logger = logger or logging.getLogger("api")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
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
