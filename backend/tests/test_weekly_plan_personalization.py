"""Tests for weekly plan personalization validator — allergy enforcement and ordering."""
from __future__ import annotations

import pytest

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.weekly_plan_personalization_validator import validate_and_sanitize, _build_forbidden_terms


def _ctx(**kwargs) -> NutritionMemoryContext:
    return NutritionMemoryContext(user_id="test-user", **kwargs)


def _plan_with_meal(title: str, description: str = "", locale: str = "fa") -> dict:
    return {
        "locale": locale,
        "days": [
            {
                "day_index": i + 1,
                "title": f"Day {i + 1}",
                "summary": "test",
                "warnings": [],
                "meals": [
                    {
                        "meal_type": "breakfast",
                        "meal_slot": "breakfast",
                        "title": title,
                        "description": description,
                        "alternatives": [],
                    }
                ],
            }
            for i in range(7)
        ],
    }


def _all_meal_text(plan: dict) -> str:
    parts = []
    for day in plan.get("days", []):
        for meal in day.get("meals", []):
            for field in ("title", "description", "portion_guidance", "preparation_notes"):
                v = meal.get(field) or ""
                parts.append(v)
            for alt in meal.get("alternatives") or []:
                parts.append(alt)
    return " ".join(parts).lower()


# ── Allergy enforcement ────────────────────────────────────────────────────────

def test_egg_allergy_blocks_persian_terms():
    ctx = _ctx(allergies=["egg"])
    plan = _plan_with_meal("صبحانه: تخم‌مرغ آب‌پز", "نیمرو با سبزی", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for term in ("تخم‌مرغ", "نیمرو", "املت", "تخم مرغ"):
        assert term not in text, f"Found forbidden egg term '{term}' in plan"


def test_egg_allergy_blocks_english_terms():
    ctx = _ctx(allergies=["egg"])
    plan = _plan_with_meal("Breakfast: Veggie Omelet", "Two eggs scrambled", locale="en")
    result = validate_and_sanitize(plan, ctx, locale="en")
    text = _all_meal_text(result)
    for term in ("omelet", "omelette", "eggs", "scrambled"):
        assert term not in text, f"Found forbidden egg term '{term}'"


def test_egg_allergy_blocks_arabic_terms():
    ctx = _ctx(allergies=["egg"])
    plan = _plan_with_meal("الفطور: عجة بالخضار", "بيضتان مع فلفل", locale="ar")
    result = validate_and_sanitize(plan, ctx, locale="ar")
    text = _all_meal_text(result)
    for term in ("عجة", "بيض", "بيضتان"):
        assert term not in text, f"Found forbidden Arabic egg term '{term}'"


def test_no_allergy_leaves_eggs_intact():
    ctx = _ctx(allergies=[])
    plan = _plan_with_meal("Breakfast: Boiled Eggs", "Two eggs", locale="en")
    result = validate_and_sanitize(plan, ctx, locale="en")
    text = _all_meal_text(result)
    assert "eggs" in text


def test_disliked_foods_excluded():
    ctx = _ctx(disliked_foods=["بادمجان"])
    plan = _plan_with_meal("شام: کشک بادمجان", "بادمجان کبابی", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    assert "بادمجان" not in text


# ── Sorting ───────────────────────────────────────────────────────────────────

def test_meals_sorted_by_fixed_order():
    ctx = _ctx()
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1,
                "title": "Day 1",
                "summary": "",
                "warnings": [],
                "meals": [
                    {"meal_slot": "dinner", "meal_type": "dinner", "title": "Dinner", "description": "", "alternatives": []},
                    {"meal_slot": "breakfast", "meal_type": "breakfast", "title": "Breakfast", "description": "", "alternatives": []},
                    {"meal_slot": "lunch", "meal_type": "lunch", "title": "Lunch", "description": "", "alternatives": []},
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    slots = [m.get("meal_slot") or m.get("meal_type") for m in result["days"][0]["meals"]]
    assert slots == ["breakfast", "lunch", "dinner"], f"Unexpected order: {slots}"


# ── Clinical review ───────────────────────────────────────────────────────────

def test_clinical_review_user_gets_warning():
    ctx = _ctx(clinical_review_required=True)
    plan = _plan_with_meal("صبحانه سالم", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        warnings = day.get("warnings") or []
        assert any("پزشک" in w for w in warnings), "Expected clinical warning in day warnings"


# ── Mock fallback safety ──────────────────────────────────────────────────────

def test_mock_fallback_is_safe_with_egg_allergy():
    from app.services.mock_ai_provider import generate_safe_week_mock
    ctx = _ctx(allergies=["egg"])
    result = generate_safe_week_mock(ctx, "fa")
    text = _all_meal_text(result)
    for term in ("تخم‌مرغ", "نیمرو", "اُملت", "تخم مرغ", "تخممرغ"):
        assert term not in text, f"Mock fallback contains egg term '{term}'"


def test_forbidden_terms_built_correctly():
    ctx = _ctx(allergies=["egg"])
    terms = _build_forbidden_terms(ctx)
    assert "نیمرو" in terms
    assert "omelet" in terms
    assert "عجة" in terms
