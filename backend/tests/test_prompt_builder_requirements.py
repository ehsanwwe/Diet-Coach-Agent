from __future__ import annotations

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services import prompt_builder


def _ctx() -> NutritionMemoryContext:
    return NutritionMemoryContext(
        user_id="u1",
        risk_level="low",
        gender="female",
        age=34,
        height_cm=165,
        weight_kg=72,
        target_weight_kg=66,
        goal_type="weight_loss",
        activity_level="moderate",
        cooking_ability=4,
        food_budget="medium",
    )


def test_base_prompt_includes_safety_tone_culture_and_care_process():
    prompt = prompt_builder.for_generate_plan(_ctx())
    system = prompt.system

    assert "professional AI diet, nutrition, and healthy lifestyle companion" in system
    assert "non-judgmental" in system
    assert "Never use body-shaming" in system
    assert "Never recommend extreme diets" in system
    assert "Never change medication" in system
    assert "Iranian/Persian food culture" in system
    assert "household units" in system
    assert "Assessment" in system
    assert "Diagnosis/problem identification" in system
    assert "Intervention" in system
    assert "Monitoring and adjustment" in system


def test_plan_generation_prompt_contract_has_real_life_plan_requirements():
    prompt = prompt_builder.for_generate_plan(_ctx())
    user = prompt.user

    assert "Do not create a complete strict diet based only on height, weight, and goal" in user
    assert "household portions" in user
    assert "alternatives" in user
    assert "quick busy-day option" in user
    assert "outside-home/restaurant flexibility" in user
    assert "simple scientific reason" in user
    assert "monitoring_notes" in user


def test_meal_analysis_prompt_includes_required_concepts():
    prompt = prompt_builder.for_analyze_meal(
        _ctx(),
        meal_text="rice and chicken",
        meal_time="lunch",
        meal_context=None,
    )
    user = prompt.user

    assert "uncertainties" in user
    assert "satiety" in user
    assert "likely effect on the user's goal" in user
    assert "one small correction" in user
    assert "next-meal suggestion" in user
    assert "without punishment or extreme compensation advice" in user


def test_what_to_eat_now_prompt_includes_context_last_meal_goal_and_hunger_scale():
    prompt = prompt_builder.for_what_to_eat_now(
        _ctx(),
        available_foods=["eggs", "bread"],
        hunger_level="high",
        meal_context="at work, last meal was breakfast",
        time_available_minutes=10,
    )
    user = prompt.user

    assert "current place/context" in user
    assert "Available foods" in user
    assert "last meal time" in user
    assert "current goal" in user
    assert "hunger 1-10" in user
    assert "best aligned with goal" in user
    assert "fastest option" in user


def test_week_plan_locale_instruction_present_for_fa_en_ar():
    for locale, expected in [
        ("fa", "Use Persian"),
        ("en", "Use English"),
        ("ar", "Use Arabic"),
    ]:
        prompt = prompt_builder.for_generate_week_plan(_ctx(), locale=locale)
        assert f"locale={locale}" in prompt.system
        assert expected in prompt.system
        assert f'"locale": "{locale}"' in prompt.user
