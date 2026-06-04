"""
Tests for PATCH /api/v1/settings/language endpoint.

Covers:
  - 200 happy path: upsert creates UserLanguagePreference row
  - 200 upsert: second call updates the existing row (no duplicate)
  - 401 unauthorized: request without valid auth token
  - 422 invalid locale: language_code not in ["fa", "en", "ar"]
  - 422 missing field: empty body
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import UserLanguagePreference
from app.models.user import User


def test_update_language_success(client, test_user: User, db_session: Session):
    resp = client.patch("/api/v1/settings/language", json={"language_code": "en"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["data"]["language_code"] == "en"
    assert "updated_at" in body["data"]

    pref = db_session.execute(
        select(UserLanguagePreference).where(
            UserLanguagePreference.user_id == test_user.id
        )
    ).scalar_one()
    assert pref.language_code == "en"


def test_update_language_upsert(client, test_user: User, db_session: Session):
    """Two calls must result in exactly one row with the latest language."""
    client.patch("/api/v1/settings/language", json={"language_code": "fa"})
    client.patch("/api/v1/settings/language", json={"language_code": "ar"})

    rows = (
        db_session.execute(
            select(UserLanguagePreference).where(
                UserLanguagePreference.user_id == test_user.id
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].language_code == "ar"


def test_update_language_unauthorized(unauth_client):
    resp = unauth_client.patch(
        "/api/v1/settings/language", json={"language_code": "en"}
    )
    assert resp.status_code == 401


def test_update_language_invalid_locale(client):
    resp = client.patch("/api/v1/settings/language", json={"language_code": "xx"})
    assert resp.status_code == 422


def test_update_language_missing_field(client):
    resp = client.patch("/api/v1/settings/language", json={})
    assert resp.status_code == 422
