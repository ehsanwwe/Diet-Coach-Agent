"""
NutritionRepository: DB access for NutritionGoal, NutritionPlan,
NutritionPlanMeal, and MealEntry.

Uses SQLAlchemy 2.x select() + session.execute() throughout.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.nutrition import NutritionGoal, NutritionPlan, NutritionPlanMeal
from app.models.chat import MealEntry


# ─── NutritionGoal ────────────────────────────────────────────────────────────

def get_nutrition_goal(db: Session, user_id: str) -> NutritionGoal | None:
    result = db.execute(
        select(NutritionGoal).where(NutritionGoal.user_id == user_id)
    )
    return result.scalar_one_or_none()


def upsert_nutrition_goal(
    db: Session,
    user_id: str,
    goal_type: str,
    target_calories: int | None = None,
    notes: str | None = None,
) -> NutritionGoal:
    goal = get_nutrition_goal(db, user_id)
    if goal is None:
        goal = NutritionGoal(user_id=user_id)
        db.add(goal)
    goal.goal_type = goal_type
    goal.target_calories = target_calories
    goal.notes = notes
    db.flush()
    return goal


# ─── NutritionPlan ────────────────────────────────────────────────────────────

def get_active_plan(db: Session, user_id: str) -> NutritionPlan | None:
    result = db.execute(
        select(NutritionPlan)
        .where(
            NutritionPlan.user_id == user_id,
            NutritionPlan.status == "active",
        )
        .order_by(NutritionPlan.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def archive_active_plans(db: Session, user_id: str) -> None:
    """Archive all currently active plans before generating a new one."""
    result = db.execute(
        select(NutritionPlan).where(
            NutritionPlan.user_id == user_id,
            NutritionPlan.status == "active",
        )
    )
    for plan in result.scalars().all():
        plan.status = "archived"
    db.flush()


def create_plan(
    db: Session,
    user_id: str,
    *,
    title: str,
    description: str | None,
    plan_metadata: dict | None,
    generated_by: str,
) -> NutritionPlan:
    plan = NutritionPlan(
        user_id=user_id,
        title=title,
        description=description,
        plan_metadata=json.dumps(plan_metadata, ensure_ascii=False) if plan_metadata else None,
        status="active",
        generated_by=generated_by,
    )
    db.add(plan)
    db.flush()
    return plan


def add_plan_meal(
    db: Session,
    plan_id: str,
    *,
    meal_time: str,
    name: str,
    description: str | None,
    calories_estimate: int | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    notes: str | None,
    order_index: int,
) -> NutritionPlanMeal:
    meal = NutritionPlanMeal(
        plan_id=plan_id,
        meal_time=meal_time,
        name=name,
        description=description,
        calories_estimate=calories_estimate,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        notes=notes,
        order_index=order_index,
    )
    db.add(meal)
    db.flush()
    return meal


def get_plan_meals(db: Session, plan_id: str) -> list[NutritionPlanMeal]:
    result = db.execute(
        select(NutritionPlanMeal)
        .where(NutritionPlanMeal.plan_id == plan_id)
        .order_by(NutritionPlanMeal.order_index)
    )
    return list(result.scalars().all())


def update_plan_metadata(
    db: Session,
    plan: NutritionPlan,
    *,
    description: str | None,
    plan_metadata: dict | None,
) -> NutritionPlan:
    plan.description = description
    plan.plan_metadata = (
        json.dumps(plan_metadata, ensure_ascii=False) if plan_metadata else None
    )
    db.flush()
    return plan


def get_plan_metadata(plan: NutritionPlan) -> dict:
    """Safely decode the plan_metadata JSON field."""
    if not plan.plan_metadata:
        return {}
    try:
        return json.loads(plan.plan_metadata)
    except (json.JSONDecodeError, TypeError):
        return {}


# ─── MealEntry ────────────────────────────────────────────────────────────────

def create_meal_entry(
    db: Session,
    user_id: str,
    *,
    meal_time: str | None,
    description: str,
    analysis_result: dict | None,
    logged_at: datetime,
) -> MealEntry:
    entry = MealEntry(
        user_id=user_id,
        meal_time=meal_time,
        description=description,
        analysis_result=(
            json.dumps(analysis_result, ensure_ascii=False)
            if analysis_result
            else None
        ),
        logged_at=logged_at,
    )
    db.add(entry)
    db.flush()
    return entry
