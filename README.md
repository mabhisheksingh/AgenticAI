# AgenticAI API (FastAPI)

A production-ready FastAPI backend for an Agentic AI application. Users submit a task, and the system routes the request to the appropriate agent(s)/tool(s) to accomplish it. The architecture emphasizes clean routing, versioning, service layers, global error handling, and strong developer tooling.

## Key Features
- **Versioned API and centralized routing** via `dispatch_router` and `APIVersion` enum.
- **Domain routers** (e.g., `UserRouter`, `AgenticRouter`) aggregated behind a clean versioned prefix.
- **Service layer** for business logic (`app/services/`).
- **Controller advice (global exception handling)** that returns a simple list-of-errors JSON for failures.
- **Standard response envelope** helpers for success and pagination (`ok()`, `paginate()`); errors use the list format.
- **Observability middleware**: correlation ID propagation and request logging.
- **Tooling**: Ruff, Black, isort, mypy, Bandit, pytest, pre-commit; unified `Makefile`.
- **Agent chat with LangGraph**: compiled once per service instance for performance and persisted with SQLite checkpointer.
- **SQLite singleton connection** with graceful shutdown to avoid connection churn and locking.

## Project Structure
```
app/
  core/
    __init__.py
    enums.py                 # APIVersion, RouterTag, ErrorCode
    errors.py                # AppError, NotFoundError, ApiErrorItem (alias-keyed items)
    exception_handlers.py    # Global handlers for AppError, validation errors, 500s
    middleware.py            # CorrelationIdMiddleware, RequestLoggingMiddleware
    response.py              # ok(), error(), paginate()
  agents/
    LLMFactory.py            # Factory to create LLMs (e.g., Ollama/OpenAI)
  routers/
    UserRouter.py            # /user endpoints
    AgenticRouter.py         # /agent endpoints
  services/
    UserService.py           # Example service implementation
    AgentService.py          # LangGraph chat + to_plain_text normalization
  repositories/
    ThreadRepository.py      # Session-thread mapping CRUD (snake_case API)
  utils/
    __init__.py
    text.py                  # to_plain_text() utility to normalize LangChain content
  config/
    SqlLiteConfig.py         # Singleton SQLite connection + schema + SQLITE_DB_PATH
  dispatch.py                # Aggregates domain routers under /v{n}
  main.py                    # FastAPI app creation & bootstrapping
  db/
    chat.db                  # Default SQLite database location (created on first run)

requirements.txt             # Runtime deps
requirements-dev.txt         # Dev/test/lint/type deps
pyproject.toml               # Tooling config: Ruff, Black, isort, pytest
mypy.ini                     # mypy config
.pre-commit-config.yaml      # Git hooks
Makefile                     # One-liner commands for quality gates
LICENSE
ui/
  .env
  package.json
  vite.config.js
  src/
    main.jsx
    App.jsx
    components/
      ChatWindow.jsx
      Sidebar.jsx
      ThreadList.jsx
    utils/
      api.js
      storage.js

## Prerequisites
- Python 3.11+
- pip (and optionally pipenv)
- make (recommended for convenience)
- Ollama (required by default, since `AgentService` uses the Ollama provider)
  - Install: macOS/Linux
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
  - Pull a model (example):
    ```bash
    ollama pull llama3.1
    ```
  - Run server (usually auto-starts):
    ```bash
    ollama serve
    ```
- Node.js 18+
- npm (comes with Node.js)

## Quick Start
1) Clone and enter the repo
```bash
git clone <your-fork-or-origin-url> AgenticAI
cd AgenticAI
```

2) Create a virtualenv and install dependencies (recommended)
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Optional: using pipenv instead of venv
```bash
pipenv install --dev
```

3) Configure environment variables
Create a `.env` file in the repository root (examples below). The default LLM provider in `AgentService` is Ollama.

```env
# --- Server ---
HOST=0.0.0.0
PORT=8000

# --- SQLite (optional) ---
# Path to the SQLite DB file. Defaults to app/db/chat.db if not set.
# SQLITE_DB_PATH=./app/db/chat.db

# --- LLM Provider Selection ---
LLM_PROVIDER=google_genai   # or 'ollama'

