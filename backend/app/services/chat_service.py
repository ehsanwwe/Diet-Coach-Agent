"""
ChatService: business logic for the companion text chat (Phase 08).

Uses NutritionMemoryService for context and NutritionAgentService for AI.
Stores messages in ChatSession / ChatMessage via chat_repository.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.audit import AuditLog
from app.models.user import User
from app.repositories import chat_repository
from app.schemas.chat import ChatHistoryItem, ChatHistoryResponse, ChatMessageResponse
from app.services import nutrition_memory_service
from app.services.nutrition_agent_service import NutritionAgentService

logger = logging.getLogger(__name__)

_generation_locks: dict[str, threading.Lock] = {}
_generation_locks_guard = threading.Lock()


@contextmanager
def _exclusive_generation(user_id: str):
    """Prevent overlapping send/edit generations for one active conversation."""
    with _generation_locks_guard:
        lock = _generation_locks.setdefault(user_id, threading.Lock())
    if not lock.acquire(blocking=False):
        raise AppError("A chat response is already being generated", status_code=409)
    try:
        yield
    finally:
        lock.release()

# Greeting detection: short pure-greeting messages that don't need AI reasoning.
_GREETING_RE = re.compile(
    r"^[\s]*"
    r"(?:سلام|درود|خوبی[؟?]?|چطوری[؟?]?|چطورید[؟?]?|خوب هستی[؟?]?|"
    r"صبح بخیر|عصر بخیر|شب بخیر|وقت بخیر|"
    r"hi|hello|hey|good\s+morning|good\s+evening|good\s+night|howdy)"
    r"[\s!؟?🌿🌱✨🍃،.]*$",
    re.IGNORECASE | re.UNICODE,
)

_GREETING_REPLY = (
    "سلام، خوش اومدی 🌿\n"
    "امروز می‌تونم در کدوم موضوع کمکت کنم؟\n"
    "• برنامه غذایی یا تنظیم وعده‌ها\n"
    "• انتخاب غذا یا هوس خوردنی الان\n"
    "• پیشرفت هدف و وضعیت بدن��\n"
    "• سوال درباره مواد مغذی یا ترکیب غذا"
)


def _is_simple_greeting(message: str) -> bool:
    return bool(_GREETING_RE.match(message.strip()))


def send_message(
    db: Session,
    user: User,
    message: str,
    client_message_id: str | None = None,
) -> ChatMessageResponse:
    from app.services.agent_orchestrator import process_user_message
    with _exclusive_generation(user.id):
        return process_user_message(db, user, message, client_message_id=client_message_id)


def edit_message(
    db: Session,
    user: User,
    session_id: str,
    message_id: str,
    content: str,
) -> ChatMessageResponse:
    """Replace a user message, truncate its continuation, and regenerate normally."""
    from app.services.agent_orchestrator import process_user_message

    with _exclusive_generation(user.id):
        session = chat_repository.get_owned_companion_session(db, user.id, session_id)
        if session is None:
            raise AppError("Chat message not found", status_code=404)

        message = chat_repository.get_message_in_session(db, session.id, message_id)
        if message is None:
            raise AppError("Chat message not found", status_code=404)
        if message.role != "user":
            raise AppError("Message cannot be edited", status_code=422)
        if chat_repository.has_pending_assistant_message(db, session.id):
            raise AppError("A chat response is already being generated", status_code=409)

        try:
            deleted_count = chat_repository.truncate_after_message(db, session, message)
            message.content = content
            message.status = "completed"
            message.error_message = None
            pending = chat_repository.create_message(
                db,
                session.id,
                "assistant",
                "",
                status="pending",
            )
            db.add(
                AuditLog(
                    user_id=user.id,
                    action="chat_message_edited",
                    resource_type="chat_message",
                    resource_id=message.id,
                    detail=json.dumps({"session_id": session.id, "deleted_messages": deleted_count}),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        try:
            return process_user_message(
                db,
                user,
                content,
                existing_session=session,
                existing_user_message=message,
                existing_pending_message=pending,
            )
        except Exception:
            db.rollback()
            failed_pending = chat_repository.get_message_in_session(db, session.id, pending.id)
            if failed_pending is not None:
                chat_repository.update_message_status(
                    db,
                    failed_pending.id,
                    "failed",
                    error_message="generation_failed",
                )
                db.commit()
            raise


def clear_session(db: Session, user: User) -> None:
    """Delete the user's companion chat session and all messages."""
    chat_repository.clear_companion_session(db, user.id)
    db.commit()


def get_history(db: Session, user: User) -> ChatHistoryResponse:
    session = chat_repository.get_or_create_companion_session(db, user.id)
    db.commit()

    messages = chat_repository.get_all_messages(db, session.id)
    items = [
        ChatHistoryItem(
            message_id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            status=m.status,
            error_message=m.error_message,
        )
        for m in messages
    ]
    return ChatHistoryResponse(session_id=session.id, messages=items)
