"""
Calendar models: NutritionPlanCalendar, NutritionPlanDay, NutritionPlanDayMeal.

Rolling multilingual meal plan calendar per user/locale.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
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


CALENDAR_LOCALES = ("fa", "en", "ar")
CALENDAR_STATUSES = ("active", "archived")
MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack", "other")


class NutritionPlanCalendar(Base):
    """
    Per-user per-locale meal plan calendar.
    One active calendar per user per locale at a time.
    """

    __tablename__ = "nutrition_plan_calendars"
    __table_args__ = (
        Index("ix_calendar_user_locale", "user_id", "locale"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    locale: Mapped[str] = mapped_column(String(5), nullable=False, default="fa", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="nutrition_calendars", lazy="raise"
    )
    days: Mapped[list["NutritionPlanDay"]] = relationship(
        "NutritionPlanDay",
        back_populates="calendar",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<NutritionPlanCalendar user={self.user_id} locale={self.locale} status={self.status}>"


class NutritionPlanDay(Base):
    """
    A single planned day within a calendar.
    Unique per user + plan_date + locale (no duplicate days).
    """

    __tablename__ = "nutrition_plan_days"
    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", "locale", name="uq_plan_day_user_date_locale"),
        Index("ix_plan_day_user_locale_date", "user_id", "locale", "plan_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    calendar_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("nutrition_plan_calendars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    locale: Mapped[str] = mapped_column(String(5), nullable=False, default="fa", index=True)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    hydration_goal: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Enriched day-level fields (all nullable — old rows remain valid)
    diet_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    diet_goal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    daily_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_macros: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    day_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    training_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    sleep_wake_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    wake_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sleep_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    dinner_to_sleep_gap: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hydration_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    drinks_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    cheat_meal_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    allowed_foods: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    limited_foods: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    forbidden_foods: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    medical_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    restaurant_party_travel_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplements_vitamins_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_tracking_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    adjustment_rules: Mapped[str | None] = mapped_column(Text, nullable=True)

    calendar: Mapped["NutritionPlanCalendar"] = relationship(
        "NutritionPlanCalendar", back_populates="days", lazy="raise"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="plan_days", lazy="raise"
    )
    meals: Mapped[list["NutritionPlanDayMeal"]] = relationship(
        "NutritionPlanDayMeal",
        back_populates="plan_day",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<NutritionPlanDay date={self.plan_date} locale={self.locale} user={self.user_id}>"


class NutritionPlanDayMeal(Base):
    """
    A single meal slot within a planned day.
    meal_type: breakfast | lunch | dinner | snack | other
    """

    __tablename__ = "nutrition_plan_day_meals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    plan_day_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("nutrition_plan_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(5), nullable=False, default="fa")
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    portion_guidance: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alternatives: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Enriched meal-level fields (all nullable — old rows remain valid)
    meal_slot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meal_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_window_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    time_window_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    calories_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    food_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    workout_relation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rest_day_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    drink_guidance: Mapped[str | None] = mapped_column(String(300), nullable=True)

    plan_day: Mapped["NutritionPlanDay"] = relationship(
        "NutritionPlanDay", back_populates="meals", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<NutritionPlanDayMeal day={self.plan_day_id} type={self.meal_type}>"