# --- Google Gemini Settings ---
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL_NAME=gemini-2.5-flash

# --- Ollama Settings ---
OLLAMA_MODEL_NAME=llama3.1:8b

# --- Common LLM Settings ---
LLM_TEMPERATURE=0.7
```

4) Run the API server
- With uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Or via Python module (uses HOST/PORT from .env):
```bash
python -m app.main
```
- Or with pipenv:
```bash
pipenv run uvicorn app.main:app --reload
```

5) Run the UI
```bash
cd ui
npm install
npm run dev
```

Open http://localhost:5173 for the UI.

## UI (React + Vite)

A minimal React + Vite UI to interact with the FastAPI backend.

### Prerequisites
- Node.js 18+
- npm (comes with Node.js)
- Backend API (see above)

### Setup & Run Locally
1. Install dependencies:
   ```bash
   cd ui
   npm install
   ```
2. Configure environment:
   - Edit `ui/.env`:
     - Set `VITE_API_BASE_URL` to your backend URL (e.g. `http://localhost:8080`)
     - Set `VITE_API_PATH` to `/v1`
3. Start the dev server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser.

### Build for Production
```bash
npm run build
npm run preview
```

### Features & UI Changes
- Gmail-like light theme, Google blue accents, modern sidebar/chat layout
- Sidebar threads can be renamed by double-clicking; press Enter or blur to save
- Thread labels are shown in the sidebar and at the top of the chat
- Selecting a thread clears the chat window for a fresh start
- All API calls use `/v1` prefix and respect `.env` config

### Environment
- Uses `userId` and optional `threadId` headers expected by backend endpoint `POST /v1/agent/chat` with body `{ message: string }`.
- `userId` is persisted in `localStorage`. `threadId` is saved after first response.

---

### Backend API Changes (relevant to UI)
- Database migration: added `thread_label` column to `session_threads` table (auto-migrates on startup)
- All thread-related endpoints now return `thread_label` in responses
- New PATCH endpoint `/v1/agent/rename-thread-label` to rename a thread label (accepts `threadId` and `label` as query params, requires `userId` header)
- All endpoints now consistently use `/v1` path prefix
- ThreadRepository and related backend logic updated to support thread labels

See above for backend setup and full details.

## Development Workflow
- Format & import-order:
```bash
make format
```
- Lint (Ruff) + auto-fix:
```bash
make lint
```
- Type-check (mypy):
```bash
make type
```
- Security scan (Bandit):
```bash
make security
```
- Run tests (pytest):
```bash
make test
```
- Run all the above quality gates:
```bash
make all
```
- Install pre-commit hooks:
```bash
make hooks
```

## API Overview (v1)
The dispatch router aggregates domain routers under a version prefix.

- `POST /v1/agent/chat` — send a chat message to the agent graph
  - Headers: `userId: <string>` (required), `threadId: <uuid>` (optional)
  - Body: `{ "message": "Hello" }`
  - Response: `ChatMessageResponse` with `threadId`, `userId`, `message`, `response`

- `GET /v1/agent/threads` — list threads for the given user session
  - Headers: `userId: <string>` (required)
  - Response: `ok([...])` envelope of mappings `{id, session_id, thread_id, created_at}`

- `DELETE /v1/agent/threads/{threadId}` — delete a specific thread for the user session
  - Headers: `userId: <string>` (required)
  - Response: `ok({ deleted: boolean, affected: number })`

Example requests:
```bash
# Chat (new thread will be created automatically)
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'userId: user-123' \
  http://localhost:8000/v1/agent/chat \
  -d '{"message":"Hello!"}'

# List threads for a user
curl -s -H 'userId: user-123' http://localhost:8000/v1/agent/threads

# Delete a thread for a user
curl -s -X DELETE -H 'userId: user-123' \
  http://localhost:8000/v1/agent/threads/<thread-uuid>
```

