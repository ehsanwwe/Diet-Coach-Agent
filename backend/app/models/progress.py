"""
Progress models: DailyCheckIn, ProgressEntry, WeeklyReport.

DATA-06: DailyCheckIn, ProgressEntry, WeeklyReport models
BE-04: lazy="raise" on all relationships
DATA-08: created_at on all models
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DailyCheckIn(Base):
    """
    Daily wellness check-in. One record per user per day is enforced at app layer.
    check_date is the date this check-in covers.
    """

    __tablename__ = "daily_checkins"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hunger_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hunger_level_1_10: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cravings: Mapped[str | None] = mapped_column(Text, nullable=True)
    craving_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    eating_location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    planned_eating_out: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    adherence_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    adherence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="daily_checkins", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<DailyCheckIn user_id={self.user_id} date={self.check_date}>"


class ProgressEntry(Base):
    """
    Generic progress measurement.
    entry_type is free-form; value_numeric or value_text stores the measurement.
    """

    __tablename__ = "progress_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="progress_entries", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<ProgressEntry user_id={self.user_id} type={self.entry_type}>"


class WeeklyReport(Base):
    """
    Weekly aggregated report. report_data is serialized JSON.
    """

    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    report_data: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="weekly_reports", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<WeeklyReport user_id={self.user_id} week={self.week_start}>"
