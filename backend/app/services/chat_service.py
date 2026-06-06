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


def send_message(db: Session, user: User, message: str) -> ChatMessageResponse:
    session = chat_repository.get_or_create_companion_session(db, user.id)

    # Store user message
    user_msg = chat_repository.create_message(db, session.id, "user", message)

    # Greeting bypass: return deterministic response without an AI call
    if _is_simple_greeting(message):
        assistant_msg = chat_repository.create_message(
            db, session.id, "assistant", _GREETING_REPLY
        )
        db.commit()
        return ChatMessageResponse(
            message_id=assistant_msg.id,
            role="assistant",
            content=_GREETING_REPLY,
            provider="local",
            is_mock=True,
            created_at=assistant_msg.created_at,
        )

    # Build history for context (last 10 messages before this one)
    recent = chat_repository.get_recent_messages(db, session.id, limit=11)
    history = [
        {"role": m.role, "content": m.content}
        for m in recent
        if m.id != user_msg.id
    ]

    # Build nutrition memory context
    ctx = nutrition_memory_service.build(db, user)

    # Call AI
    agent = NutritionAgentService()
    try:
        parsed, result = agent.chat_message(ctx, message, history)
        reply_text = parsed.get("reply") or ""
        if not reply_text:
            reply_text = "متشکرم از پیام شما. چطور می‌توانم کمک کنم؟"
    except Exception as exc:
        logger.warning("Chat AI call failed: %s", exc)
        reply_text = "متشکرم از پیام شما. در حال حاضر مربی تغذیه در دسترس نیست. بعداً تلاش کنید."
        result = type("R", (), {"provider": "mock_fallback", "is_mock": True})()  # type: ignore[assignment]

    # Store assistant response
    assistant_msg = chat_repository.create_message(db, session.id, "assistant", reply_text)

    db.commit()

    return ChatMessageResponse(
        message_id=assistant_msg.id,
        role="assistant",
        content=reply_text,
        provider=getattr(result, "provider", "mock"),
        is_mock=getattr(result, "is_mock", True),
        created_at=assistant_msg.created_at,
    )


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
        )
        for m in messages
    ]
    return ChatHistoryResponse(session_id=session.id, messages=items)
