"""
Companion chat endpoints — Phase 08.

POST /chat/message  — send a text message, get AI response
GET  /chat/history  — fetch full companion chat history

Both routes require authentication.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatMessageRequest, ChatMessageResponse
from app.schemas.common import SuccessResponse
from app.services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/message", response_model=SuccessResponse[ChatMessageResponse], status_code=201)
def send_message(
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[ChatMessageResponse]:
    """Send a text message and receive an AI nutrition companion response."""
    try:
        result = chat_service.send_message(db, current_user, body.message)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    except Exception as exc:
        raise_http_error(f"Chat service error: {exc}", status_code=500)
    return SuccessResponse(data=result)


@router.get("/history", response_model=SuccessResponse[ChatHistoryResponse])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[ChatHistoryResponse]:
    """Return the authenticated user's full companion chat history."""
    try:
        result = chat_service.get_history(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    except Exception as exc:
        raise_http_error(f"Failed to load history: {exc}", status_code=500)
    return SuccessResponse(data=result)
