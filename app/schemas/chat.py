"""Additional chat-related Pydantic models.

This module provides supplementary data models for chat operations,
including message bodies and response structures.
"""
from uuid import UUID

from pydantic import BaseModel


class ChatMessageBody(BaseModel):
    """Simple chat message body for basic message requests.
    
    A minimal model containing just the message content, used for
    simplified chat endpoints that don't require thread context.
    
    Attributes:
        message (str): The chat message content
        
    Example:
        >>> body = ChatMessageBody(message="Hello, world!")
        >>> print(body.message)  # "Hello, world!"
    """
    message: str


class ChatMessageResponse(BaseModel):
    """Response model for chat message exchanges.
    
    Represents a complete chat interaction including the user's message,
    the AI's response, and the thread context.
    
    Attributes:
        threadId (UUID): The thread ID where this exchange occurred
        userId (str): The user/session ID who sent the message
        message (str): The original user message
        response (str): The AI assistant's response
        
    Example:
        >>> response = ChatMessageResponse(
        ...     threadId=UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     userId="user123",
        ...     message="Hello",
        ...     response="Hello! How can I help you today?"
        ... )
        
    Note:
        This model uses camelCase naming (threadId, userId) to match
        frontend expectations, while internal code typically uses snake_case.
    """
    threadId: UUID
    userId: str
    message: str
    response: str
