"""
Database access for onboarding chat sessions, text messages, and audio messages.

SQLAlchemy 2.x select() style — no session.query().
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import AudioMessage, ChatMessage, ChatSession


def get_or_create_onboarding_session(db: Session, user_id: str) -> ChatSession:
    """Return the user's onboarding ChatSession, creating it if absent."""
    result = db.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.session_type == "onboarding",
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        session = ChatSession(user_id=user_id, session_type="onboarding")
        db.add(session)
        db.flush()
    return session


def create_text_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.flush()
    return msg


def create_audio_message(
    db: Session,
    session_id: str,
    user_id: str,
    file_path: str,
    mime_type: str | None,
    file_size_bytes: int | None,
    duration_seconds: float | None,
    transcription_status: str,
) -> AudioMessage:
    audio = AudioMessage(
        session_id=session_id,
        user_id=user_id,
        file_path=file_path,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        duration_seconds=duration_seconds,
        transcription_status=transcription_status,
    )
    db.add(audio)
    db.flush()
    return audio


def get_onboarding_session(db: Session, user_id: str) -> ChatSession | None:
    result = db.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.session_type == "onboarding",
        )
    )
    return result.scalar_one_or_none()


def get_text_messages(db: Session, session_id: str) -> list[ChatMessage]:
    result = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return list(result.scalars().all())


def get_audio_messages(db: Session, session_id: str) -> list[AudioMessage]:
    result = db.execute(
        select(AudioMessage)
        .where(AudioMessage.session_id == session_id)
        .order_by(AudioMessage.created_at)
    )
    return list(result.scalars().all())
