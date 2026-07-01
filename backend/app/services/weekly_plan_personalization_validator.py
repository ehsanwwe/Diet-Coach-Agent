"""Technical normalization for LLM-generated weekly plans.

Food safety and quality defects are reported by the quality evaluator and repaired
by the LLM. This module deliberately does not select, remove, or replace foods.
"""
from __future__ import annotations

from typing import Any

from app.services.nutrition_memory_service import NutritionMemoryContext, normalize_budget_tier

MEAL_ORDER = [
    "breakfast", "morning_snack", "lunch", "pre_workout", "post_workout",
    "afternoon_snack", "dinner", "optional_evening_snack", "cheating_date",
    "snack", "other",
]


def _infer_slot_from_time(slot: str, start: str | None) -> str:
    if slot != "snack" or not start:
        return slot
    try:
        hour = int(start.split(":", 1)[0])
    except (TypeError, ValueError):
        return slot
    if hour < 12:
        return "morning_snack"
    if hour < 18:
        return "afternoon_snack"
    return "optional_evening_snack"


def canonical_meal_order_value(slot: str) -> int:
    """Return the zero-based canonical rank for a meal slot."""
    try:
        return MEAL_ORDER.index(slot)
    except ValueError:
        return len(MEAL_ORDER)


def _meal_order_key(meal: dict) -> int:
    return canonical_meal_order_value(str(meal.get("meal_slot") or meal.get("meal_type") or "other"))


def sort_meals_canonically(meals: list[dict]) -> list[dict]:
    """Return copied meals in canonical order without changing food content."""
    return sorted((dict(meal) for meal in meals), key=_meal_order_key)


def _normalize_legacy_cheating(meal: dict) -> dict:
    slot = meal.get("meal_slot") or meal.get("meal_type")
    if slot != "controlled_cheating":
        return meal
    return {**meal, "meal_type": "cheating_date", "meal_slot": "cheating_date", "title": "Cheating Date"}


def collect_user_visible_text(plan: dict) -> str:
    """Collect strings recursively for diagnostics and compatibility tests."""
    parts: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(plan)
    return " ".join(parts).lower()


def validate_and_sanitize(plan_data: dict, ctx: NutritionMemoryContext, locale: str = "fa") -> dict:
    """Apply harmless structural normalization only.

    It does not make an unsafe plan safe. Callers must evaluate and reject/repair
    blocking issues before persistence.
    """
    days: list[dict] = []
    for raw_day in list(plan_data.get("days") or [])[:7]:
        day = dict(raw_day)
        meals: list[dict] = []
        for raw_meal in list(day.get("meals") or []):
            meal = dict(raw_meal)
            if not meal.get("meal_slot") and meal.get("meal_type"):
                meal["meal_slot"] = meal["meal_type"]
            meal["meal_slot"] = _infer_slot_from_time(
                str(meal.get("meal_slot") or meal.get("meal_type") or "other"),
                meal.get("time_window_start"),
            )
            meal = _normalize_legacy_cheating(meal)
            meals.append(meal)
        meals = sort_meals_canonically(meals)
        for index, meal in enumerate(meals, start=1):
            meal["meal_order"] = index
        day["meals"] = meals
        if not day.get("budget_tier"):
            day["budget_tier"] = normalize_budget_tier(ctx.food_budget or ctx.budget_tier)
        days.append(day)
    return {**plan_data, "days": days}
