"""
Nutrition models: NutritionGoal, NutritionRiskAssessment,
NutritionPlan, NutritionPlanMeal.

DATA-04: Nutrition goal, risk assessment, plan, and meal models
BE-04: lazy="raise" on all relationships
DATA-08: created_at / updated_at
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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


GOAL_TYPES = (
    "weight_loss",
    "weight_gain",
    "muscle_gain",
    "healthy_eating",
    "diabetes_support",
    "fatty_liver_support",
    "pcos_support",
    "digestive_support",
    "sports_nutrition",
    "pregnancy_caution",
    "daily_companion",
)

RISK_LEVELS = ("low", "medium", "high", "clinical_review_required")

PLAN_STATUSES = ("active", "archived")

GENERATED_BY_VALUES = ("mock", "openclaw")


class NutritionGoal(Base):
    """
    User's primary nutrition goal. One active record per user.
    goal_type is one of GOAL_TYPES; validated at app layer.
    """

    __tablename__ = "nutrition_goals"
    __table_args__ = (UniqueConstraint("user_id", name="uq_nutrition_goal"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="nutrition_goals", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<NutritionGoal user_id={self.user_id} type={self.goal_type}>"


class NutritionRiskAssessment(Base):
    """
    Safety risk assessment result. Multiple records per user.
    risk_level is one of RISK_LEVELS.
    """

    __tablename__ = "nutrition_risk_assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)
    flags_triggered: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="risk_assessments", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<NutritionRiskAssessment user_id={self.user_id} level={self.risk_level}>"


class NutritionPlan(Base):
    """
    A generated nutrition plan. Multiple plans per user; status tracks active/archived.
    generated_by indicates whether this was from mock or OpenClaw.
    """

    __tablename__ = "nutrition_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    generated_by: Mapped[str] = mapped_column(String(20), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="nutrition_plans", lazy="raise"
    )
    meals: Mapped[list["NutritionPlanMeal"]] = relationship(
        "NutritionPlanMeal", back_populates="plan", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<NutritionPlan id={self.id} user_id={self.user_id} status={self.status}>"


class NutritionPlanMeal(Base):
    """
    Individual meal in a NutritionPlan. Multiple meals per plan.
    meal_time is one of: breakfast, lunch, dinner, snack.
    """

    __tablename__ = "nutrition_plan_meals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("nutrition_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meal_time: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    calories_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    plan: Mapped["NutritionPlan"] = relationship(
        "NutritionPlan", back_populates="meals", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<NutritionPlanMeal plan_id={self.plan_id} "
            f"meal_time={self.meal_time} name={self.name}>"
        )
