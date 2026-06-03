"""
FastAPI shared dependencies: authentication context extraction.

get_auth_context — decodes Bearer token, checks blocklist, returns AuthContext.
get_current_user — derives User from AuthContext (use for most protected routes).
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_session
from app.core.errors import raise_http_error
from app.models.user import User
from app.repositories import auth_repository, user_repository


@dataclass
class AuthContext:
    user: User
    jti: str
    exp: float  # Unix timestamp from token payload


def get_auth_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_session),
) -> AuthContext:
    """
    Extract and validate the Bearer token from the Authorization header.

    Raises HTTP 401 on missing/invalid/expired/blocklisted token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise_http_error("Authorization token required", status_code=401)

    token = authorization[7:]  # strip "Bearer "

    try:
        payload = security.decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise_http_error("Token has expired", status_code=401)
    except jwt.PyJWTError:
        raise_http_error("Invalid token", status_code=401)

    jti: str | None = payload.get("jti")
    user_id: str | None = payload.get("sub")

    if not jti or not user_id:
        raise_http_error("Invalid token payload", status_code=401)

    if auth_repository.is_jti_blocked(db, jti):
        raise_http_error("Token has been revoked", status_code=401)

    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise_http_error("User not found or inactive", status_code=401)

    return AuthContext(user=user, jti=jti, exp=float(payload.get("exp", 0)))


def get_current_user(auth: AuthContext = Depends(get_auth_context)) -> User:
    """Return the authenticated User. Use for routes that only need the user."""
    return auth.user
