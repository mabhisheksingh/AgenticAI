from pydantic import BaseModel
from uuid import UUID


class ChatMessageBody(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    threadId: UUID
    userId: str
    message: str
    response: str
