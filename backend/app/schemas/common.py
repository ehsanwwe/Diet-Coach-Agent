"""
Common Pydantic v2 schemas used across all API responses.

BE-06: Pydantic v2 schemas for all request/response models
BE-08: Consistent error response format

All response models inherit from BaseModel with model_config.
v1 patterns (class Config, validator, etc.) are forbidden.
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Structured error context embedded in ErrorResponse.detail."""

    model_config = ConfigDict(extra="allow")


class ErrorResponse(BaseModel):
    """
    Standard error response shape. All API errors MUST use this.

    Shape:
        {"status": "error", "message": "...", "detail": {...}}

    BE-08: Consistent error response format.
    """

    model_config = ConfigDict(frozen=True)

    status: str = "error"
    message: str
    detail: dict[str, Any] = {}


class SuccessResponse(BaseModel, Generic[DataT]):
    """
    Standard success response wrapper for single-item responses.

    Shape:
        {"status": "ok", "data": {...}}
    """

    model_config = ConfigDict(frozen=True)

    status: str = "ok"
    data: DataT


class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Standard paginated list response.

    Shape:
        {"status": "ok", "data": [...], "total": N, "page": N, "page_size": N}
    """

    model_config = ConfigDict(frozen=True)

    status: str = "ok"
    data: list[DataT]
    total: int
    page: int = 1
    page_size: int = 20


class MessageResponse(BaseModel):
    """Simple status + message response for operations that return no data."""

    model_config = ConfigDict(frozen=True)

    status: str = "ok"
    message: str
