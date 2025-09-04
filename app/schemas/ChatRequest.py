"""Pydantic models for chat request and response data structures.

This module defines the data models used for chat API requests,
including validation rules and field constraints.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request model for chat API endpoints.
    
    Represents a chat message request with optional thread context and labeling.
    Includes validation for thread labels to ensure they remain concise.
    
    Attributes:
        thread_id (UUID, optional): Existing thread ID to continue a conversation.
            If None, a new thread will be created.
        message (str): The user's chat message content
        thread_label (str): Display label for the thread, automatically truncated
            to 10 words maximum with ellipsis if longer
            
    Validation Rules:
        - thread_label must be a non-empty string
        - thread_label is automatically truncated to 10 words max
        - Leading/trailing whitespace is stripped from thread_label
        
    Example:
        >>> request = ChatRequest(
        ...     thread_id=None,
        ...     message="Hello, how are you?",
        ...     thread_label="My First Chat"
        ... )
        >>> print(request.thread_label)  # "My First Chat"
        
        >>> long_request = ChatRequest(
        ...     message="Hello",
        ...     thread_label="This is a very long thread label that exceeds ten words"
        ... )
        >>> print(long_request.thread_label)  # "This is a very long thread label that exceeds ten..."
    """

    thread_id: Optional[UUID | None] = None
    message: str
    thread_label: str = Field(
        ..., description="Thread label (max 10 words)"
    )  # Made mandatory with validation

    @field_validator("thread_label")
    def validate_thread_label(cls, v: str) -> str:
        """Validate and format the thread label.
        
        Ensures thread labels are non-empty strings and automatically truncates
        them to 10 words maximum for UI consistency.
        
        Args:
            v (str): The thread label value to validate
            
        Returns:
            str: Validated and potentially truncated thread label
            
        Raises:
            ValueError: If the thread label is empty or not a string
            
        Processing:
            1. Validates input is a non-empty string
            2. Splits into words and counts them
            3. If more than 10 words, truncates to first 10 and adds "..."
            4. Strips leading/trailing whitespace
        """
        if not v or not isinstance(v, str):
            raise ValueError("Thread label must be a non-empty string")

        words = v.strip().split()
        if len(words) > 10:
            # Truncate to 10 words and add ellipsis
            truncated = " ".join(words[:10]) + "..."
            return truncated

        return v.strip()
