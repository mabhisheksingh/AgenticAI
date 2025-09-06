"""API router for AI agent and chat endpoints.

This module defines the REST API endpoints for chat interactions with AI agents,
including streaming chat responses and conversation management.

Uses dependency injection following DIP principles.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Header, Depends
from fastapi.responses import StreamingResponse

from app.utils.mt5_service import MT5Service
from app.core.enums import RouterTag, LLMProvider
from app.schemas.ChatRequest import ChatRequest
from app.services import AgentServiceInterface
from app.core.di_container import inject


agentic_router = APIRouter(prefix="/agent", tags=[RouterTag.agent.value])


def get_agent_service() -> AgentServiceInterface:
    """Dependency injection for AgentService.
    
    Returns:
        AgentServiceInterface: Injected agent service instance
    """
    return inject(AgentServiceInterface)


def get_mt5_service() -> MT5Service:
    """Dependency injection for MT5Service.

    Returns:
        MT5Service: Injected MT5 service instance
    """
    return inject(MT5Service)


@agentic_router.post("/chat")
async def create_and_update_chat(
        user_id: str = Header(...),
        body: ChatRequest = Body(...),
        agent_service: AgentServiceInterface = Depends(get_agent_service),
        mt5_service: MT5Service = Depends(get_mt5_service),
) -> StreamingResponse:
    """Create or continue a chat conversation with an AI agent.
    
    Handles chat interactions with AI agents, supporting both new conversation
    creation and continuation of existing threads. Returns streaming responses
    for real-time chat experience.
    
    Args:
        user_id (str): User identifier from request header. Required for all requests.
        body (ChatRequest): Chat request payload containing:
            - message: User's chat message
            - thread_id: Optional existing thread ID to continue
            - thread_label: Display label for the thread (required)
            
    Returns:
        StreamingResponse: Server-Sent Events (SSE) stream containing:
            - Initial metadata (thread ID, user ID)
            - Streaming AI response tokens
            - End-of-stream marker
            
    Headers:
        - user-id (required): User/session identifier
        
    Request Body:
        {
            "message": "Hello, how are you?",
            "thread_id": "optional-uuid-for-existing-thread",
            "thread_label": "My Chat Thread"
        }
        
    Response Format (SSE):
        data: {"threadId": "uuid", "userId": "user123"}
        data: {"type": "token", "content": "Hello"}
        data: {"type": "token", "content": "!"}
        data: [DONE]
        
    Response Headers:
        - Content-Type: text/event-stream
        - Cache-Control: no-cache
        - Connection: keep-alive
        - X-Accel-Buffering: no (for proper nginx streaming)
        
    Behavior:
        - New Thread: If thread_id is null, creates new conversation
        - Existing Thread: If thread_id provided, continues conversation
        - Streaming: Real-time token streaming for responsive UI
        - Persistence: Conversation automatically saved via LangGraph
        
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8080/v1/agent/chat",
        ...     headers={"user-id": "user123"},
        ...     json={
        ...         "message": "Hello!",
        ...         "thread_id": None,
        ...         "thread_label": "My First Chat"
        ...     },
        ...     stream=True
        ... )
        >>> for line in response.iter_lines():
        ...     print(line.decode())  # SSE stream
        
    Error Responses:
        - 422: Validation error (invalid request body)
        - 404: Thread not found (for existing thread_id)
        - 500: Internal server error
        
    Note:
        The endpoint uses FastAPI's StreamingResponse to provide real-time
        chat responses, enabling responsive user experiences in the frontend.
        :param mt5_service:
        :param llm_factory:
        :param user_id:
        :param body:
        :param agent_service:
    """
    message: str = body.message
    thread_id: Optional[UUID | None] = body.thread_id
    thread_label: str = body.thread_label  # Now mandatory

    message = mt5_service.correct_grammar(message)
    response = agent_service.stream_chat_tokens(user_id, thread_id, message, thread_label)
    return StreamingResponse(
        response,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
