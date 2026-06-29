"""
Chat and meal models: ChatSession, ChatMessage, AudioMessage, MealEntry.

DATA-05: MealEntry, ChatSession, ChatMessage, AudioMessage models
MEM-04: ChatSession tracks summary, summary_generated_at, message_count
BE-04: lazy="raise" on all relationships
DATA-08: created_at / updated_at
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


TRANSCRIPTION_STATUSES = (
    "pending",
    "not_configured",
    "processing",
    "completed",
    "failed",
)


class ChatSession(Base):
    """
    A conversation session. One session per context window.
    session_type: "onboarding" or "companion"
    """

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="companion"
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="chat_sessions", lazy="raise"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", lazy="raise"
    )
    audio_messages: Mapped[list["AudioMessage"]] = relationship(
        "AudioMessage", back_populates="session", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} type={self.session_type}>"


class ChatMessage(Base):
    """
    Individual message in a ChatSession.
    role: "user", "assistant", or "system"
    status: "pending" (AI generating) | "completed" | "failed"
    """

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    client_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} session_id={self.session_id} role={self.role}>"


class AudioMessage(Base):
    """
    Voice recording uploaded by user.
    transcription_status tracks STT pipeline state.
    """

    __tablename__ = "audio_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Integer, nullable=True)
    transcription_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_configured"
    )
    transcription_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="audio_messages", lazy="raise"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="audio_messages", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<AudioMessage id={self.id} status={self.transcription_status}>"


class MealEntry(Base):
    """
    Text-based meal log entry. Analysis result is stored as JSON text.
    meal_time: "breakfast", "lunch", "dinner", "snack"
    """

    __tablename__ = "meal_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meal_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="meal_entries", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<MealEntry id={self.id} user_id={self.user_id} meal_time={self.meal_time}>"
