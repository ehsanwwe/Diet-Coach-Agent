"""
User repository. All DB access for the User model.
SQLAlchemy 2.x select() + session.execute() only — never session.query().
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_phone(db: Session, phone: str) -> User | None:
    result = db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


def get_by_id(db: Session, user_id: str) -> User | None:
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, phone: str) -> User:
    user = User(phone=phone)
    db.add(user)
    db.flush()
    return user
