"""
Pytest configuration and shared fixtures for backend tests.

Uses an in-memory SQLite database to avoid touching the development app.db.
SECRET_KEY is set in the environment before any app modules are imported.
"""
from __future__ import annotations

import os

# Must be set before any app imports (Settings validates SECRET_KEY at import time)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_current_user
from app.core.database import Base, get_session
from app.main import app
from app.models.user import User  # noqa: F401 — imported to register ORM metadata

# ---------------------------------------------------------------------------
# In-memory engine shared across the test session
# ---------------------------------------------------------------------------

_test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)
_TestingSessionLocal = sessionmaker(
    bind=_test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def engine():
    """Create all tables once for the entire test session."""
    # Import all models to ensure their metadata is registered with Base
    import app.models.audit  # noqa: F401
    import app.models.auth  # noqa: F401
    import app.models.chat  # noqa: F401
    import app.models.lifestyle  # noqa: F401
    import app.models.nutrition  # noqa: F401
    import app.models.profile  # noqa: F401
    import app.models.progress  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=_test_engine)
    yield _test_engine
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """
    Yield a database session. Each test gets a clean transaction that is
    rolled back after the test completes (no persistent side effects).
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create and persist a test user for use in authenticated tests."""
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        phone="+989123456789",
        is_active=True,
        is_onboarded=False,
    )
    db_session.add(user)
    db_session.flush()  # Assign id without committing
    return user


@pytest.fixture
def auth_headers():
    """Dummy auth headers — client fixture already overrides get_current_user, so headers are ignored."""
    return {"Authorization": "Bearer test-token"}


def _make_session_override(session: Session):
    """Return a FastAPI dependency override that yields the given session."""
    def override_get_session() -> Generator[Session, None, None]:
        yield session
    return override_get_session


@pytest.fixture
def client(db_session: Session, test_user: User) -> TestClient:
    """
    TestClient with:
    - get_session overridden to use the test transaction session
    - get_current_user overridden to return test_user (auth bypassed)
    """
    app.dependency_overrides[get_session] = _make_session_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(db_session: Session) -> TestClient:
    """
    TestClient with:
    - get_session overridden to use the test transaction session
    - get_current_user NOT overridden (real auth — returns 401 without token)
    """
    app.dependency_overrides[get_session] = _make_session_override(db_session)

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
