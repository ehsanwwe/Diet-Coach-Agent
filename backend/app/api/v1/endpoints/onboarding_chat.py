"""
Onboarding chat endpoints.

POST /onboarding/chat/text   — send a text message
POST /onboarding/chat/audio  — upload a voice recording
GET  /onboarding/chat/history — fetch session history

All routes require authentication.
No AI calls, no STT. Phase 06 scope.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.onboarding_chat import (
    AudioUploadResponse,
    ChatHistoryResponse,
    TextMessageRequest,
    TextMessageResponse,
)
from app.services import onboarding_chat_service as svc

router = APIRouter(tags=["onboarding-chat"])


@router.post("/chat/text", response_model=SuccessResponse[TextMessageResponse])
def send_text(
    body: TextMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[TextMessageResponse]:
    """Send a text message to the onboarding habit chat."""
    try:
        result = svc.send_text_message(db, current_user, body.message)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/chat/audio", response_model=SuccessResponse[AudioUploadResponse])
async def upload_audio(
    file: UploadFile = File(...),
    duration_seconds: float | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[AudioUploadResponse]:
    """Upload a voice recording from MediaRecorder."""
    data = await file.read()
    mime_type = file.content_type or None

    try:
        result = svc.upload_audio(
            db,
            current_user,
            data=data,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
        )
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.get("/chat/history", response_model=SuccessResponse[ChatHistoryResponse])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[ChatHistoryResponse]:
    """Return the authenticated user's onboarding chat history."""
    try:
        result = svc.get_history(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)
