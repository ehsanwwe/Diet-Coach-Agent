"""
Auth service: OTP generation, JWT issuance, and logout.

SMS is mocked in development — no real messages are sent.
Set SMS_PROVIDER=mock (default) to keep this behaviour in production-like envs.
"""
from __future__ import annotations

import random
import string

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.errors import AppError
from app.models.user import User
from app.repositories import auth_repository, user_repository
from app.schemas.auth import TokenResponse, UserResponse


def _generate_otp_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def _normalize_phone(phone: str) -> str:
    return phone.strip()


def request_otp(db: Session, phone_number: str) -> dict:
    """Find or create the user, generate an OTP, and (mock-)send it."""
    phone = _normalize_phone(phone_number)

    user = user_repository.get_by_phone(db, phone)
    if user is None:
        user = user_repository.create(db, phone)

    # Development shortcut: always use the configured dev OTP code.
    if settings.ENVIRONMENT == "development":
        otp_code = settings.DEV_OTP_CODE
    else:
        otp_code = _generate_otp_code()

    auth_repository.create_otp(db, user_id=user.id, phone=phone, otp_code=otp_code)

    # Pluggable SMS dispatch — add real provider here when SMS_PROVIDER != "mock".
    if settings.SMS_PROVIDER != "mock":
        raise NotImplementedError(f"SMS provider '{settings.SMS_PROVIDER}' not implemented")

    return {"phone": phone}


def verify_otp(db: Session, phone_number: str, otp_code: str) -> TokenResponse:
    """Validate OTP, mark it consumed, issue a JWT."""
    phone = _normalize_phone(phone_number)

    otp = auth_repository.get_latest_valid_otp(db, phone)
    if otp is None:
        raise AppError("OTP not found or expired", status_code=400)

    if otp.otp_code != otp_code:
        otp.attempt_count += 1
        db.flush()
        raise AppError("Invalid OTP code", status_code=400)

    auth_repository.mark_otp_used(db, otp)

    user = user_repository.get_by_id(db, otp.user_id)
    if user is None or not user.is_active:
        raise AppError("User not found or inactive", status_code=403)

    token, jti, expires_at = security.create_access_token(subject=user.id)

    return TokenResponse(
        access_token=token,
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


def logout(db: Session, jti: str, expires_at_utc: object) -> None:
    """Add the token's jti to the blocklist so it cannot be reused."""
    from datetime import datetime, timezone

    if isinstance(expires_at_utc, datetime):
        auth_repository.add_to_blocklist(db, jti=jti, expires_at=expires_at_utc)
    else:
        # exp from decoded JWT is a Unix timestamp (int/float)
        expires_at = datetime.fromtimestamp(float(expires_at_utc), tz=timezone.utc)
        auth_repository.add_to_blocklist(db, jti=jti, expires_at=expires_at)


def get_current_user(db: Session, user_id: str) -> User:
    """Fetch a user by ID; raise AppError if missing or inactive."""
    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AppError("User not found or inactive", status_code=401)
    return user
