"""
Consistent error response format for all API endpoints.

Every error response must use this shape:
    {
        "status": "error",
        "message": "Human-readable description",
        "detail": { ... }
    }

BE-08: Consistent error response format across all endpoints.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def error_response(
    message: str,
    detail: dict[str, Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """Return a JSONResponse with the standard error shape."""
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message,
            "detail": detail or {},
        },
    )


def raise_http_error(
    message: str,
    status_code: int = 400,
    detail: dict[str, Any] | None = None,
) -> None:
    """Raise an HTTPException with the standard error detail shape."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "message": message,
            "detail": detail or {},
        },
    )


class AppError(Exception):
    """Base application error. Caught by the global exception handler."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)
