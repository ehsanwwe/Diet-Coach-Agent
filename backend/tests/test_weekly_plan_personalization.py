"""Architecture tests for detect -> LLM repair -> accept weekly plans."""
from __future__ import annotations

import copy
import json

from app.services.ai_provider import AIProvider, AIProviderResult
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.prompt_builder import for_repair_week_plan
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


def test_disliked_food_detected_in_nested_visible_fields():
    ctx = _ctx(disliked_foods=["قارچ"])
    plan = _plan()
    plan["days"][0]["shopping_notes"] = "خرید قارچ"
    plan["days"][1]["meals"][0]["alternatives"] = ["املت قارچ"]
    issues = evaluate_week_plan_quality(plan, ctx, "fa")
    assert sum(i.code == "forbidden_food" for i in issues) >= 2
