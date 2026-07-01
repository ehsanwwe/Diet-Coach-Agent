"""
Admin authentication endpoints.

POST /admin/auth/login  — credential check, issues admin JWT
POST /admin/auth/logout — client-side invalidation (stateless)
GET  /admin/auth/me     — returns admin username from token
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.admin_dependencies import require_admin
from app.core import admin_security
from app.core.config import settings
from app.core.errors import raise_http_error
from app.schemas.admin import AdminLoginRequest, AdminTokenResponse
from app.schemas.common import MessageResponse, SuccessResponse

router = APIRouter(tags=["admin-auth"])


@router.post("/login", response_model=SuccessResponse[AdminTokenResponse])
def admin_login(body: AdminLoginRequest) -> SuccessResponse[AdminTokenResponse]:
    """
    Authenticate with admin credentials from ENV.
    Returns a signed admin token on success.
    Does not reveal whether username or password was wrong.
    """
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise_http_error(
            "Admin panel is not configured on this server",
            status_code=503,
        )

    if not admin_security.verify_admin_credentials(body.username, body.password, settings):
        raise_http_error("Invalid credentials", status_code=401)

    try:
        token, expires_at = admin_security.create_admin_token(settings)
    except RuntimeError as exc:
        raise_http_error(str(exc), status_code=503)

    return SuccessResponse(
        data=AdminTokenResponse(admin_token=token, expires_at=expires_at)
    )


@router.post("/logout", response_model=MessageResponse)
def admin_logout(
    _admin: dict = Depends(require_admin),
) -> MessageResponse:
    """Stateless logout — client discards the token."""
    return MessageResponse(message="Admin logged out")


@router.get("/me", response_model=SuccessResponse[dict])
def admin_me(
    admin: dict = Depends(require_admin),
) -> SuccessResponse[dict]:
    """Return the admin username from the verified token."""
    return SuccessResponse(data={"username": admin.get("sub", "")})
