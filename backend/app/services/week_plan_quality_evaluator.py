"""Deterministic quality checks for LLM-generated weekly plans.

This module reports defects; it never chooses or replaces food.
"""
from __future__ import annotations

import copy
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal

from app.services.nutrition_memory_service import NutritionMemoryContext, normalize_budget_tier


@dataclass(frozen=True)
class DietPlanQualityIssue:
    code: str
    severity: Literal["error", "warning"]
    path: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


_PROTEIN = ("مرغ", "گوشت", "ماهی", "تخم", "کباب", "میگو", "تن", "protein", "chicken", "meat", "fish", "egg", "tofu")
_ECONOMIC = ("عدسی", "عدس با برنج", "لوبیا", "آش", "سوپ")
_SOUP = ("سوپ", "آش", "soup")
_FRUIT = ("میوه", "سیب", "موز", "پرتقال", "fruit", "apple", "banana", "orange")
_QUANTITY = re.compile(r"(?:\d|[۰-۹]|گرم|کیلو|قاشق|لیوان|کاسه|عدد|کف دست|برش|پیمانه|g\b|gram|cup|tbsp|piece)", re.I)
_VAGUE = ("مقدار مناسب", "کمی", "متعادل", "یک وعده")
_GLUTEN_MARKERS = ("gluten", "wheat", "گلوتن", "گندم")
_UNSAFE_GLUTEN = ("نان معمولی", "سنگک", "بربری", "لواش معمولی", "تافتون معمولی", "آرد گندم", "آش رشته", "رشته آش", "ماکارونی معمولی", "پاستای معمولی", "regular pasta", "regular noodles", "couscous", "rye", "barley")
_GF_ALTERNATIVES = ("بدون گلوتن", "نان برنجی", "نان ذرت", "برنج", "سیب زمینی", "سیب‌زمینی", "رشته برنجی", "کینوا", "buckwheat", "جو دوسر بدون گلوتن", "gluten-free")
_VISIBLE_DAY_FIELDS = ("title", "summary", "notes", "shopping_notes", "budget_guidance", "cheat_meal_guidance", "restaurant_party_travel_guidance")
_VISIBLE_MEAL_FIELDS = ("title", "description", "portion_guidance", "preparation_notes", "drink_guidance")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower().replace("ي", "ی").replace("ك", "ک")
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    return ""


def _meal_text(meal: dict) -> str:
    return _text({k: meal.get(k) for k in (*_VISIBLE_MEAL_FIELDS, "alternatives", "food_items")})


def _slot(meal: dict) -> str:
    return str(meal.get("meal_slot") or meal.get("meal_type") or "").lower()


def _is_gluten_restricted(ctx: NutritionMemoryContext) -> bool:
    return any(any(marker in _text(item) for marker in _GLUTEN_MARKERS) for item in ctx.allergies)


def _issue(code: str, path: str, message: str, **details: Any) -> DietPlanQualityIssue:
    return DietPlanQualityIssue(code, "error", path, message, details)


