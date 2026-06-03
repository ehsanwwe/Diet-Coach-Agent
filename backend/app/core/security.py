"""
JWT token creation and verification using PyJWT 2.x.

Tokens include a 'jti' claim for server-side revocation via TokenBlocklist.
All datetimes are naive UTC for SQLite compatibility.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def _utcnow() -> datetime:
    """Current UTC time as naive datetime (SQLite stores naive datetimes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_access_token(subject: str) -> tuple[str, str, datetime]:
    """
    Create a signed JWT.

    Returns:
        (token, jti, expires_at) where expires_at is timezone-aware UTC
        suitable for API responses.
    """
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, expires_at


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT. Raises jwt.PyJWTError subclasses on failure.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
