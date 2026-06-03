"""
Auth repository. OTP lifecycle and JWT blocklist operations.
SQLAlchemy 2.x select() + session.execute() only — never session.query().
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth import AuthOTP, TokenBlocklist


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_otp(db: Session, user_id: str, phone: str, otp_code: str) -> AuthOTP:
    now = _utcnow()
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Invalidate any existing active OTPs for this phone before creating a new one
    existing = db.execute(
        select(AuthOTP).where(
            AuthOTP.phone == phone,
            AuthOTP.used == False,  # noqa: E712
            AuthOTP.invalidated_at.is_(None),
        )
    ).scalars().all()
    for otp in existing:
        otp.invalidated_at = now

    otp = AuthOTP(
        user_id=user_id,
        phone=phone,
        otp_code=otp_code,
        expires_at=expires_at,
    )
    db.add(otp)
    db.flush()
    return otp


def get_latest_valid_otp(db: Session, phone: str) -> AuthOTP | None:
    now = _utcnow()
    result = db.execute(
        select(AuthOTP)
        .where(
            AuthOTP.phone == phone,
            AuthOTP.used == False,  # noqa: E712
            AuthOTP.invalidated_at.is_(None),
            AuthOTP.expires_at > now,
        )
        .order_by(AuthOTP.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def mark_otp_used(db: Session, otp: AuthOTP) -> None:
    otp.used = True
    db.flush()


def add_to_blocklist(db: Session, jti: str, expires_at: datetime) -> None:
    # Strip timezone info for SQLite compatibility
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    entry = TokenBlocklist(jti=jti, expires_at=expires_at)
    db.add(entry)
    db.flush()


def is_jti_blocked(db: Session, jti: str) -> bool:
    result = db.execute(select(TokenBlocklist).where(TokenBlocklist.jti == jti))
    return result.scalar_one_or_none() is not None
