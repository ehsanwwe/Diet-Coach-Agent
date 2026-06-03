"""
ChatService: business logic for the companion text chat (Phase 08).

Uses NutritionMemoryService for context and NutritionAgentService for AI.
Stores messages in ChatSession / ChatMessage via chat_repository.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import chat_repository
from app.schemas.chat import ChatHistoryItem, ChatHistoryResponse, ChatMessageResponse
from app.services import nutrition_memory_service
from app.services.nutrition_agent_service import NutritionAgentService

logger = logging.getLogger(__name__)


def send_message(db: Session, user: User, message: str) -> ChatMessageResponse:
    session = chat_repository.get_or_create_companion_session(db, user.id)

    # Store user message
    user_msg = chat_repository.create_message(db, session.id, "user", message)

    # Build history for context (last 10 messages before this one)
    recent = chat_repository.get_recent_messages(db, session.id, limit=11)
    history = [
        {"role": m.role, "content": m.content}
        for m in recent
        if m.id != user_msg.id
    ]

    # Build nutrition memory context
    ctx = nutrition_memory_service.build_context(db, user)

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
