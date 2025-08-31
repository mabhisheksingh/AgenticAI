from uuid import UUID

from pydantic import BaseModel


class ChatMessageBody(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    threadId: UUID
    userId: str
    message: str
    response: str
