# AgenticAI - Full-Stack AI Chat Application

A production-ready FastAPI backend with React frontend for agentic AI conversations. Features real-time streaming, multiple LLM providers, and modern architecture patterns.

## 🚀 Key Features

### Backend
- **Versioned REST API** with FastAPI architecture
- **Multiple LLM Support**: Ollama, Google Gemini, OpenAI, Anthropic, Groq, Hugging Face
- **Real-time Streaming** via Server-Sent Events (SSE)
- **SQLite Persistence** with thread management
- **Dependency Injection** with type-safe resolution
- **Security**: SecretStr API keys, input validation, error handling
- **Specialized AI Services**: Grammar correction, translation, and text summarization (optional Hugging Face support)
- **Lazy Loading**: Hugging Face dependencies only loaded when needed

### Frontend
- **Modern Chat UI** with Material-UI components
- **Real-time Streaming** responses
- **Thread Management** with auto-generated labels
- **Multi-user Support** with persistent sessions
- **Dark/Light Mode** with responsive design

## 🧠 Multi-Agent Routing & Query Decomposition (Latest Architecture)

### Overview
AgenticAI features a **plan-and-dispatch multi-agent router** for robust multi-step, multi-domain query handling. Complex user queries are decomposed into atomic sub-queries using an LLM, and each sub-query is routed to the most appropriate specialized agent (math, code, research). This enables accurate, modular, and collaborative agent workflows.

### How It Works
1. **LLM-Based Query Decomposition**
    - The router uses a dedicated LLM (configurable via provider) to split complex user queries into minimal, non-overlapping sub-questions.
    - Example: "Who is the current PM of India and write a Java code for prime number?" →
      - "Who is the current PM of India?" (→ research agent)
      - "How do I write Java code to find prime numbers?" (→ code agent)
      - "Show a Java function that checks if a number is prime." (→ code agent)

2. **Routing Plan Construction**
    - The router builds a `routing_plan`: a list of (agent, subquery) pairs (only agents: math, code, research).
    - The plan is tracked in the conversation state (`CustomState`) as `routing_plan`, `pending_routes`, and a `plan_active` flag.

3. **Plan-and-Dispatch Orchestration**
    - The router dispatches each sub-query in sequence:
        - Pops the next (agent, subquery) from the plan.
        - Appends the subquery as a new HumanMessage.
        - Sets the route for the StateGraph to invoke the correct agent.
    - After each agent responds, control returns to the router to dispatch the next subquery, until the plan is exhausted.
    - If an agent invokes tools, the graph will route to the tools node and then back to the same agent, until the agent completes.

4. **Final Formatting**
    - When all sub-queries are processed, the router routes to the `nlp_formatting` node.
    - The formatting agent robustly handles agent outputs (including lists) and produces a clean, user-facing answer.

### State Fields Used
- `route`: Current agent to invoke (math, code, research, nlp_formatting)
- `routing_plan`: List of (agent, subquery) pairs
- `pending_routes`: List of remaining agent types to invoke
- `plan_active`: True if a plan is being executed
- `messages`: Conversation history (with reducers for streaming)
- `summary`: Conversation summary (with safe reducer)

### StateGraph Flow Example
```
User Query → router
  ├─> router splits query with LLM → builds routing_plan
  ├─> router dispatches subquery #1 → research
  │     └─> research result → router
  ├─> router dispatches subquery #2 → code
  │     └─> code result → router
  ├─> router dispatches subquery #3 → code
  │     └─> code result → router
  └─> routing_plan exhausted → router sets route to nlp_formatting
        └─> nlp_formatting produces final answer
```

### Implementation Notes
- **No Simulation AIMessage:** The router does not emit concatenated simulation strings. Each subquery is dispatched as a true message for agent execution.
- **Agents route back to router:** After each agent completes (unless tools are invoked), the StateGraph returns to the router for the next dispatch.
- **Formatting agent is robust:** Handles AIMessage.content as string, list, or dict.
- **No direct agent → nlp_formatting edges:** Final formatting only occurs after all plan steps are complete.
- **No supervisor agent:** All orchestration is handled by the router and StateGraph.
- **No Spring MVC:** Backend is FastAPI-based.
- **No "web" agent node:** While `should_route_to_web` exists, there is no explicit web agent node in the StateGraph.

### Example State (Partial)
```python
{
    'route': 'code',
    'routing_plan': [('code', 'How do I write Java code to find prime numbers?'), ...],
    'plan_active': True,
    'messages': [HumanMessage(...), AIMessage(...), ...],
    ...
}
```

## 🏗️ Architecture

### System Overview
```
Frontend (React) ↔️ HTTP/SSE ↔️ FastAPI Backend ↔️ LLM Providers
                                          │
                                     SQLite DB
```

### Key Components
- **Services**: Business logic with dependency injection
- **Repositories**: Data access layer (SQLite)
- **Agents**: LLM provider abstractions (factory pattern)
- **Routers**: REST API endpoints (`/v1/user/*`, `/v1/agent/*`)
- **Specialized AI Services**: MT5Service for grammar correction and translation

