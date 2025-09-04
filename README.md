# AgenticAI - Full-Stack AI Chat Application

A production-ready full-stack application featuring a **FastAPI backend** and **React frontend** for an Agentic AI system. Users can submit chat messages to AI agents, manage conversation threads, and interact with multiple LLM providers through a modern, responsive UI.

## 🚀 Key Features

### Backend (FastAPI)
- **Versioned REST API** with centralized routing (`/v1/*`)
- **Spring MVC Architecture** with interface-implementation separation
- **Dependency Injection Container** following DIP principles
- **Multiple LLM Support** (Ollama, Google Gemini) via factory pattern
- **LangGraph Integration** for agent orchestration with checkpointing
- **SQLite Persistence** with thread management
- **Global Error Handling** with standardized response formats
- **Observability** with correlation IDs and request logging
- **Developer Tooling** (Ruff, Black, mypy, pytest, pre-commit)

### Frontend (React + Vite)
- **Modern Chat Interface** with Material-UI components
- **Real-time Streaming** chat responses via Server-Sent Events (SSE)
- **Thread Management** with sidebar navigation and labels
- **User Management** with dropdown selection and persistence
- **Dark/Light Mode** toggle with localStorage persistence
- **Responsive Design** optimized for desktop and mobile
- **Error Boundaries** for graceful error handling

## 🏢 Architecture Overview

### System Architecture
```
┌───────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Sidebar   │ │  Chat Area  │ │      User Selector      │ │
│  │  (Threads)  │ │ (Messages)  │ │     (Dropdown)          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                               │ HTTP/SSE
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Routers   │ │  Services   │ │      Repositories       │ │
│  │ (v1/user/*) │ │ (Business)  │ │     (Data Access)       │ │
│  │ (v1/agent/*)│ │   Logic     │ │                         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│                               │                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ LLM Factory │ │ LangGraph   │ │       SQLite DB         │ │
│  │ (Ollama/    │ │ (Agents)    │ │    (Persistence)        │ │
│  │  Gemini)    │ │             │ │                         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Frontend** → User interacts with chat interface
2. **API Layer** → HTTP requests routed through versioned endpoints
3. **Service Layer** → Business logic processes requests
4. **LangGraph** → AI agents orchestrate LLM interactions
5. **LLM Providers** → Generate AI responses (Ollama/Gemini)
6. **Repository** → Data persisted in SQLite with thread management
7. **Response** → Streaming or standard JSON responses to frontend

## 📁 Project Structure

### Backend Structure
```
app/
  ├── core/                     # Core utilities and middleware
  │   ├── enums.py              # APIVersion, RouterTag, ErrorCode, LLMProvider
  │   ├── errors.py             # AppError, NotFoundError, ApiErrorItem
  │   ├── exception_handlers.py # Global error handling
  │   ├── middleware.py         # CorrelationID, Request logging
  │   ├── response.py           # ok(), error(), paginate() helpers
  │   └── di_container.py       # Dependency injection container
  ├── services/                 # Service layer (Spring MVC pattern)
  │   ├── __init__.py           # Interface exports
  │   ├── agent_service_interface.py    # Agent service contracts
  │   ├── user_service_interface.py     # User service contracts
  │   └── impl/                 # Service implementations
  │       ├── agent_service_impl.py     # Agent service implementation
  │       ├── user_service_impl.py      # User service implementation
  │       └── langgraph_service_impl.py # LangGraph orchestration
  ├── repositories/             # Repository layer (Spring MVC pattern)
  │   ├── __init__.py           # Interface exports
  │   ├── thread_repository_interface.py    # Repository contracts
  │   ├── database_interface.py             # Database contracts
  │   └── impl/                 # Repository implementations
  │       └── thread_repository_impl.py    # Thread/session CRUD
  ├── agents/                   # AI/LLM integration (Spring MVC pattern)
  │   ├── __init__.py           # Interface exports
  │   ├── llm_provider_interface.py     # LLM provider contracts
  │   └── impl/                 # Agent implementations
  │       └── llm_factory_impl.py       # Factory for Ollama/Gemini LLMs
  ├── routers/                  # API endpoint routers
  │   ├── UserRouter.py         # /v1/user/* endpoints
  │   └── AgenticRouter.py      # /v1/agent/* endpoints
  ├── schemas/                  # Pydantic models
  │   ├── ChatRequest.py        # Chat request/response schemas
  │   └── chat.py               # Additional chat schemas
  ├── utils/                    # Utility functions
  │   └── text.py               # Text processing utilities
  ├── config/                   # Configuration management
  │   └── SqlLiteConfig.py      # SQLite connection singleton
  ├── dispatch.py               # Router aggregation
  ├── main.py                   # FastAPI app creation
  └── db/                       # Database files
      └── chat.db               # SQLite database
