# Architecture

## System Overview
```
Frontend (React) ↔️ HTTP/SSE ↔️ FastAPI Backend ↔️ LLM Providers
                                          │
                                     SQLite DB
```

## Key Components
- **Services**: Business logic with dependency injection (`app/services/`)
- **Repositories**: Data access layer (SQLite) (`app/repositories/`)
- **AI Core**: Agents, tools, router, state graph (`app/ai_core/`)
- **Routers**: REST API endpoints (`app/routers/`)
- **Utilities**: Prompt builders, agent configs, logging helpers (`app/utils/`)

## Project Structure
```
app/
├── ai_core/         # Agents, tools, router, state graph
├── core/            # DI container, errors, middleware
├── repositories/    # Data access layer
├── routers/         # API endpoints
├── services/        # Business logic
├── schemas/         # Pydantic models
└── main.py          # FastAPI app

ui/
├── components/      # React components
├── hooks/           # Custom hooks (useChat, useThreads)
├── api/             # API integration
└── utils/           # Utility functions
```

## Multi-Agent Routing & Query Decomposition

Complex user queries are decomposed into atomic sub-queries and routed to specialized agents.

### How It Works
1. **LLM-based decomposition** into minimal sub-questions.
2. **Direct agent assignment** per sub-question (math, code, research) stored as `routes`.
3. **Sequential execution**: router dispatches one unprocessed subquery at a time.
4. **Result collection** in `subquery_results`; processed tracked via `done_queries`.
5. **Final formatting** in the `format_results` node.

### State Fields
- `routes`: Mapping of sub-queries -> agent name
- `subquery_results`: list[str]
- `done_queries`: list[str]
- `messages`: list[BaseMessage]
- `summary`: str

### StateGraph Flow
```
User Query → new_router
  ├─> new_router splits query with LLM → builds routes mapping
  ├─> next_agent_router identifies unprocessed queries
  ├─> routes subquery #1 → research
  │     └─> research result → new_router
  ├─> next_agent_router identifies next unprocessed query
  ├─> routes subquery #2 → code
  │     └─> code result → new_router
  ├─> next_agent_router identifies next unprocessed query
  ├─> routes subquery #3 → math
  │     └─> math result → new_router
  └─> all queries processed → format_results
        └─> format_results produces final answer
```

### Implementation Notes
- Query splitting in `app/ai_core/agents/new_router.py` and `app/ai_core/agents/router.py`.
- Orchestration in `app/ai_core/state_graph_object.py` with a `ToolNode` and `format_results`.
- Agent definitions driven by `AgentConfig` in `app/utils/agent_utils.py`.
- Prompts consolidated in `app/utils/prompt_utils.py`.
- Logging format in `app/utils/loging_utils.py`.