### Project Structure
```
app/
├── agents/          # LLM provider factory
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

```
# Direct resolution when needed
reframer = inject(ReframeChat)
corrected_text = reframer.correct("bad grammer text")
```

#### Benefits of DI Implementation
- **Testability**: Easy to mock dependencies in unit tests
- **Flexibility**: Swap implementations without changing client code
- **Separation of Concerns**: Clear boundaries between components
- **Configuration**: Centralized dependency configuration
- **Maintainability**: Loose coupling makes refactoring easier

### Frontend Structure
```
ui/src/
  ├── components/               # React components
  │   ├── chat/                 # Chat-related components
  │   │   ├── ChatArea.jsx      # Main chat display area
  │   │   ├── ChatInput.jsx     # Message input with streaming
  │   │   ├── MessageBubble.jsx # Individual message display
  │   │   └── index.js          # Component exports
  │   ├── sidebar/              # Sidebar navigation
  │   │   ├── Sidebar.jsx       # Main sidebar container
  │   │   ├── ThreadItem.jsx    # Individual thread item
  │   │   ├── ThreadList.jsx    # Thread list with management
  │   │   └── index.js          # Component exports
  │   ├── layout/               # Layout components
  │   │   ├── TopBar.jsx        # Top navigation bar
  │   │   ├── Footer.jsx        # Footer component
  │   │   └── index.js          # Component exports
  │   └── ui/                   # Reusable UI components
  │       ├── UserSelector.jsx  # User dropdown with search
  │       ├── ThemeToggle.jsx   # Dark/light mode toggle
  │       ├── ErrorBoundary.jsx # Error boundary wrapper
  │       └── index.js          # Component exports
  ├── hooks/                    # Custom React hooks
  │   ├── useChat.js            # Chat state management
  │   ├── useThreads.js         # Thread management
  │   └── index.js              # Hook exports
  ├── api/                      # API integration
  │   ├── config.js             # API configuration
  │   ├── controller.js         # API methods
  │   ├── endpoints.js          # Endpoint definitions
  │   └── http.js               # HTTP client
  ├── utils/                    # Utility functions
  │   ├── threadUtils.js        # Thread-related utilities
  │   └── index.js              # Utility exports
  ├── contexts/                 # React contexts
  │   └── ThemeContext.jsx      # Theme state management
  ├── theme/                    # Theme configuration
  │   └── theme.js              # Material-UI theme
  ├── App.jsx                   # Main application component
  └── main.jsx                  # Application entry point
```

## 📦 Dependencies & Installation

### Core Dependencies
The application uses a **lean dependency approach** with the following core requirements:

**Essential Runtime:**
- `fastapi` - High-performance web framework
- `uvicorn[standard]` - ASGI server
- `pydantic` & `pydantic-settings` - Data validation and settings
- `python-dotenv` - Environment variable management

**AI/LLM Framework:**
- `langgraph` - Agent workflow orchestration
- `langchain-core` - Core LangChain functionality
- `langchain-ollama` - Ollama LLM integration
- `langchain-google-genai` - Google Gemini integration

**Database:**
- SQLite (built-in Python) - No additional dependencies required

### Optional Dependencies
The application supports optional dependencies for extended functionality:

```
# Optional LLM Providers (install only what you need)
openai              # OpenAI GPT models
anthropic          # Anthropic Claude models
groq               # Groq API
litellm            # Multi-provider LLM interface

# Optional Vector Databases (pick one if needed)
chromadb           # Chroma vector database
qdrant-client      # Qdrant vector database

# Optional Hugging Face Support (for grammar correction, translation, summarization)
# Install separately with: pip install -r requirements.txt
# - transformers
# - torch
# - langchain-huggingface
# - sentence-transformers
# - tiktoken

# Optional Features
redis              # Caching/session storage
sse-starlette      # Server-sent events
python-multipart   # File upload support
orjson             # Fast JSON serialization
```

### Dependency Optimization
> **💡 Optimization Tip**: The application includes all necessary dependencies in a single requirements.txt file. For a minimal installation, simply install only the dependencies you need.

### Development Dependencies
```bash
# Code Quality & Testing
ruff               # Fast Python linter
black              # Code formatter
isort              # Import organizer
mypy               # Type checker
bandit             # Security scanner
pytest             # Testing framework
pre-commit         # Git hooks
```

### Installation Methods

#### Method 1: Full Installation
```bash
pip install -r requirements.txt
```

#### Method 2: Pipenv (Recommended)
```bash
pipenv install --dev
```

#### Method 3: Make Command (Auto-detection)
```bash
make install  # Detects pipenv/pip automatically
```



## 🚀 Quick Start

### Prerequisites

**Required:**
- Python 3.11+
- Node.js 18+
- npm

**LLM Provider (choose one):**
- **Ollama (Local)**: Install Ollama and pull a model like `llama3.1:8b`
- **Google Gemini**: Get an API key from Google AI Studio
- **OpenAI**: Get an API key from OpenAI
- **Anthropic**: Get an API key from Anthropic
- **Groq**: Get an API key from Groq

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AgenticAI
   ```

2. **Set up Python environment**:
   ```bash
   # Using pipenv (recommended)
   pipenv install --dev
   pipenv shell
   
   # Or using pip with virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   # Install all dependencies:
   pip install -r requirements.txt
   ```

3. **Set up frontend dependencies**:
   ```bash
   cd ui
   npm install
   cd ..
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

5. **Run the application**:
   
   **Option 1: Run both services in separate terminals**
   ```bash
   # Terminal 1: Start the backend
   python -m app.main
   
   # Terminal 2: Start the frontend development server
   cd ui
   npm run dev
   ```
   
   **Option 2: Run backend only**
   ```bash
   python -m app.main
   ```
   
   **Option 3: Run frontend only (connects to backend on localhost:8000)**
   ```bash
   cd ui
   npm run dev
   ```

6. **Access the application**:
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

### 2. Environment Configuration

Create `.env` file:

``env
# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# === LLM Provider Selection ===
# === Small / Fast models (cheap, quick tasks like correction, summarization, classification) ===
LLM_SMALL_MODEL=llama3.1:8b
# === Medium models (good balance, reasoning, multi-lingual tasks like Hinglish correction) ===
LLM_MEDIUM_MODEL=llama3.1:8b
# === Large models (deep reasoning, content generation, complex workflows) ===
LLM_LARGE_MODEL=llama3.1:8b

# === Task Specific Models ===
# Grammar correction (Hugging Face)
LLM_CORRECTION_MODEL=vennify/t5-base-grammar-correction
# Translation (Hugging Face)
LLM_TRANSLATION_MODEL=llama3.1:8b
# Other specialized tasks
LLM_REASONING_MODEL=llama3.1:8b
LLM_SUMMARIZATION_MODEL=llama3.1:8b

# --- Google Gemini Settings ---
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL_NAME=gemini-2.5-flash

# --- Ollama Settings ---
OLLAMA_MODEL_NAME=llama3.1:8b

# --- Common LLM Settings ---
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# --- Hugging Face Settings (for specialized models) ---
# Required for grammar correction and translation models
```