### Response Format
Successful responses use `ok()` and errors return a simple array of error items.
- Success example:
```json
{
  "success": true,
  "data": { "name": "Abhishek", "email": "abhishek@abhishek.com", "age": 21 },
  "meta": null
}
```
- Error examples (via controller advice):
  - Validation (422):
  ```json
  [
    {
      "errorcode": "validation_error",
      "errormessage": "Field required",
      "errorStatus": 422,
      "errorField": "body.someField"
    }
  ]
  ```
  - App error (e.g., 400):
  ```json
  [
    {
      "errorcode": "bad_request",
      "errormessage": "One or more fields invalid",
      "errorStatus": 400,
      "errorField": "age"
    }
  ]
  ```
  - Unexpected (500):
  ```json
  [
    {
      "errorcode": "internal_error",
      "errormessage": "Internal Server Error",
      "errorStatus": 500,
      "errorField": null
    }
  ]
  ```

### Observability
- Each request/response carries an `X-Correlation-ID`. You can provide one or the server will generate it.
- Lightweight request logging includes method, path, status, duration, and correlation ID.

## LLM Provider Configuration (Ollama & Google Gemini)

The agent LLM selection and instantiation is handled by `app/agents/LLMFactory.py`, which is now optimized for clarity and error handling.

### Environment Variables

Set these in your `.env` file:

```
# --- LLM Provider Selection ---
LLM_PROVIDER=google_genai   # or 'ollama'

# --- Google Gemini Settings ---
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL_NAME=gemini-2.5-flash

# --- Ollama Settings ---
OLLAMA_MODEL_NAME=llama3.1:8b

# --- Common LLM Settings ---
LLM_TEMPERATURE=0.7
```

### Usage in Code

```python
from app.agents.LLMFactory import LLMFactory

# Create a chat model using the provider from env
llm = LLMFactory.create()

# Or specify provider/model/temperature explicitly
llm = LLMFactory.create(
    provider="ollama",  # or LLMProvider.ollama
    model="llama3.1:8b",
    temperature=0.8
)
```

- Provider/model/temperature can be omitted to use environment defaults.
- Errors are raised with clear messages if required env vars are missing or invalid.
- Logging is improved for observability.

## Agentic AI Context
This API is a backbone for an Agentic AI system:
- Users submit tasks via HTTP.
- The API routes to appropriate domain routers/services.
- Services coordinate one or more agents/tools (LLMs, retrieval, planning, function-calling, etc.) to complete the request.
- The design supports adding new agents/tools with minimal coupling by placing business logic in `app/services/` and exposing them via new routers in `app/routers/`.

Typical next steps to expand:
- Add domain-specific Pydantic request/response models in `app/models/`.
- Implement agent orchestration in `app/agents/` and call from services.
- Add configuration for providers/stores under `app/config/`.
- Write unit/integration tests for new routes/services.

## Utilities
- __Content normalization (`app/utils/text.py`)__
  - `to_plain_text(content: Any) -> str` converts various LangChain message content shapes into plain text.
  - Handles strings, lists of blocks (e.g., `{ "type": "text", "text": "..." }`), dicts with common keys, and objects exposing `.content`/`.text`.
  - Used by `AgentService.execute()` to extract the final model answer from `AIMessage` content.

Example:
```bash
python3 -c "from app.utils.text import to_plain_text; print(to_plain_text(['Hello', {'type':'text','text':'world'}]))"
```
Output:
```
Hello
world
```

## Troubleshooting
- mypy error "Source file found twice under different module names": ensure `app/` and subfolders contain `__init__.py` so packages are explicit (already included).
- If Ruff import-order warnings appear, run `make format` to auto-fix.
- If using `pipenv`, prefer running commands as `pipenv run <cmd>`.

## Database & Persistence
- Default DB path resolves to `app/db/chat.db` (created if not present). Override via `SQLITE_DB_PATH`.
- A singleton SQLite connection is used for the app lifetime (see `app/config/SqlLiteConfig.py`).
- On FastAPI shutdown, the connection is closed gracefully (`app/main.py`).

## LangGraph & Checkpointing
- The chat graph is compiled once per `LangGraphService` instance and reused for subsequent calls.
- Checkpointing uses LangGraph's `SqliteSaver` with the singleton connection for performance and stability.
- Threads are tracked via `session_threads` table. See `app/repositories/ThreadRepository.py`.

## Contributing
- Use feature branches and submit PRs.
- Keep changes formatted/linted/typed (`make all`).
- Add/adjust tests as needed.

## License
This project is licensed under the terms of the [LICENSE](LICENSE) file in this repository.
