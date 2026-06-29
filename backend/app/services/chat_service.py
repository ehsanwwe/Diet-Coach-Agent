"""
ChatService: business logic for the companion text chat (Phase 08).

Uses NutritionMemoryService for context and NutritionAgentService for AI.
Stores messages in ChatSession / ChatMessage via chat_repository.
"""
from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import chat_repository
from app.schemas.chat import ChatHistoryItem, ChatHistoryResponse, ChatMessageResponse
from app.services import nutrition_memory_service
from app.services.nutrition_agent_service import NutritionAgentService

logger = logging.getLogger(__name__)

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
    return process_user_message(db, user, message, client_message_id=client_message_id)


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
