"""
FastAPI dependency: require_admin.

Extracts and validates the admin JWT from the X-Admin-Token header.
All /api/v1/admin/* endpoints except login must use this dependency.
"""
from __future__ import annotations

import jwt
from fastapi import Header

from app.core import admin_security
from app.core.config import settings
from app.core.errors import raise_http_error


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """
    Validate the admin bearer token from X-Admin-Token header.

    Returns the decoded payload dict on success.
    Raises HTTP 401 on missing / invalid / expired token.
    """
    if not x_admin_token:
        raise_http_error("Admin authentication required", status_code=401)

    try:
        payload = admin_security.decode_admin_token(x_admin_token, settings)
    except jwt.ExpiredSignatureError:
        raise_http_error("Admin session expired", status_code=401)
    except (jwt.PyJWTError, RuntimeError):
        raise_http_error("Invalid admin token", status_code=401)

    return payload
