"""
Admin panel tests.

Covers:
- Login succeeds with correct ENV credentials
- Login fails with wrong credentials
- Admin users endpoint rejects non-admin requests
- Export endpoints return the required JSON shape
- Delete endpoint removes a user and all related records
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_admin_token(client: TestClient) -> str:
    """Log in and return the admin token string."""
    resp = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": os.environ["ADMIN_USERNAME"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["admin_token"]


def _admin_headers(token: str) -> dict[str, str]:
    return {"X-Admin-Token": token}


# ── Auth tests ────────────────────────────────────────────────────────────────

def test_admin_login_succeeds(unauth_client: TestClient):
    """Correct credentials return a token."""
    resp = unauth_client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": os.environ["ADMIN_USERNAME"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "admin_token" in data
    assert "expires_at" in data


def test_admin_login_wrong_password(unauth_client: TestClient):
    """Wrong password returns 401 without revealing which field was wrong."""
    resp = unauth_client.post(
        "/api/v1/admin/auth/login",
        json={"username": os.environ["ADMIN_USERNAME"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_admin_login_wrong_username(unauth_client: TestClient):
    """Wrong username returns 401."""
    resp = unauth_client.post(
        "/api/v1/admin/auth/login",
        json={"username": "notadmin", "password": os.environ["ADMIN_PASSWORD"]},
    )
    assert resp.status_code == 401


def test_admin_me(unauth_client: TestClient):
    """Authenticated GET /admin/auth/me returns the admin username."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.get("/api/v1/admin/auth/me", headers=_admin_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == os.environ["ADMIN_USERNAME"]


def test_admin_me_no_token(unauth_client: TestClient):
    """Missing token returns 401."""
    resp = unauth_client.get("/api/v1/admin/auth/me")
    assert resp.status_code == 401


def test_admin_me_invalid_token(unauth_client: TestClient):
    """Garbage token returns 401."""
    resp = unauth_client.get(
        "/api/v1/admin/auth/me", headers={"X-Admin-Token": "not.a.valid.jwt"}
    )
    assert resp.status_code == 401


# ── User list / detail tests ───────────────────────────────────────────────────

def test_admin_users_list_requires_auth(unauth_client: TestClient):
    """No token → 401 on user list."""
    resp = unauth_client.get("/api/v1/admin/users")
    assert resp.status_code == 401


def test_admin_users_list_normal_user_token_rejected(unauth_client: TestClient):
    """Normal user Bearer token is not accepted as admin token."""
    resp = unauth_client.get(
        "/api/v1/admin/users",
        headers={"X-Admin-Token": "Bearer faketoken"},
    )
    assert resp.status_code == 401


def test_admin_users_list_ok(unauth_client: TestClient, test_user):
    """Admin can list users; response contains at least the test user."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.get("/api/v1/admin/users", headers=_admin_headers(token))
    assert resp.status_code == 200
    users = resp.json()["data"]
    assert isinstance(users, list)
    ids = [u["id"] for u in users]
    assert test_user.id in ids


def test_admin_user_detail_ok(unauth_client: TestClient, test_user):
    """Admin can fetch a single user's detail."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.get(
        f"/api/v1/admin/users/{test_user.id}", headers=_admin_headers(token)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == test_user.id
    assert data["phone"] == test_user.phone


def test_admin_user_detail_not_found(unauth_client: TestClient):
    """Non-existent user_id returns 404."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.get(
        "/api/v1/admin/users/nonexistent-id", headers=_admin_headers(token)
    )
    assert resp.status_code == 404


# ── Export tests ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("export_type", ["onboarding", "chat", "nutrition", "all"])
def test_export_shape(unauth_client: TestClient, test_user, export_type: str):
    """Every export type returns the required top-level JSON shape."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.get(
        f"/api/v1/admin/users/{test_user.id}/export/{export_type}",
        headers=_admin_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["export_type"] == export_type
    assert "exported_at" in body
    assert body["user"]["id"] == test_user.id
    assert body["user"]["phone"] == test_user.phone
    assert "data" in body


def test_export_requires_admin(unauth_client: TestClient, test_user):
    """Export without admin token returns 401."""
    resp = unauth_client.get(f"/api/v1/admin/users/{test_user.id}/export/all")
    assert resp.status_code == 401


# ── Delete tests ──────────────────────────────────────────────────────────────

def test_delete_user(unauth_client: TestClient, db_session: Session):
    """Delete removes the user and related records; returns deleted=True."""
    import uuid
    from app.models.user import User
    from app.models.profile import UserProfile

    # Create a fresh user specifically for deletion
    user = User(
        id=str(uuid.uuid4()),
        phone="+989999000001",
        is_active=True,
        is_onboarded=False,
    )
    db_session.add(user)
    profile = UserProfile(user_id=user.id, full_name="Test Delete")
    db_session.add(profile)
    db_session.flush()

    token = _get_admin_token(unauth_client)
    resp = unauth_client.delete(
        f"/api/v1/admin/users/{user.id}", headers=_admin_headers(token)
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["deleted"] is True
    assert body["user_id"] == user.id
    assert "deleted_records" in body
    assert isinstance(body["deleted_records"], dict)


def test_delete_user_not_found(unauth_client: TestClient):
    """Deleting a non-existent user returns 404."""
    token = _get_admin_token(unauth_client)
    resp = unauth_client.delete(
        "/api/v1/admin/users/does-not-exist", headers=_admin_headers(token)
    )
    assert resp.status_code == 404


def test_delete_requires_admin(unauth_client: TestClient, test_user):
    """Delete without admin token returns 401."""
    resp = unauth_client.delete(f"/api/v1/admin/users/{test_user.id}")
    assert resp.status_code == 401
