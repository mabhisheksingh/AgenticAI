import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.SqlLiteConfig import close_sql_lite_instance
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

    # CORS for UI access (origins from env: CORS_ORIGINS="http://localhost:5173,https://your-app.com")
    origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the dispatch user_router (it already contains versioned paths like /v1/...)
    application.include_router(dispatch_router)

    # Graceful shutdown: close the singleton SQLite connection
    @application.on_event("shutdown")
    def _close_db_conn() -> None:  # pragma: no cover - simple resource cleanup
        close_sql_lite_instance()

    return application


app = create_app()
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8000"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