```

#### Spring MVC Package Structure

The backend follows **Spring MVC conventions** for clean separation of concerns:

**Interface-Implementation Pattern:**
- **Interfaces** are located in main packages (`services/`, `repositories/`, `agents/`)
- **Implementations** are organized in `impl/` subfolders
- **Dependency Injection** connects interfaces to implementations

**Package Organization:**
```python
# Import interfaces from main packages
from app.services import AgentServiceInterface, UserServiceInterface
from app.repositories import ThreadRepositoryInterface, DatabaseConnectionProvider
from app.agents import LLMProviderInterface

# Implementations are accessed through DI container
from app.core.di_container import inject
agent_service = inject(AgentServiceInterface)
```

**Benefits of This Structure:**
- **Interface Segregation Principle (ISP)**: Clean, focused interfaces
- **Dependency Inversion Principle (DIP)**: High-level modules depend on abstractions
- **Testability**: Easy to mock dependencies for unit testing
- **Maintainability**: Clear separation between contracts and implementations
- **Spring MVC Familiarity**: Java/Spring developers will find this structure familiar

**Layer Responsibilities:**
- **Services Layer**: Business logic and orchestration
- **Repository Layer**: Data access and persistence
- **Agents Layer**: AI/LLM provider abstraction
- **Routers Layer**: HTTP endpoint handling and request routing

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

## 🔧 Prerequisites

### Backend Requirements
- **Python 3.11+**
- **pip** (and optionally pipenv)
- **make** (recommended for convenience)

### Frontend Requirements
- **Node.js 18+**
- **npm** (comes with Node.js)

### LLM Provider Setup

#### Option 1: Ollama (Local LLM)
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.1

# Run server (usually auto-starts)
ollama serve
```

#### Option 2: Google Gemini
- Obtain a Google AI API key from [Google AI Studio](https://aistudio.google.com/)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <your-repo-url> AgenticAI
cd AgenticAI
```

### 2. Backend Setup

#### Using venv (Recommended)
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Using pipenv (Alternative)
```bash
pipenv install --dev
```

### 3. Environment Configuration

Create a `.env` file in the repository root:

```env
# --- Server Configuration ---
HOST=0.0.0.0
PORT=8080

# --- CORS Settings ---
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# --- Database ---
# SQLITE_DB_PATH=./app/db/chat.db  # Optional, defaults to app/db/chat.db

# --- LLM Provider Selection ---
LLM_PROVIDER=ollama  # or 'google_genai'

# --- Google Gemini Configuration ---
# GOOGLE_API_KEY=your-google-api-key
# GEMINI_MODEL_NAME=gemini-2.5-flash

# --- Ollama Configuration ---
OLLAMA_MODEL_NAME=llama3.1:8b

# --- Common LLM Settings ---
LLM_TEMPERATURE=0.7
```

### 4. Run Backend

#### Method 1: Direct uvicorn
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

#### Method 2: Python module
```bash
python -m app.main
```

#### Method 3: Make command
```bash
make run
```

#### Method 4: Pipenv
```bash
pipenv run uvicorn app.main:app --reload
```

### 5. Frontend Setup

```bash
cd ui
npm install

# Create environment file (optional)
echo "VITE_API_BASE_URL=http://localhost:8080" > .env
echo "VITE_API_PATH=/v1" >> .env

# Start development server
npm run dev
```

### 6. Access Application

- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8080/docs
- **Alternative API Docs**: http://localhost:8080/redoc

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

#### DELETE /v1/user/threads/{thread_id}
**Purpose**: Delete a specific thread

**Path Parameters:**
- `thread_id` (UUID): Thread identifier to delete

**Headers:**
- `user-id` (required): User session identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "affected": 1
  },
  "meta": null
}
```

#### PATCH /v1/user/rename-thread-label
**Purpose**: Update the label of an existing thread

**Query Parameters:**
- `threadId` (UUID, required): Thread identifier
- `label` (string, required): New label for the thread

**Headers:**
- `user-id` (required): User session identifier

**Example:**
```bash
curl -X PATCH \
  -H 'user-id: user123' \
  'http://localhost:8080/v1/user/rename-thread-label?threadId=uuid&label=New%20Label'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "updated": true,
    "affected": 1
  },
  "meta": null
}
```

#### DELETE /v1/user/{user_id}
**Purpose**: Delete a user and all associated threads

**Path Parameters:**
- `user_id` (string): User identifier to delete

**Headers:**
- `user-id` (required): Admin user identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "affected": 5
  },
  "meta": null
}
```

### Error Handling

#### Common Error Codes
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (422): Invalid request data
- `INTERNAL_ERROR` (500): Server error

#### Error Response Examples

**Validation Error:**
```json
[
  {
    "errorcode": "VALIDATION_ERROR",
    "errormessage": "Field is required",
    "errorStatus": 422,
    "errorField": "message"
  }
]
```

**Not Found Error:**
```json
[
  {
    "errorcode": "NOT_FOUND",
    "errormessage": "Thread not found",
    "errorStatus": 404,
    "errorField": null
  }
]
```

### Rate Limiting and Performance

#### Streaming Responses
- Chat endpoints use Server-Sent Events for real-time responses
- Connection kept alive until `[DONE]` marker
- Automatic reconnection supported by EventSource API

#### Best Practices
- Reuse thread IDs for continuing conversations
- Use meaningful thread labels for better UX
- Handle connection drops gracefully in client code
- Monitor SSE events for proper message reconstruction

### Interactive API Documentation

#### Swagger UI
Access interactive API documentation at [http://localhost:8080/docs](http://localhost:8080/docs)

Features:
- Try-it-out functionality for all endpoints
- Request/response examples
- Schema definitions
- Authentication configuration

#### ReDoc
Alternative documentation interface at [http://localhost:8080/redoc](http://localhost:8080/redoc)

Features:
- Clean, readable documentation layout
- Comprehensive schema information
- Code examples in multiple languages
- Hierarchical navigation



### Authentication & Headers

All requests require a `user-id` header:
```bash
curl -H "user-id: your-user-id" ...
```

### Chat Endpoints

#### POST /v1/agent/chat
Send a chat message to the AI agent.

**Headers:**
- `user-id` (required): User identifier
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "thread_id": "optional-thread-uuid",
  "thread_label": "Optional thread name"
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"type": "token", "content": "Hello"}
data: {"type": "token", "content": "!"}
data: [DONE]
```

