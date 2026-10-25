from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: int | None = Field(default=None, gt=0)

    @field_validator("message")
    @classmethod
    def reject_blank_messages(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be blank")
        return message


class ChatResponse(BaseModel):
    session_id: int
    reply: str = Field(min_length=1, max_length=8000)


class ChatSessionResponse(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    role: str
    content: Any
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_call_id: str | None = None
    tool_name: str | None = None
    status: str | None = None
