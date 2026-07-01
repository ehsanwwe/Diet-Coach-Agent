"""
Admin-specific JWT creation and verification.

Uses a SEPARATE secret (ADMIN_SESSION_SECRET) and a separate token type claim
so admin tokens cannot be used as normal user tokens and vice-versa.
Credential comparison uses hmac.compare_digest to resist timing attacks.
"""
from __future__ import annotations

import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt

_ALGORITHM = "HS256"
_TOKEN_TYPE = "admin"


def verify_admin_credentials(username: str, password: str, cfg) -> bool:
    """Constant-time comparison of submitted credentials against env settings."""
    if not cfg.ADMIN_USERNAME or not cfg.ADMIN_PASSWORD:
        return False
    username_ok = hmac.compare_digest(username.encode(), cfg.ADMIN_USERNAME.encode())
    password_ok = hmac.compare_digest(password.encode(), cfg.ADMIN_PASSWORD.encode())
    return username_ok and password_ok


def create_admin_token(cfg) -> tuple[str, datetime]:
    """
    Issue a signed admin JWT.

    Returns (token_string, expires_at_utc).
    Raises RuntimeError if ADMIN_SESSION_SECRET is not configured.
    """
    if not cfg.ADMIN_SESSION_SECRET:
        raise RuntimeError("ADMIN_SESSION_SECRET is not configured")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=cfg.ADMIN_SESSION_EXPIRE_MINUTES)
    payload = {
        "sub": cfg.ADMIN_USERNAME,
        "type": _TOKEN_TYPE,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, cfg.ADMIN_SESSION_SECRET, algorithm=_ALGORITHM)
    return token, expires_at


def decode_admin_token(token: str, cfg) -> dict:
    """
    Decode and verify an admin JWT.

    Raises jwt.PyJWTError subclasses on invalid/expired tokens.
    Raises jwt.InvalidTokenError if the token type is not 'admin'.
    """
    if not cfg.ADMIN_SESSION_SECRET:
        raise RuntimeError("ADMIN_SESSION_SECRET is not configured")
    payload = jwt.decode(token, cfg.ADMIN_SESSION_SECRET, algorithms=[_ALGORITHM])
    if payload.get("type") != _TOKEN_TYPE:
        raise jwt.InvalidTokenError("Not an admin token")
    return payload
