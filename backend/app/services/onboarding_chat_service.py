"""
Business logic for onboarding chat (text + audio).

No AI calls. No STT/transcription. Phase 06 scope only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.user import User
from app.repositories import onboarding_chat_repository as repo
from app.schemas.onboarding_chat import (
    AudioUploadResponse,
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatMessageOut,
    TextMessageResponse,
)
from app.services import audio_storage_service as storage

PLACEHOLDER_RESPONSE = (
    "پیام شما دریافت شد. مربی تغذیه به زودی پاسخ خواهد داد."
)


def send_text_message(
    db: Session,
    user: User,
    message: str,
) -> TextMessageResponse:
    session = repo.get_or_create_onboarding_session(db, user.id)

    user_msg = repo.create_text_message(
        db, session.id, role="user", content=message
    )

    # Placeholder assistant response — no AI in Phase 06
    assistant_msg = repo.create_text_message(
        db, session.id, role="assistant", content=PLACEHOLDER_RESPONSE
    )

    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return TextMessageResponse(
        session_id=session.id,
        user_message=ChatMessageOut(
            id=user_msg.id,
            session_id=user_msg.session_id,
            role=user_msg.role,
            content=user_msg.content,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageOut(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
        ),
    )


def upload_audio(
    db: Session,
    user: User,
    data: bytes,
    mime_type: str | None,
    duration_seconds: float | None,
) -> AudioUploadResponse:
    error = storage.validate_upload(data, mime_type)
    if error:
        raise AppError(error, status_code=422)

    session = repo.get_or_create_onboarding_session(db, user.id)

    storage_key, _abs_path = storage.save_audio_file(data, mime_type)

    audio_msg = repo.create_audio_message(
        db,
        session_id=session.id,
        user_id=user.id,
        file_path=storage_key,
        mime_type=mime_type,
        file_size_bytes=len(data),
        duration_seconds=duration_seconds,
        transcription_status="not_configured",
    )

    db.commit()
    db.refresh(audio_msg)

    return AudioUploadResponse(
        id=audio_msg.id,
        session_id=audio_msg.session_id,
        storage_key=storage_key,
        mime_type=audio_msg.mime_type,
        size_bytes=audio_msg.file_size_bytes,
        duration_seconds=float(audio_msg.duration_seconds) if audio_msg.duration_seconds is not None else None,
        transcription_status=audio_msg.transcription_status,
        created_at=audio_msg.created_at,
    )


def get_history(db: Session, user: User) -> ChatHistoryResponse:
    session = repo.get_onboarding_session(db, user.id)

    if session is None:
        return ChatHistoryResponse(session_id=None, items=[], total=0)

    text_msgs = repo.get_text_messages(db, session.id)
    audio_msgs = repo.get_audio_messages(db, session.id)

    items: list[ChatHistoryItem] = []

    for msg in text_msgs:
        items.append(
            ChatHistoryItem(
                kind="text",
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
            )
        )

    for audio in audio_msgs:
        items.append(
            ChatHistoryItem(
                kind="audio",
                id=audio.id,
                session_id=audio.session_id,
                storage_key=audio.file_path,
                mime_type=audio.mime_type,
                size_bytes=audio.file_size_bytes,
                duration_seconds=float(audio.duration_seconds) if audio.duration_seconds is not None else None,
                transcription_status=audio.transcription_status,
                created_at=audio.created_at,
            )
        )

    items.sort(key=lambda x: x.created_at)

    return ChatHistoryResponse(
        session_id=session.id,
        items=items,
        total=len(items),
    )
