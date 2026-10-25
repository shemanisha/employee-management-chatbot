from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: int | None = Field(default=None, gt=0)


class ChatResponse(BaseModel):
    session_id: int
    reply: str


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
