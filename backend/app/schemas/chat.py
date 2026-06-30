"""
Companion chat API request/response schemas (Pydantic v2).

Phase 08: text-only chat. No audio or image uploads.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    client_message_id: str | None = Field(None, max_length=64)


class ChatMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    provider: str
    is_mock: bool
    created_at: datetime
    actions_summary: list[str] | None = None
    tool_calls_executed: int | None = None
    suggestion_chips: list[str] | None = None


class ChatHistoryItem(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: datetime
    status: str = "completed"
    error_message: str | None = None


class ChatHistoryResponse(BaseModel):
    session_id: str | None = None
    messages: list[ChatHistoryItem] = Field(default_factory=list)
