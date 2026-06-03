from __future__ import annotations
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.models as _app_models  # noqa: F401 — registers all models with Base.metadata
from app.core.database import Base, get_session
from app.main import app
from app.api.dependencies import get_current_user
from app.models.user import User

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture()
def engine():
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session) -> User:
    user = User(phone="+989121234567", is_active=True, is_onboarded=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session, test_user) -> TestClient:
    def _override_get_session():
        try:
            yield db_session
        finally:
            pass

    def _override_get_current_user():
        return test_user

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.fixture()
def unauth_client(db_session) -> TestClient:
    def _override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = _override_get_session
    # Do NOT override get_current_user → real auth runs → returns 401
    yield TestClient(app)
    app.dependency_overrides.clear()