### 3. Run Application

#### Option 1: Manual Setup
```bash
# Start backend (choose one method)
make run              # Recommended
# OR
python -m app.main    # Direct

# Start frontend (in new terminal)
cd ui
npm run dev
```

#### Option 2: Docker Setup
```bash
# Build and run with Docker Compose (separate containers)
docker-compose up --build

# For a simpler setup without Ollama
docker-compose -f docker-compose.simple.yml up --build

# Build and run with single container (backend + frontend)
docker build -t agenticai .
docker run -p 8000:8000 --env-file .env agenticai
```

### 4. Access Application

- **Frontend**: http://localhost:5173 (development) or http://localhost:8000 (Docker)
- **API Docs**: http://localhost:8000/docs



## 🔧 Development Commands

### Code Quality & Formatting
```bash
# Format code and fix import order
make format

# Lint with Ruff and auto-fix issues
make lint

# Type check with mypy
make type

# Security scan with Bandit
make security

# Run tests with pytest
make test

# Run all quality gates
make all

# Install pre-commit hooks
make hooks

# Run health check
python scripts/health-check.py
```

### Project Management
```bash
# Install dependencies (auto-detects pipenv/pip)
make install

# Run application in production mode
make run

# Run application in development mode (with reload)
make dev

# Build and run with Docker
make docker

# Build and run with simplified Docker setup
make docker-simple
```

## 📚 API Documentation Reference

### Complete Endpoint Documentation

#### Authentication
All API endpoints require the `user-id` header for authentication and session management.

```bash
curl -H "user-id: your-session-id" http://localhost:8080/v1/endpoint
```

#### Response Format
All API responses follow a consistent envelope format:

**Success Response:**
```json
{
  "success": true,
  "data": <response_data>,
  "meta": <optional_metadata>
}
```

**Error Response:**
```json
[
  {
    "errorcode": "ERROR_CODE",
    "errormessage": "Human readable message",
    "errorStatus": 400,
    "errorField": "field_name"
  }
]
```

### Agent Endpoints (`/v1/agent/*`)

#### POST /v1/agent/chat
**Purpose**: Send a chat message to AI agent with streaming response

**Headers:**
- `user-id` (required): User session identifier
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message": "Your chat message here",
  "thread_id": "optional-uuid-for-existing-thread",
  "thread_label": "Display label for the thread"
}
```

**Response Type**: Server-Sent Events (SSE) stream

**SSE Event Format:**
```
data: {"threadId": "uuid", "userId": "user123"}
data: {"type": "token", "content": "Hello"}
data: {"type": "token", "content": " world"}
data: [DONE]
```

**Example Usage:**
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'user-id: user123' \
  http://localhost:8080/v1/agent/chat \
  -d '{
    "message": "Hello, how can you help me?",
    "thread_id": null,
    "thread_label": "My First Chat"
  }' \
  --no-buffer
```

### User Management Endpoints (`/v1/user/*`)

#### GET /v1/user/get-all
**Purpose**: Retrieve all user IDs in the system

**Headers:**
- `user-id` (required): Admin user identifier

**Response:**
```json
{
  "success": true,
  "data": ["user123", "user456", "admin"],
  "meta": null
}
```

#### GET /v1/user/threads
**Purpose**: List all threads for the authenticated user

**Headers:**
- `user-id` (required): User session identifier

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "record-uuid",
      "session_id": "user123",
      "thread_id": "thread-uuid",
      "thread_label": "My Chat",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "meta": null
}
```

#### GET /v1/user/thread/{thread_id}
**Purpose**: Get detailed information about a specific thread

**Path Parameters:**
- `thread_id` (UUID): Thread identifier

**Headers:**
- `user-id` (required): User session identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "record-uuid",
    "session_id": "user123",
    "thread_id": "thread-uuid",
    "thread_label": "My Chat",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "meta": null
}
```

## 📡 API Reference

### Authentication
All requests require `user-id` header:
```bash
curl -H "user-id: your-user-id" ...
```

### Key Endpoints

#### POST /v1/agent/chat
Send chat message with streaming response.

**Request:**
```json
{
  "message": "Hello!",
  "thread_id": "optional-uuid",
  "thread_label": "My Chat"
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"type": "token", "content": "Hello"}
data: [DONE]
```

#### GET /v1/user/threads
List user's conversation threads.

#### DELETE /v1/user/threads/{thread_id}
Delete a specific thread.

#### PATCH /v1/user/rename-thread-label?threadId={id}&label={name}
Rename thread label.

### Interactive Documentation
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🎨 Frontend Features

### Chat Interface
- **Real-time streaming** responses with Server-Sent Events
- **Message history** with user/assistant distinction
- **Thread-based conversations** with automatic labeling
- **Responsive design** for desktop and mobile

### Thread Management
- **Sidebar navigation** with thread list
- **Thread labeling** with automatic generation from first message
- **Thread renaming** via inline editing
- **Thread deletion** with confirmation
- **Thread search and filtering**

## 🔧 Development

### Code Quality Commands

#### Documentation Standards

**Python Documentation**
All Python code follows comprehensive docstring standards:
- **Google-style docstrings** for consistency
- **Type hints** for all function parameters and returns
- **Usage examples** in docstrings where helpful
- **Error documentation** for exceptions that may be raised

