"""
Profile models: UserProfile, MedicalCondition, UserMedicalFlag, Medication, Allergy.

DATA-02: UserProfile, MedicalCondition, UserMedicalFlag, Medication, Allergy
BE-04: lazy="raise" on all relationships
DATA-08: created_at and updated_at on all models
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base):
    """
    Physical and demographic profile collected during onboarding Step 1.
    One record per user.
    """

    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profile"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wrist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    thigh_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="profile", lazy="raise")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} name={self.full_name}>"


class MedicalCondition(Base):
    """
    Reference table of known medical conditions.
    Seeded during migration or startup, not user-specific.
    """

    __tablename__ = "medical_conditions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MedicalCondition code={self.code} name={self.name}>"


class UserMedicalFlag(Base):
    """
    User-specific medical flags. Populated during onboarding Step 3.
    One record per user per condition code.
    """

    __tablename__ = "user_medical_flags"
    __table_args__ = (
        UniqueConstraint("user_id", "condition_code", name="uq_user_medical_flag"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    has_condition: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="medical_flags", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<UserMedicalFlag user_id={self.user_id} "
            f"code={self.condition_code} has={self.has_condition}>"
        )


class Medication(Base):
    """
    Medications reported by user during onboarding Step 3.
    Multiple records per user are allowed.
    """

    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="medications", lazy="raise")

    def __repr__(self) -> str:
        return f"<Medication user_id={self.user_id} name={self.name}>"


class Allergy(Base):
    """
    Food allergies and intolerances reported by user.
    Multiple records per user are allowed.
    """

    __tablename__ = "allergies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="allergies", lazy="raise")

    def __repr__(self) -> str:
        return f"<Allergy user_id={self.user_id} allergen={self.allergen}>"
