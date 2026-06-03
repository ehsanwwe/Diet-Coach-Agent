"""
SQLAlchemy 2.x synchronous database engine and session factory.

Patterns enforced here:
  - 2.0-style only: select() + session.execute()
  - check_same_thread=False required for SQLite + FastAPI
  - get_session() is a FastAPI Depends-compatible generator
  - DeclarativeBase is defined here; all models import Base from this module

BE-02: SQLite + SQLAlchemy 2.x sync + Session via Depends(get_session)
BE-04: lazy="raise" is set on individual model relationships, not here
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """All ORM models inherit from this Base."""

    pass


# Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001, ARG001
    """Enable SQLite pragmas for foreign keys and safer concurrent reads."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy Session for use in FastAPI route dependencies.

    Usage in routes:
        def my_route(db: Session = Depends(get_session)):
            result = db.execute(select(User)).scalars().all()

    Use SQLAlchemy 2.x select() statements with db.execute().
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