**Code Documentation Philosophy**
- **Self-documenting code**: Clear variable and function names
- **Comprehensive docstrings**: Every public function and class documented
- **Inline comments**: Complex logic explained with comments
- **Architecture documentation**: High-level system design explained

#### Quality Tools

```bash
# Format code and fix import order
make format

# Lint with Ruff and auto-fix issues
make lint

# Type check with mypy
make type

# Security scan with Bandit
make security

# Run tests with pytest
make test

# Run all quality gates
make all

# Install pre-commit hooks
make hooks

# Run health check
python scripts/health-check.py
```

### Common Issues

**LLM Provider Issues:**
- Ensure Ollama is running: `ollama serve`
- Check API keys are set correctly
- Verify model names match your provider

**CORS Issues:**
- Set `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173` in `.env`

**Database Issues:**
- Database auto-creates on first run
- Check SQLite file permissions if needed

## 📄 Key Features & Architecture

- **Spring MVC Pattern**: Interface-implementation separation with dependency injection
- **Multiple LLM Support**: Ollama (local), Google Gemini, OpenAI, Anthropic, Groq, Hugging Face
- **Real-time Streaming**: Token-by-token responses via Server-Sent Events
- **Security**: SecretStr API keys, input validation, error sanitization
- **Thread Management**: Auto-generated labels, persistent conversations
- **Modern UI**: Material-UI with dark/light themes and responsive design
- **Specialized AI Services**: Grammar correction and translation using Hugging Face models

## 🎯 Summary

**AgenticAI** demonstrates modern full-stack development with:
- **Clean Architecture**: SOLID principles with dependency injection
- **Production Ready**: Error handling, logging, security best practices
- **Developer Friendly**: Quality gates, documentation, easy setup
- **Extensible**: Easy to add new LLM providers and features

**Get started:** `git clone → make install → make run → open http://localhost:8080/docs`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow code quality standards (`make all`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

*Built with ❤️ for developers who value clean code and modern architecture.*

### Python Docstring Standards

All Python modules, classes, and functions in this project follow comprehensive docstring standards:

#### Module-Level Documentation
- **Purpose and Scope**: Clear description of module functionality
- **Key Features**: List of main capabilities provided
- **Integration Points**: How the module fits into the larger system
- **Dependencies**: Important external dependencies

#### Class Documentation
- **Purpose**: What the class represents or manages
- **Key Methods**: Overview of primary public methods
- **Usage Examples**: Basic usage patterns
- **CustomState Management**: How the class manages internal state

#### Function Documentation
- **Purpose**: Clear description of what the function does
- **Parameters**: Type hints and detailed parameter descriptions
- **Returns**: Return type and description of returned values
- **Examples**: Code examples showing typical usage
- **Error Handling**: Exceptions that may be raised
- **Side Effects**: Any state changes or external effects

#### Example Documentation Structure

```
def stream_chat_tokens(
    user_id: str,
    thread_id: UUID | None,
    message: str,
    thread_label: str
) -> AsyncGenerator[str, None]:
    """Stream AI agent response tokens for real-time chat experience.
    
    Provides a streaming interface for AI agent responses, enabling real-time
    chat experiences in the frontend. Coordinates with the LangGraph service
    to execute the AI agent and stream response tokens.
    
    Args:
        user_id (str): Unique identifier for the user/session
        thread_id (UUID, optional): Existing thread ID to continue conversation
        message (str): The user's chat message to send to the AI agent
        thread_label (str): Label for the thread (mandatory for new threads)
        
    Yields:
        str: Server-Sent Events (SSE) formatted strings containing response tokens
        
    Example:
        >>> async for token in AgentService.stream_chat_tokens(
        ...     user_id="user123",
        ...     thread_id=None,
        ...     message="Hello, how are you?",
        ...     thread_label="My First Chat"
        ... ):
        ...     print(token)  # SSE-formatted response tokens
    """
```

### Documentation Coverage

The following modules have comprehensive documentation:

#### Core Modules (`app/core/`)
- **`enums.py`**: API versioning, error codes, LLM providers
- **`errors.py`**: Structured error handling and API error responses
- **`middleware.py`**: Request correlation and logging middleware
- **`response.py`**: Standardized API response helpers
- **`exception_handlers.py`**: Global exception handling patterns

#### Configuration (`app/config/`)
- **`SqlLiteConfig.py`**: Database connection management and schema migration

#### Utilities (`app/utils/`)
- **`text.py`**: Content extraction and text processing utilities
- **`reframe_chat.py`**: **AI-powered text correction service with dependency injection support**
  - **Text Correction**: Grammar, spelling, and clarity improvements using LLM
  - **Dependency Injection**: Follows DIP principles with automatic LLM provider injection
  - **Minimal & Clean**: Simplified implementation focusing on core functionality
  - **Tool-Free LLM**: Uses LLM instances without tools to prevent interference
  - **Error Handling**: Comprehensive error handling with custom exceptions
  - **Usage Example**:
    ```python
    from app.core.di_container import inject
    from app.utils.reframe_chat import ReframeChat
    
    # Using dependency injection (recommended)
    reframer = inject(ReframeChat)
    
    # Basic text correction
    corrected = reframer.correct("i need halp with my cod")
    # Returns: "I need help with my code"
    
    # Fix grammar and spelling
    fixed = reframer.correct("this funktoin dosnt work proprly")
    # Returns: "This function doesn't work properly"
    ```
- **`mt5_service.py`**: **Specialized grammar correction and translation service**
  - **Grammar Correction**: Uses vennify/t5-base-grammar-correction model for accurate grammar fixes
  - **Translation**: Supports multilingual translation with mT5 models
  - **Text Summarization**: Provides text summarization capabilities
  - **Model Flexibility**: Configurable LLM models via environment variables
  - **Fallback Handling**: Graceful degradation when correction models don't improve text
  - **Dependency Injection**: Seamlessly integrated with the DI container
  - **Tool-Free LLM**: Uses LLM instances without tools for optimal text processing
  - **Usage Example**:
    ```python
    from app.core.di_container import inject
    from app.utils.mt5_service import MT5Service
    
    # Using dependency injection
    grammar_service = inject(MT5Service)
    
    # Grammar correction
    corrected = grammar_service.correct_grammar("this sentence have grammer errors")
    # Returns: "this sentence has grammar errors."
    
    # Translation
    translated = grammar_service.translate("Hello world", "Spanish")
    # Returns: "Hola mundo"
    
    # Summarization
    summary = grammar_service.summarize("Long text to summarize...", max_length=100)
    ```

#### Service Layer (`app/services/`)
- **`agent_service_interface.py`**: Agent service contracts (AgentServiceInterface, AgentExecutionInterface, ConversationStateInterface)
- **`user_service_interface.py`**: User management service contracts
- **`impl/agent_service_impl.py`**: High-level agent interaction coordination
- **`impl/langgraph_service_impl.py`**: LangGraph workflow orchestration
- **`impl/user_service_impl.py`**: User management business logic

#### Repository Layer (`app/repositories/`)
- **`thread_repository_interface.py`**: Thread and session data access contracts
- **`database_interface.py`**: Database connection provider contracts
- **`impl/thread_repository_impl.py`**: Thread and session data access implementation

#### Agents Layer (`app/agents/`)
- **`llm_provider_interface.py`**: LLM provider abstraction contracts
- **`impl/llm_factory_impl.py`**: Factory implementation for multiple LLM providers with tool management
  - **Tool Management**: Enhanced with `with_tools` parameter to create LLM instances with or without tools
  - **Hugging Face Support**: Added support for Hugging Face models like grammar correction and translation models
  - **Multiple Provider Support**: Ollama, Google Gemini, OpenAI, Anthropic, Groq, Hugging Face

#### API Layer (`app/routers/`)
- **`AgenticRouter.py`**: AI agent and chat endpoints
- **`UserRouter.py`**: User and thread management endpoints

#### Schema Definitions (`app/schemas/`)
- **`ChatRequest.py`**: Chat request validation models
- **`chat.py`**: Additional chat-related data models

### Accessing Documentation

#### Interactive API Documentation
- **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc)

