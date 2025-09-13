# Backend

This document describes the FastAPI backend, dependency injection, repositories, configuration, and how to run it.

## Overview
- Framework: FastAPI + Uvicorn
- Persistence: SQLite via `SqliteSaver` for LangGraph and a thread repository for metadata
- DI: Custom container in `app/core/di_container.py`
- API Routers: `app/dispatch.py` includes versioned routers (e.g., `/v1/agent/*`, `/v1/user/*`)
- Default port: `8080`

## Dependency Injection
See `app/core/di_container.py`.

Interfaces bound:
- `AgentExecutionInterface` → `LangGraphServiceImpl` (singleton)
- `ConversationStateInterface` → `LangGraphServiceImpl` (same singleton)
- `AgentServiceInterface` → `AgentServiceImpl`
- `ThreadRepositoryInterface`, `ThreadQueryInterface`, `UserRepositoryInterface` → `ThreadRepositoryImpl`
- `DatabaseConnectionProvider` → SQLite connection provider

Key factory (summary):
```python
# app/core/di_container.py (excerpt)
from app.services import AgentExecutionInterface, ConversationStateInterface
from app.services.impl.langgraph_service_impl import LangGraphServiceImpl

def langgraph_service_factory():
    thread_repository = container.resolve(ThreadRepositoryInterface)
    db_provider = container.resolve(DatabaseConnectionProvider)
    return LangGraphServiceImpl(thread_repository, db_provider)

container.register_factory(AgentExecutionInterface, langgraph_service_factory)
container.register_factory(ConversationStateInterface, langgraph_service_factory)
```

## Services
- `app/services/agent_service_interface.py`: contracts (AgentServiceInterface, AgentExecutionInterface, ConversationStateInterface)
- `app/services/impl/agent_service_impl.py`: coordinates stream with `execute_agent()`
- `app/services/impl/langgraph_service_impl.py`: orchestrates LangGraph graph, streaming SSE
- `app/services/impl/user_service_impl.py`: user/thread business logic

## Repositories
- `app/repositories/impl/thread_repository_impl.py`: thread/session metadata persistence
- `app/repositories/*`: interfaces and provider

## Configuration
- `.env`:
  - `HOST=0.0.0.0`
  - `PORT=8080`
  - `LLM_SMALL_MODEL`, `LLM_MEDIUM_MODEL`, `LLM_LARGE_MODEL`, `LLM_CORRECTION_MODEL`, etc.
- `app/main.py` reads these values and registers middleware/routers.

## Run
```bash
# Development
python -m app.main  # Starts on http://localhost:8080

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Health Checks
```bash
# API docs
curl http://localhost:8080/docs

# DB
python -c "from app.config.SqlLiteConfig import get_sql_lite_instance; print('DB OK')"

# LLM model/provider mapping
python -c "import os; from app.utils.llm_utils import MODEL_PROVIDER_MAP; m=os.getenv('LLM_MEDIUM_MODEL'); print('LLM_MEDIUM_MODEL:', m); print('Provider:', MODEL_PROVIDER_MAP.get(m))"
```

## Middleware
- `CorrelationIdMiddleware` for request tracing
- `RequestLoggingMiddleware` for structured logs

## Notes
- Backend streams responses with SSE from `/v1/agent/chat`.
- DI container is initialized in `create_app()` before middleware and routers.