### Thread Management Endpoints

#### GET /v1/user/threads
List all threads for a user.

**Headers:**
- `user-id` (required)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "thread_id": "uuid",
      "thread_label": "My Chat",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /v1/user/thread/{thread_id}
Get detailed thread information with messages.

#### DELETE /v1/user/threads/{thread_id}
Delete a specific thread.

#### PATCH /v1/user/rename-thread-label
Rename a thread's label.

**Query Parameters:**
- `threadId` (required): Thread UUID
- `label` (required): New label

### User Management Endpoints

#### GET /v1/user/get-all
Get all user IDs in the system.

### Example Requests

```bash
# Send a chat message
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'user-id: user-123' \
  http://localhost:8080/v1/agent/chat \
  -d '{"message":"Hello!"}'

# List user threads
curl -H 'user-id: user-123' \
  http://localhost:8080/v1/user/threads

# Delete a thread
curl -X DELETE \
  -H 'user-id: user-123' \
  http://localhost:8080/v1/user/threads/thread-uuid

# Rename thread
curl -X PATCH \
  -H 'user-id: user-123' \
  'http://localhost:8080/v1/user/rename-thread-label?threadId=uuid&label=NewName'
```

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

### User Experience
- **User selection** dropdown with search functionality
- **Dark/light mode** toggle with persistence
- **Error boundaries** for graceful error handling
- **Loading states** and progress indicators
- **Keyboard shortcuts** for common actions

### Technical Features
- **Material-UI** components for consistent design
- **Custom hooks** for state management (useChat, useThreads)
- **Error handling** with user-friendly messages
- **Local storage** for user preferences
- **API integration** with proper error handling

## 📚 Code Documentation

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
- **State Management**: How the class manages internal state

#### Function Documentation
- **Purpose**: Clear description of what the function does
- **Parameters**: Type hints and detailed parameter descriptions
- **Returns**: Return type and description of returned values
- **Examples**: Code examples showing typical usage
- **Error Handling**: Exceptions that may be raised
- **Side Effects**: Any state changes or external effects

#### Example Documentation Structure

```python
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
- **`impl/llm_factory_impl.py`**: Factory implementation for Ollama/Gemini LLMs

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
```bash
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
```python
# Old complex import paths
from app.services.interfaces.agent_service_interface import AgentServiceInterface
from app.repositories.interfaces.thread_repository_interface import ThreadRepositoryInterface
from app.agents.interfaces.llm_provider_interface import LLMProviderInterface
```

**After (Spring MVC Structure):**
```python
# New clean import paths
from app.services import AgentServiceInterface, UserServiceInterface
from app.repositories import ThreadRepositoryInterface, DatabaseConnectionProvider
from app.agents import LLMProviderInterface
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

## 🚀 Deployment

### Production Build

#### Backend
```bash
# Using Docker (recommended)
docker build -t agentic-ai-backend .
docker run -p 8080:8080 agentic-ai-backend

# Or direct deployment
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
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
   pip install -r requirements-dev.txt
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

**Issue**: `RuntimeError: LLM_PROVIDER is not set`

**Solutions**:
1. **Set environment variables**:
   ```bash
   export LLM_PROVIDER=ollama  # or google_genai
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
   from app.agents import LLMProviderInterface
   
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
   from app.agents.LLMFactory import LLMFactory
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

# LLM connectivity 
python -c "from app.agents.impl.llm_factory_impl import LLMFactoryImpl; LLMFactoryImpl().create_model(); print('LLM OK')"

# Dependency injection health
python -c "from app.core.di_container import inject; from app.services import AgentServiceInterface; inject(AgentServiceInterface); print('DI OK')"

# New import structure verification
python -c "from app.services import AgentServiceInterface; from app.repositories import ThreadRepositoryInterface; from app.agents import LLMProviderInterface; print('Imports OK')"
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