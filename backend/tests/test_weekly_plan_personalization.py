"""Tests for weekly plan personalization validator — allergy enforcement and ordering."""
from __future__ import annotations

import pytest

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.weekly_plan_personalization_validator import (
    validate_and_sanitize,
    _build_forbidden_terms,
    collect_user_visible_text,
    canonical_meal_order_value,
    sort_meals_canonically,
    MEAL_ORDER,
)


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
            # cheating_date is a meta-meal (flexible dinner out) — no specific food_items
            if (meal.get("meal_type") or meal.get("meal_slot") or "") == "cheating_date":
                continue
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
            # cheating_date is a meta-meal (flexible dinner out) — no specific food_items
            if (meal.get("meal_type") or meal.get("meal_slot") or "") == "cheating_date":
                continue
            items = meal.get("food_items") or []
            assert len(items) > 0, f"Budget-replaced meal has empty food_items: {meal.get('title')}"
            for item in items:
                assert item.get("amount"), f"food_item missing amount: {item}"
                assert item.get("unit"), f"food_item missing unit: {item}"


# ── Persian allergy phrase normalization ──────────────────────────────────────

def test_persian_gluten_phrase_allergies():
    ctx = _ctx(allergies=["حساسیت به گلوتن"])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "رژیم حاوی نان و گندم",
                "warnings": [], "budget_guidance": "خرید نان سبوس‌دار توصیه می‌شود",
                "shopping_notes": "آرد، ماکارونی، رشته فرنگی",
                "meals": [
                    {
                        "meal_type": "breakfast", "meal_slot": "breakfast",
                        "title": "صبحانه: نان و کره", "description": "نان سبوس‌دار با کره",
                        "alternatives": ["گندم با شیر"],
                        "food_items": [{"name": "نان سبوس‌دار", "amount": "60", "unit": "گرم", "calories_estimate": 150}],
                    }
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = collect_user_visible_text(result)
    for term in ("نان", "آرد", "گندم", "گلوتن", "ماکارونی", "رشته", "bread", "wheat", "pasta", "flour"):
        assert term not in text, f"Gluten term '{term}' still present after Persian phrase allergy"


def test_persian_dairy_phrase_allergies():
    ctx = _ctx(allergies=["حساسیت به لبنیات"])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "برنامه با ماست و پنیر",
                "warnings": [], "shopping_notes": "شیر، ماست، پنیر، دوغ",
                "cheat_meal_guidance": "می‌توانید ماست بخورید",
                "meals": [
                    {
                        "meal_type": "breakfast", "meal_slot": "breakfast",
                        "title": "صبحانه: ماست با میوه", "description": "ماست کم‌چرب با میوه فصلی",
                        "alternatives": ["پنیر با نان"],
                        "food_items": [{"name": "ماست کم‌چرب", "amount": "200", "unit": "گرم", "calories_estimate": 100}],
                    }
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = collect_user_visible_text(result)
    for term in ("ماست", "پنیر", "شیر", "لبنیات", "yogurt", "cheese", "milk", "dairy"):
        assert term not in text, f"Dairy term '{term}' still present after حساسیت به لبنیات"


def test_lactose_intolerance_phrase_allergies():
    ctx = _ctx(allergies=["عدم تحمل لاکتوز"])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "", "warnings": [],
                "supplements_vitamins_guidance": "مصرف کلسیم از شیر توصیه می‌شود",
                "meals": [
                    {
                        "meal_type": "lunch", "meal_slot": "lunch",
                        "title": "ناهار: مرغ با ماست", "description": "مرغ با ماست یونانی",
                        "alternatives": ["دوغ با خیار"],
                        "food_items": [
                            {"name": "مرغ آب‌پز", "amount": "120", "unit": "گرم", "calories_estimate": 200},
                            {"name": "ماست یونانی", "amount": "100", "unit": "گرم", "calories_estimate": 80},
                        ],
                    }
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = collect_user_visible_text(result)
    for term in ("ماست", "دوغ", "شیر", "لاکتوز", "لبنیات", "yogurt", "cheese", "milk", "dairy", "kefir"):
        assert term not in text, f"Lactose term '{term}' still present after عدم تحمل لاکتوز"


# ── Day-level recursive repair ────────────────────────────────────────────────

def test_day_level_recursive_repair():
    ctx = _ctx(allergies=["حساسیت به گلوتن", "حساسیت به لبنیات"])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1",
                "summary": "روز با نان و ماست شروع کنید",
                "budget_guidance": "خرید نان سبوس‌دار و ماست اقتصادی است",
                "shopping_notes": "پنیر، شیر، آرد گندم، ماکارونی",
                "cheat_meal_guidance": "می‌توانید پاستا بخورید",
                "restaurant_party_travel_guidance": "نان تازه انتخاب کنید",
                "supplements_vitamins_guidance": "کلسیم از شیر و ماست تامین کنید",
                "warnings": [],
                "meals": [{"meal_type": "breakfast", "meal_slot": "breakfast", "title": "صبحانه سالم", "description": "میوه", "alternatives": [], "food_items": [{"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 60}]}],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = collect_user_visible_text(result)
    for term in ("نان", "ماست", "پنیر", "شیر", "آرد", "گندم", "ماکارونی", "پاستا"):
        assert term not in text, f"Forbidden term '{term}' still in day-level fields"


def test_meal_level_recursive_repair():
    ctx = _ctx(allergies=["لبنیات"])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "", "warnings": [],
                "meals": [
                    {
                        "meal_type": "lunch", "meal_slot": "lunch",
                        "title": "ناهار: مرغ با سبزیجات",
                        "description": "مرغ سالم",
                        "drink_guidance": "با شیر کم‌چرب بنوشید",
                        "preparation_notes": "با ماست یونانی مزه‌دار کنید",
                        "alternatives": ["سالاد با پنیر", "ماست با میوه"],
                        "food_items": [
                            {"name": "مرغ آب‌پز", "amount": "120", "unit": "گرم", "calories_estimate": 200},
                            {"name": "یوگورت کم‌چرب", "amount": "100", "unit": "گرم", "calories_estimate": 80},
                        ],
                    }
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    text = collect_user_visible_text(result)
    for term in ("شیر", "ماست", "پنیر", "yogurt", "milk", "cheese", "dairy", "لبنیات"):
        assert term not in text, f"Dairy term '{term}' remains in meal-level fields"
    # Replaced meal must still have valid food_items (cheating_date is exempt)
    for day in result["days"]:
        for meal in day.get("meals", []):
            if (meal.get("meal_type") or meal.get("meal_slot") or "") == "cheating_date":
                continue
            items = meal.get("food_items") or []
            assert len(items) > 0, "Replaced meal has empty food_items"
            for item in items:
                assert item.get("amount"), "food_item missing amount"
                assert item.get("unit"), "food_item missing unit"


# ── Budget guidance allergen safety ───────────────────────────────────────────

def test_economic_gluten_budget_guidance_and_shopping_notes():
    ctx = _ctx(food_budget="اقتصادی", allergies=["gluten"])
    plan = _plan_with_meal("صبحانه سالم", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        bg = (day.get("budget_guidance") or "").lower()
        sn = (day.get("shopping_notes") or "").lower()
        for term in ("نان", "آرد", "گندم", "ماکارونی", "رشته", "bread", "wheat", "pasta", "flour"):
            assert term not in bg, f"Gluten term '{term}' in budget_guidance: {bg[:100]}"
            assert term not in sn, f"Gluten term '{term}' in shopping_notes: {sn[:100]}"


def test_economic_lactose_budget_guidance_and_shopping_notes():
    ctx = _ctx(food_budget="اقتصادی", allergies=["lactose"])
    plan = _plan_with_meal("صبحانه سالم", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        bg = (day.get("budget_guidance") or "").lower()
        sn = (day.get("shopping_notes") or "").lower()
        for term in ("ماست", "پنیر", "شیر", "دوغ", "کشک", "yogurt", "cheese", "milk", "dairy"):
            assert term not in bg, f"Dairy term '{term}' in budget_guidance"
            assert term not in sn, f"Dairy term '{term}' in shopping_notes"


def test_standard_budget_lactose_allergy_shopping_notes_safe():
    ctx = _ctx(food_budget="معمولی", allergies=["lactose"])
    plan = _plan_with_meal("صبحانه سالم", locale="fa")
    result = validate_and_sanitize(plan, ctx, locale="fa")
    for day in result["days"]:
        sn = (day.get("shopping_notes") or "").lower()
        for term in ("ماست", "پنیر", "شیر", "لبنیات", "yogurt", "cheese", "milk", "dairy"):
            assert term not in sn, f"Dairy term '{term}' in standard-budget shopping_notes"


# ── Canonical meal ordering ───────────────────────────────────────────────────

def test_canonical_meal_order_and_meal_order_values():
    ctx = _ctx()
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "", "warnings": [],
                "meals": [
                    {"meal_type": "lunch", "meal_slot": "lunch", "title": "Lunch", "description": "", "alternatives": []},
                    {"meal_type": "afternoon_snack", "meal_slot": "afternoon_snack", "title": "Afternoon Snack", "description": "", "alternatives": []},
                    {"meal_type": "breakfast", "meal_slot": "breakfast", "title": "Breakfast", "description": "", "alternatives": []},
                    {"meal_type": "dinner", "meal_slot": "dinner", "title": "Dinner", "description": "", "alternatives": []},
                ],
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    day_meals = result["days"][0]["meals"]
    slots = [m.get("meal_slot") or m.get("meal_type") for m in day_meals]
    assert slots == ["breakfast", "lunch", "afternoon_snack", "dinner"], f"Wrong order: {slots}"

    # Check 1-based canonical meal_order values
    expected_orders = {
        "breakfast": MEAL_ORDER.index("breakfast") + 1,       # 1
        "lunch": MEAL_ORDER.index("lunch") + 1,               # 3
        "afternoon_snack": MEAL_ORDER.index("afternoon_snack") + 1,  # 6
        "dinner": MEAL_ORDER.index("dinner") + 1,             # 7
    }
    for meal in day_meals:
        slot = meal.get("meal_slot") or meal.get("meal_type")
        assert meal.get("meal_order") == expected_orders[slot], (
            f"meal_order for {slot} should be {expected_orders[slot]}, got {meal.get('meal_order')}"
        )


# ── collect_user_visible_text helper ─────────────────────────────────────────

def test_collect_user_visible_text_covers_all_fields():
    plan = {
        "days": [
            {
                "title": "Test Day",
                "summary": "summary-unique-abc",
                "budget_guidance": "budget-unique-xyz",
                "shopping_notes": "shopping-unique-qrs",
                "cheat_meal_guidance": "cheat-unique-pqr",
                "restaurant_party_travel_guidance": "restaurant-unique-lmn",
                "supplements_vitamins_guidance": "supplements-unique-def",
                "allowed_foods": ["allowed-unique-food"],
                "warnings": ["warning-unique-msg"],
                "meals": [
                    {
                        "title": "meal-unique-title",
                        "description": "meal-unique-desc",
                        "drink_guidance": "drink-unique-guidance",
                        "alternatives": ["alt-unique-item"],
                        "food_items": [{"name": "fi-unique-name", "amount": "1", "unit": "g"}],
                    }
                ],
            }
        ]
    }
    text = collect_user_visible_text(plan)
    for marker in (
        "summary-unique-abc", "budget-unique-xyz", "shopping-unique-qrs",
        "cheat-unique-pqr", "restaurant-unique-lmn", "supplements-unique-def",
        "allowed-unique-food", "warning-unique-msg", "meal-unique-title",
        "meal-unique-desc", "drink-unique-guidance", "alt-unique-item",
        "fi-unique-name",
    ):
        assert marker in text, f"collect_user_visible_text missed field containing '{marker}'"


# ── Portion guidance repair ───────────────────────────────────────────────────

from app.services.weekly_plan_personalization_validator import (
    _portion_guidance_is_vague,
    _repair_portion_guidance,
)


def test_vague_controlled_is_detected():
    assert _portion_guidance_is_vague("برنج کنترل‌شده") is True


def test_vague_bread_slice_without_palm_is_detected():
    assert _portion_guidance_is_vague("دو برش نان") is True


def test_vague_appropriate_amount_is_detected():
    assert _portion_guidance_is_vague("مقدار مناسب برنج") is True


def test_empty_guidance_is_vague():
    assert _portion_guidance_is_vague(None) is True
    assert _portion_guidance_is_vague("") is True


def test_palm_bread_not_vague():
    assert _portion_guidance_is_vague("۲ کف دست نان") is False


def test_spoon_rice_not_vague():
    assert _portion_guidance_is_vague("۸ قاشق غذاخوری برنج") is False


def _repair_meal(title: str, description: str = "", allergies: set | None = None) -> str:
    meal = {"title": title, "description": description, "meal_slot": "lunch"}
    return _repair_portion_guidance(meal, allergies or set())


def test_bread_slice_repaired_to_palm():
    result = _repair_meal("نان و پنیر", "نان سبوس‌دار با پنیر")
    assert "کف دست" in result


def test_rice_vague_repaired_to_spoon():
    result = _repair_meal("برنج ساده", "برنج با کره")
    assert "قاشق" in result


def test_ghormeh_sabzi_repaired_to_split():
    result = _repair_meal("برنج با خورش قرمه‌سبزی", "برنج ایرانی با خورش قرمه‌سبزی")
    assert "قاشق غذاخوری برنج" in result
    assert "قرمه" in result


def test_loobia_polo_repaired_to_single_spoon():
    result = _repair_meal("لوبیاپلو با گوجه", "لوبیاپلو سنتی")
    assert "قاشق غذاخوری" in result
    assert "لوبیاپلو" in result


def test_bread_repair_skipped_for_gluten_allergy():
    result = _repair_meal("نان و پنیر", "نان سبوس‌دار", allergies={"gluten"})
    assert "نان" not in result or "کف دست نان" not in result


def test_yogurt_repair_skipped_for_lactose_allergy():
    result = _repair_meal("ماست و خیار", "ماست کم‌چرب", allergies={"lactose"})
    assert "ماست" not in result


def test_validate_sanitize_repairs_vague_portion_fa():
    ctx = _ctx(allergies=[])
    plan = {
        "locale": "fa",
        "days": [
            {
                "day_index": i + 1,
                "title": f"روز {i+1}",
                "summary": "",
                "warnings": [],
                "meals": [
                    {
                        "meal_slot": "lunch",
                        "meal_type": "lunch",
                        "title": "برنج با خورش قرمه‌سبزی",
                        "description": "برنج ایرانی با خورش قرمه‌سبزی",
                        "portion_guidance": "برنج کنترل‌شده",
                        "alternatives": [],
                    }
                ],
            }
            for i in range(7)
        ],
    }
    result = validate_and_sanitize(plan, ctx, locale="fa")
    pg = result["days"][0]["meals"][0].get("portion_guidance", "")
    assert "کنترل‌شده" not in pg
    assert "قاشق" in pg


def test_validate_sanitize_does_not_repair_non_fa():
    ctx = _ctx(allergies=[])
    plan = {
        "locale": "en",
        "days": [
            {
                "day_index": i + 1,
                "title": f"Day {i+1}",
                "summary": "",
                "warnings": [],
                "meals": [
                    {
                        "meal_slot": "lunch",
                        "meal_type": "lunch",
                        "title": "Chicken with rice",
                        "description": "Controlled portions",
                        "portion_guidance": "controlled amount",
                        "alternatives": [],
                    }
                ],
            }
            for i in range(7)
        ],
    }
    result = validate_and_sanitize(plan, ctx, locale="en")
    pg = result["days"][0]["meals"][0].get("portion_guidance", "")
    # en locale: validator does not modify portion_guidance
    assert pg == "controlled amount"


# ── Canonical meal ordering — end-to-end ordering guarantees ─────────────────

def _day_with_meals(meals: list[dict]) -> dict:
    """Helper: single-day plan with given meals."""
    return {
        "locale": "fa",
        "days": [
            {
                "day_index": 1, "title": "Day 1", "summary": "", "warnings": [],
                "meals": meals,
            }
        ] + [{"day_index": i + 2, "title": f"Day {i+2}", "summary": "", "warnings": [], "meals": []} for i in range(6)],
    }


def test_validator_canonical_order_shuffled_input():
    """Validator must sort lunch→snack→dinner→breakfast into breakfast→lunch→dinner."""
    ctx = _ctx()
    plan = _day_with_meals([
        {"meal_slot": "lunch",   "meal_type": "lunch",   "title": "Lunch",   "description": "", "alternatives": []},
        {"meal_slot": "afternoon_snack", "meal_type": "afternoon_snack", "title": "Snack", "description": "", "alternatives": []},
        {"meal_slot": "dinner",  "meal_type": "dinner",  "title": "Dinner",  "description": "", "alternatives": []},
        {"meal_slot": "breakfast","meal_type": "breakfast","title": "Breakfast","description":"","alternatives": []},
    ])
    result = validate_and_sanitize(plan, ctx, locale="fa")
    slots = [m.get("meal_slot") or m.get("meal_type") for m in result["days"][0]["meals"]]
    assert slots == ["breakfast", "lunch", "afternoon_snack", "dinner"], f"Wrong order: {slots}"


def test_validator_ignores_stale_meal_order():
    """Validator ignores input meal_order and stamps canonical values regardless."""
    ctx = _ctx()
    plan = _day_with_meals([
        {"meal_slot": "lunch",     "meal_type": "lunch",     "title": "Lunch",     "description": "", "alternatives": [], "meal_order": 1},
        {"meal_slot": "breakfast", "meal_type": "breakfast", "title": "Breakfast", "description": "", "alternatives": [], "meal_order": 7},
        {"meal_slot": "dinner",    "meal_type": "dinner",    "title": "Dinner",    "description": "", "alternatives": [], "meal_order": 2},
    ])
    result = validate_and_sanitize(plan, ctx, locale="fa")
    meals = result["days"][0]["meals"]
    slots = [m.get("meal_slot") or m.get("meal_type") for m in meals]
    assert slots == ["breakfast", "lunch", "dinner"], f"Wrong order: {slots}"
    orders = {m.get("meal_slot"): m.get("meal_order") for m in meals}
    assert orders["breakfast"] == MEAL_ORDER.index("breakfast") + 1   # 1
    assert orders["lunch"]     == MEAL_ORDER.index("lunch") + 1       # 3
    assert orders["dinner"]    == MEAL_ORDER.index("dinner") + 1      # 7


def test_snack_time_inference_order():
    """'snack' slot is upgraded by time_window_start and sorted canonically."""
    ctx = _ctx()
    plan = _day_with_meals([
        {"meal_slot": "snack", "meal_type": "snack", "title": "Evening snack", "description": "", "alternatives": [], "time_window_start": "21:00"},
        {"meal_slot": "snack", "meal_type": "snack", "title": "Morning snack", "description": "", "alternatives": [], "time_window_start": "10:00"},
        {"meal_slot": "snack", "meal_type": "snack", "title": "Afternoon snack","description": "", "alternatives": [], "time_window_start": "15:00"},
    ])
    result = validate_and_sanitize(plan, ctx, locale="fa")
    meals = result["days"][0]["meals"]
    slots = [m.get("meal_slot") or m.get("meal_type") for m in meals]
    assert slots == ["morning_snack", "afternoon_snack", "optional_evening_snack"], f"Wrong snack order: {slots}"


def test_sort_meals_canonically_helper():
    """sort_meals_canonically() returns dicts sorted by canonical slot, ignoring meal_order."""
    meals = [
        {"meal_slot": "dinner",    "meal_type": "dinner",    "title": "Dinner",    "meal_order": 1},
        {"meal_slot": "lunch",     "meal_type": "lunch",     "title": "Lunch",     "meal_order": 3},
        {"meal_slot": "breakfast", "meal_type": "breakfast", "title": "Breakfast", "meal_order": 99},
    ]
    result = sort_meals_canonically(meals)
    slots = [m["meal_slot"] for m in result]
    assert slots == ["breakfast", "lunch", "dinner"], f"sort_meals_canonically produced: {slots}"


def test_canonical_meal_order_value_helper():
    """canonical_meal_order_value() returns correct 1-based positions."""
    assert canonical_meal_order_value("breakfast")            == 1
    assert canonical_meal_order_value("morning_snack")        == 2
    assert canonical_meal_order_value("lunch")                == 3
    assert canonical_meal_order_value("pre_workout")          == 4
    assert canonical_meal_order_value("post_workout")         == 5
    assert canonical_meal_order_value("afternoon_snack")      == 6
    assert canonical_meal_order_value("dinner")               == 7
    assert canonical_meal_order_value("optional_evening_snack") == 8
    assert canonical_meal_order_value("cheating_date")        == 9
    assert canonical_meal_order_value("snack")                == 10
    assert canonical_meal_order_value("other")                == 11
    assert canonical_meal_order_value("unknown_slot")         == 11
