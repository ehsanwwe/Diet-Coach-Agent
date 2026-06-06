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

    plan_day: Mapped["NutritionPlanDay"] = relationship(
        "NutritionPlanDay", back_populates="meals", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<NutritionPlanDayMeal day={self.plan_day_id} type={self.meal_type}>"