#### Code Documentation
```
# View module documentation
python -c "import app.services; help(app.services)"

# View specific interface documentation
python -c "from app.services import AgentServiceInterface; help(AgentServiceInterface)"

# View implementation documentation
python -c "from app.services.impl.langgraph_service_impl import LangGraphServiceImpl; help(LangGraphServiceImpl)"
```

### Import Structure Changes

#### New Simplified Import Pattern (Post Spring MVC Reorganization)

With the Spring MVC structure, imports are significantly cleaner:

**Before (Old Structure):**

```
# Old complex import paths
from app.services.interfaces.agent_service_interface import AgentServiceInterface
from app.repositories.interfaces.thread_repository_interface import ThreadRepositoryInterface
from app.ai_core.interfaces.llm_provider_interface import LLMFactoryInterface
```

**After (Spring MVC Structure):**

```
# New clean import paths
from app.services import AgentServiceInterface, UserServiceInterface
from app.repositories import ThreadRepositoryInterface, DatabaseConnectionProvider
from app.ai_core import LLMFactoryInterface
```

**Package [__init__.py](file:///Users/abhishek/Desktop/Coding/AgenticAI/app/__init__.py) Files:**
Each main package re-exports its interfaces for clean imports:

```python
# app/services/__init__.py
from .agent_service_interface import (
    AgentServiceInterface,
    AgentExecutionInterface,
    ConversationStateInterface,
)
from .user_service_interface import UserServiceInterface

__all__ = [
    "AgentServiceInterface",
    "AgentExecutionInterface", 
    "ConversationStateInterface",
    "UserServiceInterface",
]
```

**Benefits of New Import Structure:**
- **Cleaner Code**: Shorter, more readable import statements
- **Spring MVC Compliance**: Follows Java/Spring naming conventions
- **Better IDE Support**: Autocomplete works better with main package imports
- **Easier Refactoring**: Changes to implementations don't affect import statements
- **Consistent Pattern**: All interfaces imported from main packages

#### IDE Integration
Most modern IDEs will automatically display docstrings when hovering over functions or classes:
- **VS Code**: Hover tooltips and Go to Definition
- **PyCharm**: Quick Documentation (Ctrl+Q)
- **Vim/Neovim**: LSP hover information



### Code Quality Commands

#### Documentation Standards

```
# Format code and fix import order
make format

# Lint with Ruff and auto-fix issues
make lint

# Type check with mypy
make type

# Security scan with Bandit
make security

# Run tests with pytest
make test

# Run all quality gates
make all

# Install pre-commit hooks
make hooks

# Run health check
python scripts/health-check.py
```





### Code Quality Commands

#### Documentation Standards

**Python Documentation**
All Python code follows comprehensive docstring standards:
- **Google-style docstrings** for consistency
- **Type hints** for all function parameters and returns
- **Usage examples** in docstrings where helpful
- **Error documentation** for exceptions that may be raised

**Code Documentation Philosophy**
- **Self-documenting code**: Clear variable and function names
- **Comprehensive docstrings**: Every public function and class documented
- **Inline comments**: Complex logic explained with comments
- **Architecture documentation**: High-level system design explained

#### Quality Tools

```bash
# Format code and fix import order
make format

# Lint with Ruff and auto-fix issues
make lint

# Type check with mypy
make type

# Security scan with Bandit
make security

# Run tests with pytest
make test

# Run all quality gates
make all

# Install pre-commit hooks
make hooks
```

### Development Guidelines

1. **Backend Development:**
   - Follow Python PEP 8 style guidelines
   - Use type hints for all functions
   - Add docstrings for all public functions
   - Write unit tests for new features

2. **Frontend Development:**
   - Use ESLint and Prettier for code formatting
   - Follow React best practices
   - Use TypeScript for type safety
   - Implement proper error boundaries

3. **API Development:**
   - Use Pydantic models for request/response validation
   - Implement proper error handling
   - Add OpenAPI documentation
   - Version all API endpoints

## 🗄️ Database Schema

### SQLite Tables

#### session_threads
```sql
CREATE TABLE session_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    thread_id TEXT NOT NULL UNIQUE,
    thread_label TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

### Environment Variables

#### Server Configuration
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8080)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

#### Database Configuration
- `SQLITE_DB_PATH`: Path to SQLite database file

#### LLM Configuration
- `LLM_PROVIDER`: Provider name ('ollama' or 'google_genai')
- `LLM_TEMPERATURE`: Response temperature (0.0-1.0)

#### Provider-Specific Settings
- `OLLAMA_MODEL_NAME`: Ollama model name
- `GOOGLE_API_KEY`: Google AI API key
- `GEMINI_MODEL_NAME`: Gemini model name

## 🚑 Quick Troubleshooting

### Common Setup Issues

#### LLM Provider Issues
```bash
# Ollama not responding
curl http://localhost:11434/api/tags
ollama serve  # if not running
ollama pull llama3.1  # if model missing

# Google Gemini API issues
echo $GOOGLE_API_KEY  # verify key is set
```

#### Dependency Problems
```bash
# Clean install
make clean && make install

# Manual reinstall
pip install -r requirements.txt --force-reinstall
```

#### Frontend-Backend Connection
```bash
# Check CORS settings in .env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Verify ports are free
lsof -i :8080  # Backend
lsof -i :5173  # Frontend
```

#### Database Permissions
```bash
# Create db directory
mkdir -p app/db

# Check permissions
ls -la app/db/
```

## 🚀 Deployment

### Production Build

#### Backend
```bash
# Direct deployment
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd ui
npm run build
npm run preview
```

### Production Considerations

1. **Security:**
   - Use HTTPS in production
   - Set proper CORS origins
   - Validate all input data
   - Use environment variables for secrets

2. **Performance:**
   - Enable database connection pooling
   - Implement caching strategies
   - Use CDN for static assets
   - Monitor API response times

3. **Monitoring:**
   - Set up application logging
   - Implement health checks
   - Monitor resource usage
   - Track error rates

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_agents.py
```

### Frontend Testing
```bash
cd ui
npm test
```

### Docker Testing
```bash
# Test Docker build process
./scripts/test-docker.sh
```

### Health Check
```bash
# Run application health check
python scripts/health-check.py
```

## 🛠️ Comprehensive Troubleshooting

### Development Environment Issues

#### Python Environment Problems

**Issue**: `ModuleNotFoundError` when running the application
```bash
ModuleNotFoundError: No module named 'app'
```

**Solutions**:
1. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate  # or `pipenv shell`
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run from correct directory**:
   ```bash
   cd /path/to/AgenticAI
   python -m app.main
   ```

#### Database Connection Issues

**Issue**: `sqlite3.OperationalError: unable to open database file`

**Solutions**:
1. **Check database path permissions**:
   ```bash
   ls -la app/db/
   chmod 755 app/db/
   chmod 644 app/db/chat.db
   ```

2. **Create database directory**:
   ```bash
   mkdir -p app/db
   ```

3. **Verify environment variable**:
   ```bash
   echo $SQLITE_DB_PATH
   # Should point to writable location
   ```

#### LLM Provider Configuration

**Issue**: `Expected type 'SecretStr | None', got 'str' instead`

**Solutions**:
1. **Upgrade to latest version**: Recent updates fixed SecretStr compatibility
   ```bash
   git pull origin main
   pip install --upgrade -r requirements.txt
   ```

2. **Verify LangChain versions**:
   ```bash
   pip list | grep langchain
   # Ensure compatible versions are installed
   ```

**Issue**: `RuntimeError: LLM_PROVIDER is not set`

**Solutions**:
1. **Set environment variables**:
   ```bash
   export LLM_PROVIDER=ollama  # or google_genai, openai, anthropic, groq, huggingface
   export OLLAMA_MODEL_NAME=llama3.1:8b
   ```

2. **Check .env file**:
   ```bash
   cat .env | grep LLM_PROVIDER
   ```

3. **Verify Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

**Issue**: `Hugging Face model loading errors`

**Solutions**:
1. **Ensure required dependencies are installed**:
   ```bash
   pip install langchain-huggingface transformers
   ```

2. **Set Hugging Face model names in .env**:
   ```bash
   # For grammar correction
   LLM_CORRECTION_MODEL=vennify/t5-base-grammar-correction
   
   # For translation
   LLM_TRANSLATION_MODEL=google/mt5-small
   ```

3. **Verify model availability**:
   ```python
   from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
   tokenizer = AutoTokenizer.from_pretrained("vennify/t5-base-grammar-correction")
   model = AutoModelForSeq2SeqLM.from_pretrained("vennify/t5-base-grammar-correction")
   ```

**Issue**: `Arguments missing for parameters "timeout", "stop"`

**Solutions**:
1. **Update code**: Recent fixes added required ChatAnthropic parameters
   ```bash
   # Fixed in latest version
   return ChatAnthropic(
       model_name=model_name,
       api_key=SecretStr(api_key),
       temperature=temp,
       timeout=60,
       stop=None
   )
   ```

**Issue**: `Google API key not configured`

**Solutions**:
1. **Set Google API key**:
   ```bash
   export GOOGLE_API_KEY=your-api-key-here
   ```

2. **Verify key is valid**:
   ```bash
   curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
        https://generativelanguage.googleapis.com/v1/models
   ```

### API and Network Issues

#### CORS Configuration

**Issue**: `CORS error` in browser console

**Solutions**:
1. **Check CORS origins**:
   ```bash
   echo $CORS_ORIGINS
   # Should include your frontend URL
   ```

2. **Update .env file**:
   ```env
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

3. **Restart backend server** after CORS changes

#### Header Naming Issues

**Issue**: `422 Validation Error` for user-id header

**Solutions**:
1. **Use kebab-case headers**:
   ```bash
   curl -H "user-id: user123"  # Correct
   curl -H "user_id: user123"  # Incorrect
   ```

2. **Check FastAPI header conversion**:
   - FastAPI converts snake_case to kebab-case automatically
   - Use `user-id` in requests, `user_id` in Python code

#### Thread Management Issues

**Issue**: `Thread not found` errors

**Solutions**:
1. **Verify thread exists**:
   ```bash
   curl -H "user-id: user123" \
        http://localhost:8080/v1/user/threads
   ```

2. **Check thread ID format**:
   ```bash
   # Ensure valid UUID format
   python -c "import uuid; print(uuid.UUID('your-thread-id'))"
   ```

3. **Database consistency check**:
   ```sql
   SELECT * FROM session_threads WHERE session_id = 'user123';
   ```

### Frontend Integration Issues

#### Server-Sent Events (SSE)

**Issue**: SSE connection drops or doesn't work

**Solutions**:
1. **Check network connectivity**:
   ```javascript
   fetch('http://localhost:8080/v1/agent/chat', {
     method: 'POST',
     headers: {
       'user-id': 'test',
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       message: 'test',
       thread_label: 'test'
     })
   }).then(response => console.log(response.status))
   ```

2. **Verify SSE headers**:
   ```bash
   curl -N -H "user-id: user123" \
        -H "Content-Type: application/json" \
        -d '{"message":"test","thread_label":"test"}' \
        http://localhost:8080/v1/agent/chat
   ```

3. **Browser debugging**:
   ```javascript
   // Check EventSource connection
   const eventSource = new EventSource('/api/stream');
   eventSource.onopen = () => console.log('SSE connected');
   eventSource.onerror = (error) => console.error('SSE error:', error);
   ```

**Issue**: Unhandled events like `{"type": "user", "messages": "..."}`

**Solutions**:
1. **Update to latest version**: Recent fixes added proper event handling
   ```bash
   git pull origin main
   cd ui && npm install
   ```

2. **Verify event handler**:
   ```javascript
   // Fixed in useChat.js
   if (obj?.type === 'user') {
     console.log('User message event received:', obj.messages || obj.content);
   } else {
     console.log('Unknown event type received:', obj);
   }
   ```

#### React Component Issues

**Issue**: UserSelector dropdown not working

**Solutions**:
1. **Check Material-UI Autocomplete props**:
   ```jsx
   <Autocomplete
     options={options}
     value={selectedOption}
     onChange={handleChange}
     onInputChange={handleInputChange}
     // Don't set inputValue manually for search to work
   />
   ```

2. **Verify search functionality**:
   ```jsx
   const handleInputChange = (event, newInputValue) => {
     // Let Autocomplete manage its own input for search
     console.log('Search query:', newInputValue);
   };
   ```

### Performance and Monitoring

#### Logging and Debugging

**Enable debug logging**:
```python
# In your .env file
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Monitor request correlation**:
```bash
# Check correlation IDs in logs
tail -f app.log | grep "cid="
```

