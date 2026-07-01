"""Architecture tests for detect -> LLM repair -> accept weekly plans."""
from __future__ import annotations

import copy
import json

from app.services.ai_provider import AIProvider, AIProviderResult
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.mock_ai_provider import MockAIProvider
from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.prompt_builder import for_generate_week_plan, for_repair_week_plan
from app.services.week_plan_quality_evaluator import evaluate_week_plan_quality
from app.services.weekly_plan_personalization_validator import validate_and_sanitize


def _ctx(**kwargs) -> NutritionMemoryContext:
    values = dict(
        user_id="u1", food_budget="high", budget_tier="premium",
        likes_iranian_food=True, goal_type="muscle_gain", breakfast_habit="full",
    )
    values.update(kwargs)
    return NutritionMemoryContext(**values)


def _meal(slot: str, title: str, description: str | None = None) -> dict:
    return {
        "meal_type": slot, "meal_slot": slot, "title": title,
        "description": description or f"150 گرم {title}",
        "portion_guidance": f"150 گرم {title}",
        "time_window_start": "07:00" if slot == "breakfast" else "12:30",
        "time_window_end": "09:00" if slot == "breakfast" else "14:00",
        "alternatives": [], "food_items": [],
    }


def _plan(*, bad: bool = False, cheat: bool = True) -> dict:
    days = []
    for index in range(7):
        breakfast = _meal("breakfast", "سیب‌زمینی آبپز با میوه" if bad else f"صبحانه پروتئینی مرغ {index}")
        lunch = _meal("lunch", "عدسی با برنج" if bad else f"ناهار مرغ کبابی {index}")
        dinner = _meal("dinner", "سوپ سبزیجات" if bad else f"شام ماهی و سبزیجات {index}")
        meals = [breakfast, lunch, dinner]
        if cheat and index == 4:
            meals.append({
                **_meal("cheating_date", "Cheating Date", "یک انعطاف برنامه‌ریزی‌شده و کنترل‌شده، نه پرخوری؛ 1 وعده"),
                "time_window_start": "20:00", "time_window_end": "22:00",
            })
        days.append({"day_index": index + 1, "title": f"روز {index + 1}", "summary": "برنامه روز", "meals": meals})
    return {"locale": "fa", "days": days}


def _codes(plan: dict, ctx: NutritionMemoryContext | None = None) -> set[str]:
    return {issue.code for issue in evaluate_week_plan_quality(plan, ctx or _ctx(), "fa")}


def test_detects_poor_premium_breakfast_without_mutation():
    plan = _plan(bad=True)
    original = copy.deepcopy(plan)
    assert "poor_premium_breakfast" in _codes(plan)
    assert plan == original


def test_detects_premium_economic_drift_without_mutation():
    plan = _plan(bad=True)
    original = copy.deepcopy(plan)
    codes = _codes(plan)
    assert {"premium_economic_drift", "premium_lentils_rice_lunch", "repeated_light_dinner"} <= codes
    assert plan == original


def test_quality_evaluator_does_not_block_light_breakfast_for_premium_user():
    ctx = _ctx(goal_type=None, breakfast_habit="light")
    plan = _plan()
    for day in plan["days"]:
        breakfast = day["meals"][0]
        breakfast["title"] = "صبحانه سبک میوه و مغزها"
        breakfast["description"] = breakfast["portion_guidance"] = "1 عدد میوه + 15 گرم مغزها"
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    assert "poor_premium_breakfast" not in {issue.code for issue in issues}
    assert "low_protein_snacks" not in {issue.code for issue in issues}


def test_quality_evaluator_separates_safety_blockers_from_quality_warnings():
    ctx = _ctx(disliked_foods=["برنج"])
    plan = _plan(bad=True)
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    assert any(issue.code == "forbidden_food" and issue.severity == "safety_blocker" for issue in issues)
    assert any(issue.code == "premium_economic_drift" and issue.severity == "repairable_quality" for issue in issues)
    forbidden = next(issue for issue in issues if issue.code == "forbidden_food")
    assert forbidden.path.startswith("$.days[")
    assert forbidden.details["term"] == "برنج"
    assert forbidden.details["snippet"]


class _SequenceProvider(AIProvider):
    def __init__(self, plans: list[dict]):
        self.plans = plans
        self.calls: list[list[dict[str, str]]] = []

    def generate_text(self, messages, temperature=None, max_tokens=None):
        self.calls.append(messages)
        plan = self.plans[min(len(self.calls) - 1, len(self.plans) - 1)]
        return AIProviderResult(json.dumps(plan, ensure_ascii=False), "fake", "fake")


