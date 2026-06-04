"""
Settings endpoints.

All routes require authentication. Anonymous access is rejected by
the get_current_user dependency.

Phase 10 — UI-13, UI-14:
  PATCH /settings/language — upsert the user's language preference
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.settings import LanguagePreferenceResponse, UpdateLanguageRequest
from app.services.settings_service import upsert_language_preference

router = APIRouter(tags=["settings"])


@router.patch(
    "/language",
    response_model=SuccessResponse[LanguagePreferenceResponse],
)
def update_language_preference(
    body: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[LanguagePreferenceResponse]:
    """Upsert the authenticated user's display language preference."""
    pref = upsert_language_preference(db, current_user, body.language_code)
    return SuccessResponse(
        data=LanguagePreferenceResponse.model_validate(pref)
    )
