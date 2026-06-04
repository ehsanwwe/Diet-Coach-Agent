"""
Pydantic v2 schemas for Settings endpoints.

Phase 10: Settings, Polish & Remaining UI
UI-13, UI-14
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UpdateLanguageRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    language_code: Literal["fa", "en", "ar"]


class LanguagePreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language_code: str
    updated_at: datetime
