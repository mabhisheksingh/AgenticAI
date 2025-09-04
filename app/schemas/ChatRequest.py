from uuid import UUID

from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """
    Represents a chat request.
    """

    thread_id: UUID | None = None
    message: str
    thread_label: str = Field(
        ..., description="Thread label (max 10 words)"
    )  # Made mandatory with validation

    @validator("thread_label")
    def validate_thread_label(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Thread label must be a non-empty string")

        words = v.strip().split()
        if len(words) > 10:
            # Truncate to 10 words and add ellipsis
            truncated = " ".join(words[:10]) + "..."
            return truncated

        return v.strip()