def test_service_retries_and_returns_llm_repaired_plan():
    bad, repaired = _plan(bad=True), _plan()
    provider = _SequenceProvider([bad, repaired])
    service = NutritionAgentService()
    service._provider = provider
    result, _ = service.generate_week_plan(_ctx(), "fa")
    assert len(provider.calls) == 2
    assert [d["meals"][0]["title"] for d in result["days"]] == [d["meals"][0]["title"] for d in repaired["days"]]
    assert "EXACT REVIEW ISSUES JSON" in provider.calls[1][-1]["content"]


def test_only_repairable_quality_does_not_fail_after_two_repairs():
    ctx = _ctx(goal_type=None, breakfast_habit="light", disliked_foods=[])
    quality_only = _plan(bad=True)
    provider = _SequenceProvider([quality_only, quality_only, quality_only])
    service = NutritionAgentService()
    service._provider = provider
    result, _ = service.generate_week_plan(ctx, "fa")
    assert len(provider.calls) == 3
    assert len(result["days"]) == 7
    assert not [i for i in evaluate_week_plan_quality(result, ctx, "fa") if i.severity == "safety_blocker"]


def test_missing_cheating_date_triggers_repair_prompt_and_llm_adds_it():
    bad, repaired = _plan(cheat=False), _plan()
    provider = _SequenceProvider([bad, repaired])
    service = NutritionAgentService()
    service._provider = provider
    result, _ = service.generate_week_plan(_ctx(), "fa")
    assert "missing_cheating_date" in provider.calls[1][-1]["content"]
    cheats = [m for d in result["days"] for m in d["meals"] if m["meal_slot"] == "cheating_date"]
    assert len(cheats) == 1 and cheats[0]["title"] == "Cheating Date"


def test_controlled_cheating_legacy_normalization_is_structural():
    plan = _plan()
    cheat = plan["days"][4]["meals"][-1]
    cheat["meal_type"] = cheat["meal_slot"] = "controlled_cheating"
    cheat["title"] = "Controlled Cheating"
    result = validate_and_sanitize(plan, _ctx(), "fa")
    normalized = result["days"][4]["meals"][-1]
    assert normalized["meal_type"] == normalized["meal_slot"] == "cheating_date"
    assert normalized["title"] == "Cheating Date"


def test_gluten_violation_is_blocking_and_not_replaced():
    ctx = _ctx(allergies=["گلوتن"])
    plan = _plan()
    plan["days"][0]["meals"][0]["description"] = "2 کف دست نان معمولی سنگک با مرغ"
    original = copy.deepcopy(plan)
    assert "gluten_violation" in _codes(plan, ctx)
    assert plan == original


def test_gluten_alternative_repair_instruction():
    ctx = _ctx(allergies=["gluten"], bread_frequency="daily")
    plan = _plan()
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    assert "missing_gluten_free_alternative" in {i.code for i in issues}
    prompt = for_repair_week_plan(ctx, "fa", plan, issues)
    assert "نان بدون گلوتن" in prompt.user
    assert "gluten-free" in prompt.user.lower()


def test_repair_prompt_contains_exact_forbidden_terms_and_variants():
    ctx = _ctx(disliked_foods=["بادمجان", "عدس", "برنج"])
    plan = _plan(bad=True)
    prompt = for_repair_week_plan(ctx, "fa", plan, evaluate_week_plan_quality(plan, ctx, "fa"))
    for term in ("بادمجان", "بادمجون", "eggplant", "عدس", "عدسی", "lentil", "برنج", "پلو", "چلو", "کته", "rice"):
        assert term in prompt.user
    assert "shopping_notes" in prompt.user and "alternatives" in prompt.user


def test_disliked_food_detected_in_nested_visible_fields():
    ctx = _ctx(disliked_foods=["قارچ"])
    plan = _plan()
    plan["days"][0]["shopping_notes"] = "خرید قارچ"
    plan["days"][1]["meals"][0]["alternatives"] = ["املت قارچ"]
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    assert sum(i.code == "forbidden_food" for i in issues) >= 2


def test_mock_repairs_premium_persian_staple_dislikes():
    ctx = _ctx(disliked_foods=["بادمجان", "عدس", "برنج"])
    service = NutritionAgentService()
    service._provider = MockAIProvider()
    plan, result = service.generate_week_plan(ctx, "fa")
    visible = validate_and_sanitize(plan, ctx, "fa")
    text = json.dumps(visible, ensure_ascii=False)
    assert result.provider == "mock"
    assert all(term not in text for term in ctx.disliked_foods)
    assert evaluate_week_plan_quality(plan, ctx, "fa") == []
    assert len(plan["days"]) == 7
    assert all(
        meal.get("time_window_start") and meal.get("time_window_end")
        for day in plan["days"] for meal in day["meals"]
    )


