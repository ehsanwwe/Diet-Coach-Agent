"""
Companion chat API request/response schemas (Pydantic v2).

Phase 08: text-only chat. No audio or image uploads.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    provider: str
    is_mock: bool
    created_at: datetime


class ChatHistoryItem(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: str | None = None
    messages: list[ChatHistoryItem] = Field(default_factory=list)