**Database query performance**:
```python
# Enable SQLite query logging
import sqlite3
sqlite3.enable_callback_tracebacks(True)
```

#### Memory and Resource Usage

**Monitor Python memory usage**:
```bash
# Using ps
ps aux | grep python

# Using htop
htop -p $(pgrep -f "python.*app.main")
```

**Check database size**:
```bash
du -h app/db/chat.db
sqlite3 app/db/chat.db "PRAGMA database_list;"
```

**Monitor file descriptors**:
```bash
lsof -p $(pgrep -f "python.*app.main")
```

### Type Checking and Code Quality

#### mypy Issues

**Issue**: `Source file found twice under different module names`

**Solutions**:
1. **Add `__init__.py` files**:
   ```bash
   find app/ -type d -exec touch {}/__init__.py ;
   ```

2. **Check mypy configuration**:
   ```ini
   # pyproject.toml
   [tool.mypy]
   python_version = "3.11"
   strict = true
   exclude = ["build", "dist"]
   ```

#### Import and Module Issues

**Issue**: Module import errors after Spring MVC reorganization

**Solutions**:
1. **Use new import structure**:
   ```python
   # New correct imports
   from app.services import AgentServiceInterface
   from app.repositories import ThreadRepositoryInterface
   from app.ai_core import LLMFactoryInterface
   
   # Avoid old import paths
   # from app.services.interfaces.agent_service_interface import AgentServiceInterface  # OLD
   ```

