"""
Admin panel Pydantic v2 schemas.
All schemas use model_config with from_attributes=True where ORM objects are used.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    admin_token: str
    expires_at: datetime


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    phone: str
    full_name: str | None
    language: str | None
    is_onboarded: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    has_nutrition_plan: bool
    chat_message_count: int
    latest_activity: datetime | None


class AdminUserDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    phone: str
    is_active: bool
    is_onboarded: bool
    created_at: datetime
    updated_at: datetime
    # Profile summary
    full_name: str | None
    gender: str | None
    birth_date: str | None  # ISO string
    height_cm: float | None
    weight_kg: float | None
    target_weight_kg: float | None
    # Language
    language: str | None
    # Goal
    goal_type: str | None
    # Risk
    risk_level: str | None
    # Counts
    chat_session_count: int
    chat_message_count: int
    nutrition_plan_count: int


class AdminDeleteResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    deleted: bool
    user_id: str
    deleted_records: dict[str, int]


class AdminExportUser(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    phone: str
    created_at: str  # ISO


class AdminExportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    export_type: str
    exported_at: str  # ISO
    user: AdminExportUser
    data: dict[str, Any]
