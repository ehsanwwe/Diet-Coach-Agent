"""Tests for diet quality gates — Cheating Date injection and premium Persian lunches."""
from __future__ import annotations

import pytest

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.weekly_plan_personalization_validator import (
    validate_and_sanitize,
    _inject_cheating_date,
    _enforce_premium_persian_lunches,
    _lunch_is_premium_protein,
)


def _ctx(**kwargs) -> NutritionMemoryContext:
    return NutritionMemoryContext(user_id="test-user", **kwargs)


def _make_7_day_plan(meals_per_day=None, locale="fa") -> dict:
    """Build a minimal 7-day plan dict for testing."""
    days = []
    for i in range(7):
        day_meals = meals_per_day[i] if meals_per_day else [
            {"meal_type": "breakfast", "meal_slot": "breakfast", "title": "صبحانه", "description": "", "alternatives": []},
            {"meal_type": "lunch", "meal_slot": "lunch", "title": "ناهار: عدسی", "description": "عدسی با برنج", "alternatives": []},
            {"meal_type": "dinner", "meal_slot": "dinner", "title": "شام", "description": "", "alternatives": []},
        ]
        days.append({
            "day_index": i + 1,
            "title": f"Day {i + 1}",
            "summary": "test",
            "warnings": [],
            "meals": day_meals,
        })
    return {"locale": locale, "days": days}


def _meals_with_type(days: list[dict], meal_type: str) -> list[dict]:
    found = []
    for day in days:
        for meal in day.get("meals") or []:
            if (meal.get("meal_type") or meal.get("meal_slot") or "") == meal_type:
                found.append(meal)
    return found


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: cheating_date injected on day 6 when no cheat meal exists
# ─────────────────────────────────────────────────────────────────────────────
def test_cheating_date_injected_on_day_6():
    plan = _make_7_day_plan()
    result = _inject_cheating_date(plan["days"], "fa")
    cheat_meals = _meals_with_type(result, "cheating_date")
    assert len(cheat_meals) == 1
    assert cheat_meals[0]["title"] == "Cheating Date"
    # Should be on day 6 (index 5)
    day6_meals = result[5]["meals"]
    cheat_in_day6 = [m for m in day6_meals if (m.get("meal_type") or "") == "cheating_date"]
    assert len(cheat_in_day6) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: controlled_cheating is normalised to cheating_date
# ─────────────────────────────────────────────────────────────────────────────
def test_controlled_cheating_normalised_to_cheating_date():
    days_with_old = []
    for i in range(7):
        meals = [{"meal_type": "breakfast", "title": "B", "alternatives": []}]
        if i == 5:
            meals.append({
                "meal_type": "controlled_cheating",
                "meal_slot": "controlled_cheating",
                "title": "چیتینگ کنترل‌شده",
                "description": "old style",
                "alternatives": [],
            })
        days_with_old.append({"day_index": i + 1, "title": f"D{i+1}", "summary": "", "warnings": [], "meals": meals})

    result = _inject_cheating_date(days_with_old, "fa")
    cheat_meals = _meals_with_type(result, "cheating_date")
    old_meals = _meals_with_type(result, "controlled_cheating")

    assert len(old_meals) == 0, "controlled_cheating must be gone"
    assert len(cheat_meals) == 1
    assert cheat_meals[0]["title"] == "Cheating Date"


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: cheating_date not duplicated if already present
# ─────────────────────────────────────────────────────────────────────────────
def test_no_duplicate_cheating_date():
    days = _make_7_day_plan()["days"]
    # Inject once
    days = _inject_cheating_date(days, "fa")
    # Inject again
    days = _inject_cheating_date(days, "fa")
    cheat_meals = _meals_with_type(days, "cheating_date")
    assert len(cheat_meals) == 1, "Should not duplicate Cheating Date"


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: premium Persian plan gets ≥5 premium-protein lunches
# ─────────────────────────────────────────────────────────────────────────────
def test_premium_persian_lunches_enforced():
    # All 7 lunches are economic (عدسی, آش, لوبیا, etc.)
    economic_lunches = [
        {"meal_type": "lunch", "meal_slot": "lunch", "title": f"ناهار: عدسی {i}", "description": "عدسی", "alternatives": []}
        for i in range(7)
    ]
    days = []
    for i in range(7):
        days.append({
            "day_index": i + 1,
            "title": f"D{i+1}",
            "summary": "",
            "warnings": [],
            "meals": [
                {"meal_type": "breakfast", "title": "B", "alternatives": []},
                economic_lunches[i],
                {"meal_type": "dinner", "title": "D", "alternatives": []},
            ],
        })
    result = _enforce_premium_persian_lunches(days)
    lunches = _meals_with_type(result, "lunch")
    premium_count = sum(1 for m in lunches if _lunch_is_premium_protein(m))
    assert premium_count >= 5, f"Expected ≥5 premium lunches, got {premium_count}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: economic plan is NOT upgraded to premium lunches
# ─────────────────────────────────────────────────────────────────────────────
def test_economic_plan_not_touched_by_premium_gate():
    plan = _make_7_day_plan()
    ctx = _ctx(food_budget="low")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    lunches = _meals_with_type(result["days"], "lunch")
    # At least one economic lunch must survive (عدسی)
    economic_still_there = any("عدس" in (m.get("title") or "") for m in lunches)
    assert economic_still_there, "Economic plan lunches should not be replaced by premium gate"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: validate_and_sanitize always produces cheating_date in 7-day plan
# ─────────────────────────────────────────────────────────────────────────────
def test_validate_and_sanitize_injects_cheating_date():
    plan = _make_7_day_plan()
    ctx = _ctx(food_budget="high")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    cheat_meals = _meals_with_type(result["days"], "cheating_date")
    assert len(cheat_meals) >= 1, "validate_and_sanitize must inject a Cheating Date meal"
    assert cheat_meals[0]["title"] == "Cheating Date"
