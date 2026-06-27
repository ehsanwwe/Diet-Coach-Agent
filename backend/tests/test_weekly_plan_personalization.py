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


# ── Budget tier tests ─────────────────────────────────────────────────────────

from app.services.nutrition_memory_service import normalize_budget_tier
from app.services.weekly_plan_personalization_validator import _EXPENSIVE_TERMS


def test_normalize_budget_tier_persian():
    assert normalize_budget_tier("اقتصادی") == "economic"
    assert normalize_budget_tier("معمولی") == "standard"
    assert normalize_budget_tier("گران") == "premium"


def test_normalize_budget_tier_english():
    assert normalize_budget_tier("low_budget") == "economic"
    assert normalize_budget_tier("standard") == "standard"
    assert normalize_budget_tier("expensive") == "premium"
    assert normalize_budget_tier(None) == "unknown"
    assert normalize_budget_tier("unknown_value") == "unknown"


def _expensive_plan(locale: str = "fa") -> dict:
    return {
        "locale": locale,
        "days": [
            {
                "day_index": i + 1,
                "title": f"Day {i + 1}",
                "summary": "",
                "warnings": [],
                "meals": [
                    {
                        "meal_type": "lunch",
                        "meal_slot": "lunch",
                        "title": "Lunch: Salmon with Quinoa",
                        "description": "Grilled salmon fillet with quinoa and avocado",
                        "alternatives": ["steak salad"],
                    }
                ],
            }
            for i in range(7)
        ],
    }


def test_economic_budget_removes_expensive_foods():
    ctx = _ctx(food_budget="اقتصادی")
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for term in ("salmon", "quinoa", "avocado", "steak"):
        assert term not in text.lower(), f"Expensive term '{term}' still in economic plan"


def test_economic_budget_replacement_is_allergy_safe():
    ctx = _ctx(food_budget="اقتصادی", allergies=["egg"])
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for egg_term in ("تخم‌مرغ", "تخم مرغ", "نیمرو", "omelet", "egg"):
        assert egg_term not in text, f"Allergen '{egg_term}' appeared after economic budget replacement"


def test_economic_budget_sets_budget_tier_on_days():
    ctx = _ctx(food_budget="اقتصادی")
    plan = _plan_with_meal("صبحانه سالم", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        assert day.get("budget_tier") == "economic"
        assert day.get("budget_guidance")
        assert day.get("shopping_notes")


def test_standard_budget_does_not_over_restrict():
    ctx = _ctx(food_budget="معمولی")
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": i + 1,
                "title": f"Day {i + 1}",
                "summary": "",
                "warnings": [],
                "meals": [
                    {
                        "meal_type": "lunch",
                        "meal_slot": "lunch",
                        "title": "Lunch: Chicken with rice",
                        "description": "Steamed chicken with rice and salad",
                        "alternatives": [],
                    }
                ],
            }
            for i in range(7)
        ],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        assert day.get("budget_tier") == "standard"
    text = _all_meal_text(result)
    assert "chicken" in text


def test_premium_budget_keeps_expensive_foods():
    ctx = _ctx(food_budget="گران")
    plan = _expensive_plan(locale="en")
    result = validate_and_sanitize(plan, ctx, locale="en")
    text = _all_meal_text(result)
    assert "salmon" in text or "quinoa" in text, "Premium budget should keep expensive foods"
    for day in result["days"]:
        assert day.get("budget_tier") == "premium"


def test_budget_tier_field_present_all_days():
    ctx = _ctx(food_budget="معمولی")
    plan = _plan_with_meal("Breakfast: Oatmeal", locale="en")
    result = validate_and_sanitize(plan, ctx, locale="en")
    assert len(result["days"]) == 7
    for day in result["days"]:
        assert "budget_tier" in day
        assert "budget_guidance" in day
        assert "shopping_notes" in day


# ── Validator hardening: allergen-safe replacement candidates ─────────────────

def test_economic_tree_nut_allergy_safe_replacement():
    ctx = _ctx(food_budget="اقتصادی", allergies=["tree_nut"])
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for term in ("گردو", "بادام", "پسته", "آجیل", "walnut", "almond", "cashew", "pistachio"):
        assert term not in text, f"Tree-nut term '{term}' found after economic+tree_nut replacement"


def test_economic_lactose_allergy_safe_replacement():
    ctx = _ctx(food_budget="اقتصادی", allergies=["lactose"])
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for term in ("ماست", "پنیر", "شیر", "yogurt", "cheese", "milk", "dairy"):
        assert term not in text, f"Dairy term '{term}' found after economic+lactose replacement"


def test_economic_gluten_allergy_safe_replacement():
    ctx = _ctx(food_budget="اقتصادی", allergies=["gluten"])
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = _all_meal_text(result)
    for term in ("نان", "گندم", "wheat", "gluten", "pasta"):
        assert term not in text, f"Gluten term '{term}' found after economic+gluten replacement"


def test_allergen_replaced_meals_have_non_empty_food_items():
    ctx = _ctx(allergies=["egg"])
    plan = _plan_with_meal("صبحانه: تخم‌مرغ آب‌پز", "نیمرو", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        for meal in day.get("meals", []):
            items = meal.get("food_items") or []
            assert len(items) > 0, f"Replaced meal has empty food_items: {meal.get('title')}"
            for item in items:
                assert item.get("amount"), f"food_item missing amount: {item}"
                assert item.get("unit"), f"food_item missing unit: {item}"


def test_budget_replaced_meals_have_non_empty_food_items():
    ctx = _ctx(food_budget="اقتصادی")
    plan = _expensive_plan(locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        for meal in day.get("meals", []):
            items = meal.get("food_items") or []
            assert len(items) > 0, f"Budget-replaced meal has empty food_items: {meal.get('title')}"
            for item in items:
                assert item.get("amount"), f"food_item missing amount: {item}"
                assert item.get("unit"), f"food_item missing unit: {item}"
