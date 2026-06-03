"""
Pydantic v2 schemas for onboarding chat endpoints.

Covers:
- POST /onboarding/chat/text
- POST /onboarding/chat/audio
- GET  /onboarding/chat/history
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TextMessageRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message must not be empty")
        return stripped


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class TextMessageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut | None = None


class AudioUploadResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    session_id: str
    storage_key: str
    mime_type: str | None
    size_bytes: int | None
    duration_seconds: float | None
    transcription_status: str
    created_at: datetime


class ChatHistoryItem(BaseModel):
    """One item in the history — either a text message or an audio record."""

    model_config = ConfigDict(frozen=True)

    kind: str  # "text" | "audio"
    id: str
    session_id: str
    # Text-specific
    role: str | None = None
    content: str | None = None
    # Audio-specific
    storage_key: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    transcription_status: str | None = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str | None
    items: list[ChatHistoryItem]
    total: int
