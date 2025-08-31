import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from app.dispatch import dispatch_router

load_dotenv()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="AgenticAI")
    # Controller Advice: register global exception handlers
    register_exception_handlers(application)

    # Cross-cutting middleware
    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(RequestLoggingMiddleware)

    # Include the dispatch user_router (it already contains versioned paths like /v1/...)
    application.include_router(dispatch_router)
    return application


app = create_app()
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8000"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
