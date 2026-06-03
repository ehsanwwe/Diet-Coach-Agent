"""
Lifestyle models: LifestyleProfile, FoodPreference, BehaviorProfile.

DATA-03: Lifestyle, food preference, and behavior profile models
BE-04: lazy="raise" on all relationships
DATA-08: created_at / updated_at
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class LifestyleProfile(Base):
    """
    Lifestyle data collected during onboarding Step 4.
    One record per user.
    """

    __tablename__ = "lifestyle_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_lifestyle_profile"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooking_ability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    food_budget: Mapped[str | None] = mapped_column(String(50), nullable=True)
    eating_out_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    travel_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="lifestyle_profile", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<LifestyleProfile user_id={self.user_id}>"


class FoodPreference(Base):
    """
    Food preferences and dietary restrictions from onboarding Step 5.
    JSON fields are stored as Text for SQLite compatibility.
    """

    __tablename__ = "food_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_food_preference"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    likes_iranian_food: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vegetarian: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vegan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    halal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    disliked_foods: Mapped[str | None] = mapped_column(Text, nullable=True)
    favorite_foods: Mapped[str | None] = mapped_column(Text, nullable=True)
    breakfast_habit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rice_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bread_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sweets_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tea_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    restaurant_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="food_preference", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<FoodPreference user_id={self.user_id}>"


class BehaviorProfile(Base):
    """
    Behavioral and psychological eating patterns from onboarding Step 6.
    JSON fields store lists serialized as Text.
    """

    __tablename__ = "behavior_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_behavior_profile"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emotional_eating: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    night_eating: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meal_skipping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cravings: Mapped[str | None] = mapped_column(Text, nullable=True)
    binge_history: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    diet_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_failures: Mapped[str | None] = mapped_column(Text, nullable=True)
    hunger_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    motivation_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="behavior_profile", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<BehaviorProfile user_id={self.user_id}>"
