"""
User model: the central FK target for all other models.

DATA-01: User model
BE-04: All relationships use lazy="raise"
DATA-08: created_at, updated_at on all models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.audit import AuditLog, UserLanguagePreference
    from app.models.auth import AuthOTP
    from app.models.chat import AudioMessage, ChatSession, MealEntry
    from app.models.lifestyle import BehaviorProfile, FoodPreference, LifestyleProfile
    from app.models.calendar import NutritionPlanCalendar, NutritionPlanDay
    from app.models.nutrition import (
        NutritionGoal,
        NutritionPlan,
        NutritionRiskAssessment,
    )
    from app.models.profile import (
        Allergy,
        Medication,
        UserMedicalFlag,
        UserProfile,
    )
    from app.models.progress import DailyCheckIn, ProgressEntry, WeeklyReport


class User(Base):
    """
    Core user record. Phone number is the sole identifier.
    All other data hangs off this via FK.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    otps: Mapped[list["AuthOTP"]] = relationship(
        "AuthOTP", back_populates="user", lazy="raise"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", lazy="raise"
    )
    language_preference: Mapped["UserLanguagePreference | None"] = relationship(
        "UserLanguagePreference", back_populates="user", uselist=False, lazy="raise"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False, lazy="raise"
    )
    medical_flags: Mapped[list["UserMedicalFlag"]] = relationship(
        "UserMedicalFlag", back_populates="user", lazy="raise"
    )
    medications: Mapped[list["Medication"]] = relationship(
        "Medication", back_populates="user", lazy="raise"
    )
    allergies: Mapped[list["Allergy"]] = relationship(
        "Allergy", back_populates="user", lazy="raise"
    )
    lifestyle_profile: Mapped["LifestyleProfile | None"] = relationship(
        "LifestyleProfile", back_populates="user", uselist=False, lazy="raise"
    )
    food_preference: Mapped["FoodPreference | None"] = relationship(
        "FoodPreference", back_populates="user", uselist=False, lazy="raise"
    )
    behavior_profile: Mapped["BehaviorProfile | None"] = relationship(
        "BehaviorProfile", back_populates="user", uselist=False, lazy="raise"
    )
    nutrition_goals: Mapped[list["NutritionGoal"]] = relationship(
        "NutritionGoal", back_populates="user", lazy="raise"
    )
    risk_assessments: Mapped[list["NutritionRiskAssessment"]] = relationship(
        "NutritionRiskAssessment", back_populates="user", lazy="raise"
    )
    nutrition_plans: Mapped[list["NutritionPlan"]] = relationship(
        "NutritionPlan", back_populates="user", lazy="raise"
    )
    nutrition_calendars: Mapped[list["NutritionPlanCalendar"]] = relationship(
        "NutritionPlanCalendar", back_populates="user", lazy="raise"
    )
    plan_days: Mapped[list["NutritionPlanDay"]] = relationship(
        "NutritionPlanDay", back_populates="user", lazy="raise"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="user", lazy="raise"
    )
    meal_entries: Mapped[list["MealEntry"]] = relationship(
        "MealEntry", back_populates="user", lazy="raise"
    )
    audio_messages: Mapped[list["AudioMessage"]] = relationship(
        "AudioMessage", back_populates="user", lazy="raise"
    )
    daily_checkins: Mapped[list["DailyCheckIn"]] = relationship(
        "DailyCheckIn", back_populates="user", lazy="raise"
    )
    progress_entries: Mapped[list["ProgressEntry"]] = relationship(
        "ProgressEntry", back_populates="user", lazy="raise"
    )
    weekly_reports: Mapped[list["WeeklyReport"]] = relationship(
        "WeeklyReport", back_populates="user", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone}>"
