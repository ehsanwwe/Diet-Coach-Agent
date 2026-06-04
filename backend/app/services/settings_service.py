"""
Settings service: upsert_language_preference.

Phase 10: Settings, Polish & Remaining UI
UI-13, UI-14
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import UserLanguagePreference
from app.models.user import User


def upsert_language_preference(
    db: Session, user: User, language_code: str
) -> UserLanguagePreference:
    """Insert or update the user's language preference (one row per user)."""
    stmt = select(UserLanguagePreference).where(
        UserLanguagePreference.user_id == user.id
    )
    pref = db.execute(stmt).scalar_one_or_none()
    if pref is None:
        pref = UserLanguagePreference(user_id=user.id, language_code=language_code)
        db.add(pref)
    else:
        pref.language_code = language_code
        pref.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(pref)
    return pref
