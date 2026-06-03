"""
Auth endpoints: OTP request, OTP verification, logout, current user.

AUTH-01: POST /auth/request-otp
AUTH-02: POST /auth/verify-otp
AUTH-03: POST /auth/logout
AUTH-04: GET  /auth/me
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, get_auth_context, get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.auth import RequestOTPRequest, TokenResponse, UserResponse, VerifyOTPRequest
from app.schemas.common import MessageResponse, SuccessResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/request-otp", response_model=SuccessResponse[dict])
def request_otp(
    body: RequestOTPRequest,
    db: Session = Depends(get_session),
) -> SuccessResponse[dict]:
    try:
        result = auth_service.request_otp(db, body.phone_number)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data={"phone": result["phone"], "message": "OTP sent successfully"})


@router.post("/verify-otp", response_model=SuccessResponse[TokenResponse])
def verify_otp(
    body: VerifyOTPRequest,
    db: Session = Depends(get_session),
) -> SuccessResponse[TokenResponse]:
    try:
        token_response = auth_service.verify_otp(db, body.phone_number, body.otp_code)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=token_response)


@router.post("/logout", response_model=MessageResponse)
def logout(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_session),
) -> MessageResponse:
    try:
        auth_service.logout(db, jti=auth.jti, expires_at_utc=auth.exp)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=SuccessResponse[UserResponse])
def me(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    return SuccessResponse(data=UserResponse.model_validate(current_user))