def test_week_plan_generation_succeeds_with_disliked_eggplant_lentils_rice_real_service_path():
    ctx = _ctx(
        gender="male", height_cm=200, weight_kg=140, target_weight_kg=115,
        risk_level="high", clinical_review_required=True,
        active_medical_flags=["thyroid_issues"],
        goal_type=None, breakfast_habit="light", exercise_days_per_week=3,
        allergies=[], disliked_foods=["بادمجان", "عدس", "برنج"],
        rice_frequency="daily",
    )
    assert ctx.disliked_foods == ["بادمجان", "عدس", "برنج"]
    service = NutritionAgentService()
    service._provider = MockAIProvider()

    plan, _ = service.generate_week_plan(ctx, "fa")

    forbidden_variants = (
        "بادمجان", "بادمجون", "کشک بادمجان", "eggplant",
        "عدس", "عدسی", "خوراک عدس", "سوپ عدس", "lentil", "lentils",
        "برنج", "پلو", "چلو", "کته", "زرشک‌پلو", "زرشکپلو", "سبزی‌پلو", "سبزیپلو", "rice",
    )
    visible = json.dumps(plan, ensure_ascii=False).lower()
    assert len(plan["days"]) == 7
    assert all(term not in visible for term in forbidden_variants)
    meals = [meal for day in plan["days"] for meal in day["meals"]]
    assert all(meal.get("title") and meal.get("description") for meal in meals)
    assert all(meal.get("portion_guidance") for meal in meals)
    assert all(meal.get("time_window_start") and meal.get("time_window_end") for meal in meals)
    cheats = [meal for meal in meals if meal.get("meal_slot") == "cheating_date"]
    assert len(cheats) == 1 and cheats[0]["title"] == "Cheating Date"
    assert not [issue for issue in evaluate_week_plan_quality(plan, ctx, "fa") if issue.severity == "safety_blocker"]


def test_gluten_repair_guidance_excludes_rice_options_when_disliked():
    ctx = _ctx(allergies=["گلوتن"], disliked_foods=["برنج"], bread_frequency="daily")
    plan = _plan()
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    prompt = for_repair_week_plan(ctx, "fa", plan, issues)
    guidance = prompt.user.split("GLUTEN-FREE ALTERNATIVES", 1)[-1]
    assert "نان ذرت بدون گلوتن" in guidance
    assert "نان برنجی" not in guidance
    assert "رشته برنجی" not in guidance

    service = NutritionAgentService()
    service._provider = MockAIProvider()
    repaired, _ = service.generate_week_plan(ctx, "fa")
    visible = json.dumps(repaired, ensure_ascii=False)
    assert "برنج" not in visible
    assert "نان ذرت بدون گلوتن" in visible
    assert evaluate_week_plan_quality(repaired, ctx, "fa") == []


def test_mock_repair_task_does_not_reuse_generate_week_static_plan():
    ctx = _ctx(goal_type=None, breakfast_habit="light", disliked_foods=["بادمجان", "عدس", "برنج"])
    provider = MockAIProvider()
    initial_prompt = for_generate_week_plan(ctx, "fa")
    initial = json.loads(provider.generate_text(initial_prompt.to_messages()).content)
    issues = evaluate_week_plan_quality(validate_and_sanitize(initial, ctx, "fa"), ctx, "fa")
    repaired_prompt = for_repair_week_plan(ctx, "fa", initial, issues)
    repaired = json.loads(provider.generate_text(repaired_prompt.to_messages()).content)
    assert initial != repaired
    assert repaired_prompt.task_type == "repair_week_fa"
    assert not [i for i in evaluate_week_plan_quality(repaired, ctx, "fa") if i.severity == "safety_blocker"]


def test_production_quality_modules_have_no_food_replacement_pools():
    from pathlib import Path

    services = Path(__file__).parents[1] / "app" / "services"
    source = "\n".join(
        (services / name).read_text(encoding="utf-8").lower()
        for name in ("weekly_plan_personalization_validator.py", "week_plan_quality_evaluator.py")
    )
    for forbidden_name in (
        "premium_persian_lunches", "replacement_candidates",
        "enforce_premium_persian_meal_quality", "safe_replacement",
    ):
        assert forbidden_name not in source
