"""Tests for nutrition personalization quality improvements."""
from __future__ import annotations

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services import prompt_builder


def _ctx(**kwargs) -> NutritionMemoryContext:
    defaults = dict(user_id="u1", risk_level="low", gender="female", age=32,
                    height_cm=165, weight_kg=70, goal_type="weight_loss",
                    food_budget="medium", budget_tier="standard")
    defaults.update(kwargs)
    return NutritionMemoryContext(**defaults)


# ── Restaurant habits in prompt context ───────────────────────────────────────

def test_restaurant_guidance_included_when_user_eats_out():
    ctx = _ctx(restaurant_frequency="few_weekly")
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "RESTAURANT" in p.user or "eating-out" in p.user.lower() or "restaurant_party_travel_guidance" in p.user


def test_restaurant_guidance_absent_when_user_never_eats_out():
    ctx = _ctx(restaurant_frequency="never")
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "RESTAURANT / EATING-OUT GUIDANCE" not in p.user


def test_eating_out_frequency_in_lifestyle_context():
    ctx = _ctx(eating_out_frequency="few_weekly")
    memory = ctx.to_prompt_memory()
    assert memory["lifestyle_context"].get("eating_out_frequency") == "few_weekly"


def test_restaurant_freq_in_preferences_context():
    ctx = _ctx(restaurant_frequency="daily")
    memory = ctx.to_prompt_memory()
    assert memory["preferences_and_food_culture"].get("restaurant_frequency") == "daily"


def test_chat_mentions_restaurant_when_user_eats_out():
    ctx = _ctx(restaurant_frequency="few_weekly")
    p = prompt_builder.for_chat_message(ctx, "چی بخورم؟", [])
    assert "restaurant" in p.system.lower() or "eating out" in p.system.lower() or "few_weekly" in p.system


# ── Controlled cheating in plan ───────────────────────────────────────────────

def test_controlled_cheating_section_present_in_week_plan_fa():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "چیتینگ کنترل‌شده" in p.user


def test_controlled_cheating_section_present_in_week_plan_en():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="en")
    assert "Controlled Cheating" in p.user


def test_controlled_cheating_section_present_in_week_plan_ar():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="ar")
    assert "وجبة مرنة محسوبة" in p.user


def test_controlled_cheating_conservative_for_diabetes():
    ctx = _ctx(goal_type="diabetes_support")
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "CONSERVATIVE" in p.user or "conservative" in p.user.lower()


def test_controlled_cheating_never_binge():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "binge" in p.user.lower() or "NEVER present it as binge" in p.user


# ── Travel not in plan generation context ─────────────────────────────────────

def test_travel_not_in_budget_access_summary():
    from app.services.nutrition_memory_service import summarize_budget_and_access

    class FakeLifestyle:
        food_budget = "medium"
        eating_out_frequency = "rarely"
        travel_frequency = "daily"
        cooking_ability = None
        work_schedule = None

    budget_summary, _ = summarize_budget_and_access(FakeLifestyle())
    assert "travel" not in (budget_summary or "").lower()


def test_travel_not_in_lifestyle_context_of_prompt_memory():
    ctx = _ctx(travel_frequency="daily")
    memory = ctx.to_prompt_memory()
    lifestyle = memory["lifestyle_context"]
    assert "travel_frequency" not in lifestyle
    assert "travel" not in str(lifestyle).lower()


# ── Culture-aware food planning ───────────────────────────────────────────────

def test_fa_locale_includes_persian_food_culture_rules():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "Iranian/Persian food culture" in p.user or "نان" in p.user


def test_fa_locale_warns_against_mast_chekide_as_main_breakfast():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "ماست چکیده با گردو" in p.user and ("NOT a main" in p.user or "not" in p.user.lower())


def test_ar_locale_includes_arabic_food_culture_rules():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="ar")
    assert "Arabic/Middle Eastern" in p.user or "فول" in p.user or "حمص" in p.user


def test_en_locale_uses_international_patterns():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="en")
    assert "International food culture" in p.user or "globally common" in p.user


# ── Budget + gluten → varied alternatives ─────────────────────────────────────

def test_gluten_restriction_with_medium_budget_produces_varied_alternatives():
    ctx = _ctx(allergies=["gluten"], food_budget="medium", budget_tier="standard")
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "GLUTEN-FREE ALTERNATIVES" in p.user
    assert "rice noodles" in p.user.lower() or "رشته برنجی" in p.user or "potato" in p.user.lower() or "سیب‌زمینی" in p.user


def test_gluten_restriction_with_premium_budget_mentions_quinoa():
    ctx = _ctx(allergies=["gluten"], food_budget="high", budget_tier="premium")
    p = prompt_builder.for_generate_week_plan(ctx, locale="en")
    assert "GLUTEN-FREE ALTERNATIVES" in p.user
    assert "quinoa" in p.user.lower() or "buckwheat" in p.user.lower() or "GF oats" in p.user


def test_no_gluten_restriction_no_gluten_section():
    ctx = _ctx(allergies=[])
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "GLUTEN-FREE ALTERNATIVES" not in p.user


# ── Anti-repetition rule ──────────────────────────────────────────────────────

def test_anti_repetition_rule_in_week_plan():
    ctx = _ctx()
    p = prompt_builder.for_generate_week_plan(ctx, locale="fa")
    assert "ANTI-REPETITION" in p.user
    assert "Rotate" in p.user or "rotate" in p.user


# ── Chat controls cheating topic ──────────────────────────────────────────────

def test_chat_mentions_controlled_cheating_concept():
    ctx = _ctx()
    p = prompt_builder.for_chat_message(ctx, "خسته شدم از رژیم", [])
    assert "controlled cheating" in p.system.lower() or "چیتینگ" in p.system