def _string_paths(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, _text(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _string_paths(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _string_paths(item, f"{path}[{index}]")


def evaluate_week_plan_quality(plan_data: dict, ctx: NutritionMemoryContext, locale: str) -> list[DietPlanQualityIssue]:
    """Return structured defects without mutating *plan_data*."""
    snapshot = copy.deepcopy(plan_data)
    issues: list[DietPlanQualityIssue] = []
    days = plan_data.get("days")
    if not isinstance(days, list) or len(days) != 7:
        issues.append(_issue("invalid_day_count", "$.days", "Plan must contain exactly 7 days.", actual=len(days or [])))
        return issues

    premium_fa = locale == "fa" and ctx.likes_iranian_food and normalize_budget_tier(ctx.food_budget or ctx.budget_tier) == "premium"
    breakfasts: list[tuple[str, str]] = []
    lunches: list[str] = []
    dinners: list[str] = []
    snacks: list[str] = []
    cheats: list[tuple[int, dict]] = []

    forbidden = [x for x in (*ctx.allergies, *ctx.disliked_foods) if x and not any(m in _text(x) for m in _GLUTEN_MARKERS)]
    visible_strings = list(_string_paths(plan_data))
    for term in forbidden:
        normalized = _text(term)
        for path, value in visible_strings:
            if normalized in value:
                position = value.find(normalized)
                snippet = value[max(0, position - 30):position + len(normalized) + 30]
                issues.append(_issue(
                    "forbidden_food", path,
                    "Allergy/intolerance or disliked food appears in a user-visible field.",
                    term=term, snippet=snippet,
                ))
    if _is_gluten_restricted(ctx):
        for path, value in visible_strings:
            if any(term in value for term in _UNSAFE_GLUTEN):
                issues.append(_issue("gluten_violation", path, "Plan contains a wheat/gluten food despite the gluten restriction."))

    for di, day in enumerate(days):
        day_path = f"$.days[{di}]"
        meals = day.get("meals") if isinstance(day, dict) else None
        if not isinstance(meals, list):
            issues.append(_issue("missing_meals", f"{day_path}.meals", "Day meals must be an array."))
            continue
        for mi, meal in enumerate(meals):
            path = f"{day_path}.meals[{mi}]"
            text = _meal_text(meal)
            slot = _slot(meal)
            if slot in {"cheating_date", "controlled_cheating"}:
                cheats.append((di + 1, meal))
            if slot == "breakfast": breakfasts.append((str(meal.get("title") or "").strip().lower(), text))
            elif slot == "lunch": lunches.append(text)
            elif slot == "dinner": dinners.append(text)
            elif "snack" in slot or slot == "snack": snacks.append(text)
            desc = _text(meal.get("description")) + " " + _text(meal.get("portion_guidance"))
            if slot != "cheating_date" and (not _QUANTITY.search(desc) or any(v in desc for v in _VAGUE)):
                issues.append(_issue("vague_portion", path, "Meal needs measurable portions in description or portion_guidance."))
            if slot != "cheating_date" and (not meal.get("time_window_start") or not meal.get("time_window_end")):
                issues.append(_issue("missing_time_window", path, "Meal needs a clear time window."))

    if len(cheats) != 1:
        issues.append(_issue("missing_cheating_date" if not cheats else "duplicate_cheating_date", "$.days", "Exactly one visible Cheating Date meal is required.", count=len(cheats)))
    else:
        day_no, meal = cheats[0]
        desc = _meal_text(meal)
        if day_no not in (5, 6) or meal.get("title") != "Cheating Date" or not meal.get("time_window_start") or not meal.get("time_window_end"):
            issues.append(_issue("invalid_cheating_date", f"$.days[{day_no - 1}]", "Cheating Date must be on day 5 or 6, use the exact title, and include a time window."))
        if not any(x in desc for x in ("کنترل", "برنامه", "planned", "controlled")) or any(x in desc for x in ("شوک متابولیسم", "metabolism shock")):
            issues.append(_issue("invalid_cheating_date_guidance", f"$.days[{day_no - 1}]", "Cheating Date must describe planned controlled flexibility without unsupported metabolism claims."))

    if premium_fa:
        title_counts = Counter(t for t, _ in breakfasts if t)
        for title, count in title_counts.items():
            if count > 2: issues.append(_issue("repeated_breakfast", "$.days", "The same breakfast title appears more than twice.", title=title, count=count))
        for idx, (_, text) in enumerate(breakfasts):
            # A potato-based breakfast is not inherently poor when paired with
            # meaningful protein. The blocking condition is the absent protein.
            if not any(p in text for p in _PROTEIN):
                issues.append(_issue("poor_premium_breakfast", f"$.days[{idx}].meals", "Full premium breakfast is snack-like or lacks meaningful protein."))
        economic_count = sum(any(k in text for k in _ECONOMIC) for text in lunches + dinners)
        if economic_count > 2: issues.append(_issue("premium_economic_drift", "$.days", "Premium plan contains too many economic filler main meals.", count=economic_count))
        if any("عدسی" in text and "برنج" in text for text in lunches): issues.append(_issue("premium_lentils_rice_lunch", "$.days", "عدسی با برنج is not appropriate as a premium high-protein lunch unless explicitly requested."))
        if sum(any(p in text for p in _PROTEIN) for text in lunches) < 5: issues.append(_issue("insufficient_lunch_protein", "$.days", "Fewer than 5 lunches contain meaningful main protein."))
        soup_dinners = sum(any(k in text for k in _SOUP) for text in dinners)
        if soup_dinners > 1: issues.append(_issue("repeated_light_dinner", "$.days", "Soup/light dinner appears more than once in a premium plan.", count=soup_dinners))
        if sum(any(p in text for p in _PROTEIN) for text in dinners) < 4: issues.append(_issue("insufficient_dinner_protein", "$.days", "Fewer than 4 dinners contain meaningful protein."))
        fruit_only = sum(any(f in text for f in _FRUIT) and not any(p in text for p in _PROTEIN) for text in snacks)
        if fruit_only > 2: issues.append(_issue("low_protein_snacks", "$.days", "Too many fruit-only snacks for a premium high-protein plan.", count=fruit_only))

    if _is_gluten_restricted(ctx):
        all_visible = _text(plan_data)
        bread_expected = (ctx.bread_frequency or "").lower() not in ("", "never", "none") or locale == "fa"
        if bread_expected and not any(alt in all_visible for alt in _GF_ALTERNATIVES):
            issues.append(_issue("missing_gluten_free_alternative", "$.days", "Gluten restriction needs practical gluten-free bread/grain alternatives, not simple removal."))

    assert plan_data == snapshot, "quality evaluator must not mutate the plan"
    return issues


def has_blocking_quality_issues(issues: list[DietPlanQualityIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