2. **Check [__init__.py](file:///Users/abhishek/Desktop/Coding/AgenticAI/app/__init__.py) files exist**:
   ```bash
   find app/ -name "__init__.py" | head -10
   # Should show __init__.py files in all packages
   ```

**Issue**: Circular import errors

**Solutions**:
1. **Use `from __future__ import annotations`**
2. **Move imports inside functions if needed**
3. **Restructure module dependencies**

**Issue**: Type hint errors with LangChain

**Solutions**:
1. **Use `cast()` for complex types**:
   ```python
   from typing import cast
   config = cast(RunnableConfig, {"configurable": {...}})
   ```

2. **Use `getattr()` for dynamic attributes**:
   ```python
   content = getattr(chunk, "content", None)
   ```

### LangGraph and AI Model Issues

#### LangGraph Checkpointing

**Issue**: Conversation history not persisting

**Solutions**:
1. **Verify SQLite checkpointer**:
   ```python
   from langgraph.checkpoint.sqlite import SqliteSaver
   memory = SqliteSaver(get_sql_lite_instance())
   print(memory.list())  # Should show checkpoints
   ```

2. **Check thread configuration**:
   ```python
   config = {"configurable": {"thread_id": "uuid", "session_id": "user"}}
   state = graph.get_state(config)
   print(state.values)  # Should show conversation
   ```

#### Model Response Issues

**Issue**: Empty or malformed responses from LLM

**Solutions**:
1. **Test LLM directly**:
   ```python
   from app.ai_core.LLMFactory import LLMFactory
   llm = LLMFactory.create()
   response = llm.invoke("Hello")
   print(response.content)
   ```

2. **Check model availability**:
   ```bash
   # For Ollama
   ollama list
   ollama show llama3.1:8b
   
   # For Google Gemini
   curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
        https://generativelanguage.googleapis.com/v1/models
   ```

3. **Verify streaming configuration**:
   ```python
   # Check if model supports streaming
   for chunk in llm.stream("Hello"):
       print(chunk.content, end="", flush=True)
   ```

### Getting Help

#### Diagnostic Commands

**System Information**:
```bash
# Python environment
python --version
pip list | grep -E "(fastapi|langchain|langgraph)"

# System resources
df -h  # Disk space
free -h  # Memory
netstat -tlnp | grep :8080  # Port usage
```

**Application Health Check**:
```bash
# API health
curl http://localhost:8080/docs

# Database connectivity
python -c "from app.config.SqlLiteConfig import get_sql_lite_instance; print('DB OK')"

# LLM connectivity (updated for SecretStr compatibility)
python -c "from app.agents.impl.llm_factory_impl import LLMFactoryImpl; from app.core.enums import LLMProvider; LLMFactoryImpl().create_model(LLMProvider.ollama); print('LLM OK')"

# Dependency injection health
python -c "from app.core.di_container import inject; from app.services import AgentServiceInterface; inject(AgentServiceInterface); print('DI OK')"

# New import structure verification
python -c "from app.services import AgentServiceInterface; from app.repositories import ThreadRepositoryInterface; from app.ai_core import LLMFactoryInterface; print('Imports OK')"

# SecretStr functionality check
python -c "from pydantic import SecretStr; print('SecretStr available:', SecretStr('test'))"
```

#### Common Log Patterns

**Successful request**:
```
method=POST path=/v1/agent/chat status=200 duration_ms=1234.56 cid=uuid
```

**Error patterns to look for**:
```bash
# Database errors
grep -i "sqlite" app.log

# LLM errors
grep -i "llm\|model" app.log

# CORS errors
grep -i "cors" app.log

# Validation errors
grep -i "validation\|422" app.log
```



### Common Issues

1. **mypy error "Source file found twice":**
   - Ensure all directories have `__init__.py` files

2. **Ruff import-order warnings:**
   - Run `make format` to auto-fix

3. **CORS errors:**
   - Check `CORS_ORIGINS` environment variable
   - Ensure frontend URL is included

4. **LLM connection issues:**
   - Verify Ollama is running (if using Ollama)
   - Check API key configuration (if using Gemini)
   - Validate model names in environment variables

5. **Database errors:**
   - Check SQLite file permissions
   - Verify database path configuration

## 📝 License

This project is licensed under the terms of the [LICENSE](LICENSE) file in this repository.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup for Contributors

1. Follow the Quick Start guide
2. Install pre-commit hooks: `make hooks`
3. Run quality checks: `make all`
4. Ensure all tests pass: `make test`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

## 📋 Summary

**AgenticAI** is a production-ready, full-stack AI chat application that demonstrates modern software architecture principles and best practices:

### 🏗️ **Architecture Highlights**
- **Spring MVC Pattern**: Clean separation with interface-implementation design
- **Dependency Injection**: Type-safe DI container following SOLID principles
- **Microservice-Ready**: Modular design with clear service boundaries
- **Real-time Streaming**: Token-level chat streaming via Server-Sent Events

### 🚀 **Technical Excellence**
- **Quality Gates**: Automated formatting, linting, type checking, and security scanning
- **Developer Experience**: Make commands, pre-commit hooks, and comprehensive documentation
- **Testing Ready**: Structured for easy unit testing with dependency injection
- **Production Ready**: Error handling, logging, observability, and deployment guides
- **Enhanced Security**: SecretStr API key protection and improved error handling

### 🔧 **Flexibility & Extensibility**
- **Multiple LLM Support**: Easy to add new providers via factory pattern (OpenAI, Google, Anthropic, Groq, Ollama)
- **Lean Dependencies**: Optional packages for minimal installation footprint
- **Configuration-Driven**: Environment-based configuration for different deployments
- **Modern Stack**: FastAPI + React with TypeScript support

### 🎯 **Perfect For**
- Learning modern full-stack development patterns
- Building production AI chat applications
- Demonstrating clean architecture principles
- Rapid prototyping of AI-powered features

**Get started in 5 minutes:** `git clone → make install → make run → open http://localhost:8080/docs`

---

## 🐳 Docker Deployment

This project includes Docker support for flexible deployment options.

### Docker Files
- `Dockerfile`: Multi-stage Dockerfile that builds both backend and frontend in a single container
- `Dockerfile.backend`: Backend service Dockerfile with integrated frontend build (deprecated)
- `ui/Dockerfile`: Frontend service Dockerfile (deprecated)

### Running with Docker

#### Option 1: Single Container (Backend + Frontend) - Recommended
```bash
# Build the single container
docker build -t agenticai .

# Run the container with external .env file
docker run -p 8000:8000 --env-file .env -v $(pwd)/app/db:/app/app/db agenticai
```

#### Option 2: Separate Containers with Docker Compose
```bash
# Build and run services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# Stop services
docker-compose down

```

