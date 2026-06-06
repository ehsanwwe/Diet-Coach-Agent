"""
Chat repository: DB operations for companion ChatSession and ChatMessage.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession


def get_or_create_companion_session(db: Session, user_id: str) -> ChatSession:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id, ChatSession.session_type == "companion")
        .order_by(ChatSession.created_at.desc())
        .limit(1)
    )
    session = db.execute(stmt).scalar_one_or_none()
    if session is None:
        session = ChatSession(user_id=user_id, session_type="companion")
        db.add(session)
        db.flush()
    return session


def create_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
) -> ChatMessage:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    msg = ChatMessage(session_id=session_id, role=role, content=content, created_at=now)
    db.add(msg)
    db.flush()
    return msg


def get_recent_messages(
    db: Session,
    session_id: str,
    limit: int = 20,
) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return list(reversed(rows))


def get_all_messages(db: Session, session_id: str) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def clear_companion_session(db: Session, user_id: str) -> None:
    """Delete all companion chat sessions for a user (messages deleted first to avoid lazy-raise)."""
    session_ids = db.execute(
        select(ChatSession.id).where(
            ChatSession.user_id == user_id,
            ChatSession.session_type == "companion",
        )
    ).scalars().all()

    if session_ids:
        db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
        db.execute(delete(ChatSession).where(ChatSession.id.in_(session_ids)))
    db.flush()
