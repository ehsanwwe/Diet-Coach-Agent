"""
NutritionMemoryService: collects and compacts user context from DB for AI prompts.

Returns NutritionMemoryContext — the single source of truth for all prompt building.
Raw file paths, tokens, and secrets are never included.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.chat import MealEntry
from app.models.progress import ProgressEntry, WeeklyReport
from app.models.user import User
from app.repositories import calendar_repository, onboarding_repository, progress_repository


@dataclass
class NutritionMemoryContext:
    user_id: str
    # Anthropometrics
    height_cm: float | None = None
    weight_kg: float | None = None
    target_weight_kg: float | None = None
    waist_circumference: float | None = None
    gender: str | None = None
    age: int | None = None
    # Medical
    risk_level: str = "low"
    clinical_review_required: bool = False
    active_medical_flags: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    warning_symptoms: list[str] = field(default_factory=list)
    # Nutrition goal
    goal_type: str | None = None
    # Lifestyle
    activity_level: str | None = None
    sleep_hours: float | None = None
    stress_level: int | None = None
    work_schedule: str | None = None
    cooking_ability: int | None = None
    food_budget: str | None = None
    eating_out_frequency: str | None = None
    travel_frequency: str | None = None
    # Food preferences
    vegetarian: bool = False
    vegan: bool = False
    halal: bool = True
    likes_iranian_food: bool = True
    disliked_foods: list[str] = field(default_factory=list)
    favorite_foods: list[str] = field(default_factory=list)
    # Behavior
    emotional_eating: bool = False
    night_eating: bool = False
    meal_skipping: bool = False
    cravings: list[str] = field(default_factory=list)
    binge_history: bool = False
    diet_history: str | None = None
    previous_failures: str | None = None
    hunger_pattern: str | None = None
    motivation_level: int | None = None
    diet_history_summary: str | None = None
    previous_failures_summary: str | None = None
    craving_patterns: str | None = None
    hard_meals: str | None = None
    emotional_eating_pattern: str | None = None
    night_eating_pattern: str | None = None
    skipped_meal_pattern: str | None = None
    stress_eating_pattern: str | None = None
    sleep_craving_pattern: str | None = None
    budget_access_summary: str | None = None
    cooking_access_summary: str | None = None
    meal_history_summary: str | None = None
    progress_history_summary: str | None = None
    recent_checkin_summary: str | None = None
    energy_trend_summary: str | None = None
    hunger_1_10_trend_summary: str | None = None
    daily_craving_summary: str | None = None
    eating_location_summary: str | None = None
    planned_eating_out_summary: str | None = None
    symptom_summary: str | None = None
    adherence_summary: str | None = None
    weekly_insights_summary: str | None = None
    body_response_summary: str | None = None
    communication_style: str | None = None
    # Current active plan
    current_plan_id: str | None = None
    current_plan_title: str | None = None
    current_plan_summary: str | None = None
    active_plan_summary: str | None = None
    active_calendar_summary: str | None = None

    def to_compact_dict(self) -> dict:
        """Return a concise dict for embedding in AI prompts."""
        d: dict = {}
        if self.gender:
            d["gender"] = self.gender
        if self.age:
            d["age"] = self.age
        if self.height_cm and self.weight_kg:
            d["height_cm"] = self.height_cm
            d["weight_kg"] = self.weight_kg
        if self.target_weight_kg:
            d["target_weight_kg"] = self.target_weight_kg
        if self.waist_circumference:
            d["waist_circumference"] = self.waist_circumference
        if self.goal_type:
            d["goal"] = self.goal_type
        d["risk_level"] = self.risk_level
        if self.clinical_review_required:
            d["clinical_review_required"] = True
        if self.active_medical_flags:
            d["medical_conditions"] = self.active_medical_flags
        if self.medications:
            d["medications"] = self.medications
        if self.allergies:
            d["allergies"] = self.allergies
        if self.activity_level:
            d["activity_level"] = self.activity_level
        if self.sleep_hours is not None:
            d["sleep_hours"] = self.sleep_hours
        if self.stress_level is not None:
            d["stress_level"] = self.stress_level
        if self.cooking_ability is not None:
            d["cooking_ability"] = self.cooking_ability
        if self.food_budget:
            d["food_budget"] = self.food_budget
        if self.budget_access_summary:
            d["budget_access_summary"] = self.budget_access_summary
        if self.cooking_access_summary:
            d["cooking_access_summary"] = self.cooking_access_summary
        d["vegetarian"] = self.vegetarian
        d["vegan"] = self.vegan
        d["halal"] = self.halal
        d["likes_iranian_food"] = self.likes_iranian_food
        if self.disliked_foods:
            d["disliked_foods"] = self.disliked_foods
        if self.favorite_foods:
            d["favorite_foods"] = self.favorite_foods
        if self.emotional_eating:
            d["emotional_eating"] = True
        if self.night_eating:
            d["night_eating"] = True
        if self.meal_skipping:
            d["meal_skipping"] = True
        if self.motivation_level is not None:
            d["motivation_level"] = self.motivation_level
        if self.cravings:
            d["cravings"] = self.cravings
        if self.hunger_pattern:
            d["hunger_pattern"] = self.hunger_pattern
        if self.diet_history_summary:
            d["diet_history_summary"] = self.diet_history_summary
        if self.previous_failures_summary:
            d["previous_failures"] = self.previous_failures_summary
        if self.craving_patterns:
            d["craving_patterns"] = self.craving_patterns
        if self.hard_meals:
            d["hard_meals"] = self.hard_meals
        if self.emotional_eating_pattern:
            d["emotional_eating_pattern"] = self.emotional_eating_pattern
        if self.night_eating_pattern:
            d["night_eating_pattern"] = self.night_eating_pattern
        if self.skipped_meal_pattern:
            d["skipped_meal_pattern"] = self.skipped_meal_pattern
        if self.stress_eating_pattern:
            d["stress_eating_pattern"] = self.stress_eating_pattern
        if self.sleep_craving_pattern:
            d["sleep_craving_pattern"] = self.sleep_craving_pattern
        if self.meal_history_summary:
            d["meal_history_summary"] = self.meal_history_summary
        if self.progress_history_summary:
            d["progress_history_summary"] = self.progress_history_summary
        if self.recent_checkin_summary:
            d["recent_checkin_summary"] = self.recent_checkin_summary
        if self.energy_trend_summary:
            d["energy_trend_summary"] = self.energy_trend_summary
        if self.hunger_1_10_trend_summary:
            d["hunger_1_10_trend_summary"] = self.hunger_1_10_trend_summary
        if self.daily_craving_summary:
            d["daily_craving_summary"] = self.daily_craving_summary
        if self.eating_location_summary:
            d["eating_location_summary"] = self.eating_location_summary
        if self.planned_eating_out_summary:
            d["planned_eating_out_summary"] = self.planned_eating_out_summary
        if self.symptom_summary:
            d["symptom_summary"] = self.symptom_summary
        if self.adherence_summary:
            d["adherence_summary"] = self.adherence_summary
        if self.weekly_insights_summary:
            d["weekly_insights_summary"] = self.weekly_insights_summary
        if self.body_response_summary:
            d["body_response_summary"] = self.body_response_summary
        if self.communication_style:
            d["communication_style"] = self.communication_style
        if self.active_plan_summary:
            d["active_plan_summary"] = self.active_plan_summary
        if self.active_calendar_summary:
            d["active_calendar_summary"] = self.active_calendar_summary
        return d

    def to_prompt_memory(self) -> dict[str, Any]:
        """Return grouped, compact memory sections for prompt readability."""
        missing: list[str] = []
        if self.age is None:
            missing.append("age")
        if not self.gender:
            missing.append("gender")
        if self.height_cm is None:
            missing.append("height")
        if self.weight_kg is None:
            missing.append("weight")
        if not self.goal_type:
            missing.append("goal")
        if not self.recent_checkin_summary:
            missing.append("recent_checkins")
        if not self.meal_history_summary:
            missing.append("meal_history")

        return {
            "stable_user_profile": {
                k: v
                for k, v in {
                    "age": self.age,
                    "gender": self.gender,
                    "height_cm": self.height_cm,
                    "weight_kg": self.weight_kg,
                    "target_weight_kg": self.target_weight_kg,
                    "waist_circumference": self.waist_circumference,
                    "goal": self.goal_type,
                }.items()
                if v is not None
            },
            "medical_safety_context": {
                "risk_level": self.risk_level,
                "clinical_review_required": self.clinical_review_required,
                "medical_conditions": self.active_medical_flags,
                "medications": self.medications,
                "allergies": self.allergies,
                "warning_symptoms": self.warning_symptoms,
            },
            "lifestyle_context": {
                k: v
                for k, v in {
                    "activity_level": self.activity_level,
                    "sleep_hours": self.sleep_hours,
                    "stress_level": self.stress_level,
                    "work_schedule": self.work_schedule,
                    "budget_access_summary": self.budget_access_summary,
                    "cooking_access_summary": self.cooking_access_summary,
                }.items()
                if v is not None
            },
            "preferences_and_food_culture": {
                "vegetarian": self.vegetarian,
                "vegan": self.vegan,
                "halal": self.halal,
                "likes_iranian_food": self.likes_iranian_food,
                "favorite_foods": self.favorite_foods,
                "disliked_foods": self.disliked_foods,
            },
            "behavior_patterns": {
                k: v
                for k, v in {
                    "diet_history_summary": self.diet_history_summary,
                    "previous_failures": self.previous_failures_summary,
                    "craving_patterns": self.craving_patterns,
                    "hard_meals": self.hard_meals,
                    "emotional_eating_pattern": self.emotional_eating_pattern,
                    "night_eating_pattern": self.night_eating_pattern,
                    "skipped_meal_pattern": self.skipped_meal_pattern,
                    "stress_eating_pattern": self.stress_eating_pattern,
                    "sleep_craving_pattern": self.sleep_craving_pattern,
                    "motivation_level": self.motivation_level,
                }.items()
                if v is not None
            },
            "recent_progress_checkins": {
                k: v
                for k, v in {
                    "recent_checkin_summary": self.recent_checkin_summary,
                    "energy_trend_summary": self.energy_trend_summary,
                    "hunger_1_10_trend_summary": self.hunger_1_10_trend_summary,
                    "daily_craving_summary": self.daily_craving_summary,
                    "eating_location_summary": self.eating_location_summary,
                    "planned_eating_out_summary": self.planned_eating_out_summary,
                    "symptom_summary": self.symptom_summary,
                    "adherence_summary": self.adherence_summary,
                    "progress_history_summary": self.progress_history_summary,
                    "weekly_insights_summary": self.weekly_insights_summary,
                    "body_response_summary": self.body_response_summary,
                    "meal_history_summary": self.meal_history_summary,
                }.items()
                if v is not None
            },
            "active_plan_context": {
                k: v
                for k, v in {
                    "current_plan_id": self.current_plan_id,
                    "current_plan_title": self.current_plan_title,
                    "active_plan_summary": self.active_plan_summary,
                    "active_calendar_summary": self.active_calendar_summary,
                }.items()
                if v is not None
            },
            "missing_or_unknown_data": missing,
        }


def _calc_age(birth_date: date) -> int:
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def _decode_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def _decode_json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _avg(values: list[float | int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def summarize_behavior_profile(bp) -> dict[str, str | None]:
    if not bp:
        return {}

    cravings = _decode_json_list(bp.cravings)
    patterns: dict[str, str | None] = {
        "diet_history_summary": bp.diet_history,
        "previous_failures_summary": bp.previous_failures,
        "craving_patterns": ", ".join(cravings[:5]) if cravings else None,
        "emotional_eating_pattern": "reported" if bp.emotional_eating else None,
        "night_eating_pattern": "reported" if bp.night_eating else None,
        "skipped_meal_pattern": "reported" if bp.meal_skipping else None,
        "hard_meals": None,
    }
    if bp.hunger_pattern:
        patterns["hard_meals"] = f"hunger pattern: {bp.hunger_pattern}"
    return patterns


def summarize_budget_and_access(lifestyle) -> tuple[str | None, str | None]:
    if not lifestyle:
        return None, None
    budget_parts = []
    if lifestyle.food_budget:
        budget_parts.append(f"budget={lifestyle.food_budget}")
    if lifestyle.eating_out_frequency:
        budget_parts.append(f"eating_out={lifestyle.eating_out_frequency}")
    if lifestyle.travel_frequency:
        budget_parts.append(f"travel={lifestyle.travel_frequency}")

    cooking_parts = []
    if lifestyle.cooking_ability is not None:
        cooking_parts.append(f"cooking_ability={lifestyle.cooking_ability}/5")
    if lifestyle.work_schedule:
        cooking_parts.append(f"work_schedule={lifestyle.work_schedule}")

    return (
        "; ".join(budget_parts) if budget_parts else None,
        "; ".join(cooking_parts) if cooking_parts else None,
    )


def summarize_recent_checkins(checkins) -> str | None:
    if not checkins:
        return None
    oldest_first = list(reversed(checkins[:7]))
    weights = [c.weight_kg for c in oldest_first if c.weight_kg is not None]
    waists = [c.waist_cm for c in oldest_first if getattr(c, "waist_cm", None) is not None]
    sleeps = [c.sleep_hours for c in oldest_first if c.sleep_hours is not None]
    sleep_quality = [
        c.sleep_quality for c in oldest_first if getattr(c, "sleep_quality", None) is not None
    ]
    stresses = [c.stress_level for c in oldest_first if c.stress_level is not None]
    hungers = [c.hunger_level for c in oldest_first if c.hunger_level is not None]
    hungers_10 = [
        c.hunger_level_1_10
        for c in oldest_first
        if getattr(c, "hunger_level_1_10", None) is not None
    ]
    energy = [c.energy_level for c in oldest_first if getattr(c, "energy_level", None) is not None]
    activities = [c.activity_minutes for c in oldest_first if c.activity_minutes is not None]
    adherence = [
        c.adherence_level for c in oldest_first if getattr(c, "adherence_level", None) is not None
    ]
    notes = [c.adherence_notes.strip() for c in oldest_first if c.adherence_notes and c.adherence_notes.strip()]
    cravings = [c.cravings.strip() for c in oldest_first if getattr(c, "cravings", None)]
    locations = [c.eating_location for c in oldest_first if getattr(c, "eating_location", None)]
    symptoms = [c.symptoms.strip() for c in oldest_first if getattr(c, "symptoms", None)]

    parts = [f"{len(oldest_first)} recent check-ins"]
    if len(weights) >= 2:
        parts.append(f"weight {weights[0]}->{weights[-1]}kg")
    elif weights:
        parts.append(f"latest weight {weights[-1]}kg")
    if len(waists) >= 2:
        parts.append(f"waist {waists[0]}->{waists[-1]}cm")
    elif waists:
        parts.append(f"latest waist {waists[-1]}cm")
    if sleeps:
        parts.append(f"avg sleep {_avg(sleeps)}h")
    if sleep_quality:
        parts.append(f"avg sleep quality {_avg(sleep_quality)}/5")
    if stresses:
        parts.append(f"avg stress {_avg(stresses)}/5")
    if hungers:
        parts.append(f"avg hunger {_avg(hungers)}/5")
    if hungers_10:
        parts.append(f"avg hunger {_avg(hungers_10)}/10")
    if energy:
        parts.append(f"avg energy {_avg(energy)}/5")
    if activities:
        parts.append(f"avg activity {int(_avg(activities) or 0)}min")
    if adherence:
        parts.append(f"avg adherence {_avg(adherence)}/5")
    if cravings:
        parts.append("cravings: " + " | ".join(cravings[-3:]))
    if locations:
        counts = Counter(locations)
        parts.append("eating locations: " + ", ".join(f"{k}={v}" for k, v in counts.most_common(3)))
    if any(getattr(c, "planned_eating_out", None) for c in oldest_first):
        parts.append("planned eating out reported")
    if symptoms:
        parts.append("symptoms: " + " | ".join(symptoms[-3:]))
    if notes:
        parts.append("recent notes: " + " | ".join(notes[-3:]))
    return "; ".join(parts)


def summarize_checkin_signals(checkins) -> dict[str, str | None]:
    if not checkins:
        return {}
    oldest_first = list(reversed(checkins[:7]))
    energy = [c.energy_level for c in oldest_first if getattr(c, "energy_level", None) is not None]
    hungers_10 = [
        c.hunger_level_1_10
        for c in oldest_first
        if getattr(c, "hunger_level_1_10", None) is not None
    ]
    cravings = [c.cravings.strip() for c in oldest_first if getattr(c, "cravings", None)]
    locations = [c.eating_location for c in oldest_first if getattr(c, "eating_location", None)]
    symptoms = [c.symptoms.strip() for c in oldest_first if getattr(c, "symptoms", None)]
    adherence = [
        c.adherence_level for c in oldest_first if getattr(c, "adherence_level", None) is not None
    ]
    planned_out_count = sum(1 for c in oldest_first if getattr(c, "planned_eating_out", None))

    return {
        "energy_trend_summary": f"avg energy {_avg(energy)}/5" if energy else None,
        "hunger_1_10_trend_summary": f"avg hunger {_avg(hungers_10)}/10" if hungers_10 else None,
        "daily_craving_summary": " | ".join(cravings[-3:]) if cravings else None,
        "eating_location_summary": (
            ", ".join(f"{k}={v}" for k, v in Counter(locations).most_common(3))
            if locations
            else None
        ),
        "planned_eating_out_summary": (
            f"planned eating out on {planned_out_count} recent day(s)" if planned_out_count else None
        ),
        "symptom_summary": " | ".join(symptoms[-3:]) if symptoms else None,
        "adherence_summary": f"avg adherence {_avg(adherence)}/5" if adherence else None,
    }


def summarize_progress_history(db: Session, user_id: str) -> tuple[str | None, str | None]:
    result = db.execute(
        select(ProgressEntry)
        .where(ProgressEntry.user_id == user_id)
        .order_by(desc(ProgressEntry.recorded_at))
        .limit(10)
    )
    entries = list(reversed(result.scalars().all()))
    if not entries:
        return None, None

    by_type: dict[str, list[ProgressEntry]] = {}
    for entry in entries:
        by_type.setdefault(entry.entry_type, []).append(entry)

    parts = []
    body_parts = []
    for entry_type, rows in by_type.items():
        nums = [r.value_numeric for r in rows if r.value_numeric is not None]
        if len(nums) >= 2:
            text = f"{entry_type}: {nums[0]}->{nums[-1]}"
        elif nums:
            text = f"{entry_type}: latest {nums[-1]}"
        else:
            vals = [r.value_text for r in rows if r.value_text]
            text = f"{entry_type}: {vals[-1]}" if vals else None
        if text:
            parts.append(text)
            if entry_type in {"weight", "waist", "waist_cm", "body_response"}:
                body_parts.append(text)

    return ("; ".join(parts) if parts else None, "; ".join(body_parts) if body_parts else None)


def summarize_meal_history(db: Session, user_id: str) -> str | None:
    result = db.execute(
        select(MealEntry)
        .where(MealEntry.user_id == user_id)
        .order_by(desc(MealEntry.logged_at))
        .limit(10)
    )
    meals = list(result.scalars().all())
    if not meals:
        return None

    meal_types = Counter(m.meal_time or "unknown" for m in meals)
    examples = [m.description[:80] for m in meals[:3]]
    quality_scores = []
    summaries = []
    for meal in meals:
        data = _decode_json_dict(meal.analysis_result)
        score = data.get("quality_score")
        if isinstance(score, (int, float)):
            quality_scores.append(score)
        summary = data.get("analysis_summary")
        if isinstance(summary, str) and summary:
            summaries.append(summary[:100])

    parts = [
        f"{len(meals)} recent meals",
        "meal types: " + ", ".join(f"{k}={v}" for k, v in meal_types.most_common()),
    ]
    if quality_scores:
        parts.append(f"avg quality score {_avg(quality_scores)}/10")
    if examples:
        parts.append("examples: " + " | ".join(examples))
    if summaries:
        parts.append("recent analysis: " + " | ".join(summaries[:2]))
    return "; ".join(parts)


def summarize_weekly_insights(db: Session, user_id: str) -> str | None:
    result = db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user_id)
        .order_by(desc(WeeklyReport.generated_at))
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        return None
    data = _decode_json_dict(report.report_data)
    if not data:
        return None
    parts = [f"week {report.week_start.isoformat()} to {report.week_end.isoformat()}"]
    for key in ("avg_hunger", "avg_sleep", "avg_stress", "total_activity_minutes", "adherence_pct", "suggested_focus", "sleep_stress_note"):
        value = data.get(key)
        if value is not None:
            parts.append(f"{key}={value}")
    return "; ".join(parts)


def summarize_active_plan(db: Session, plan) -> str | None:
    if not plan:
        return None
    from app.repositories import nutrition_repository

    meta = nutrition_repository.get_plan_metadata(plan)
    warnings = meta.get("warnings") or []
    daily = meta.get("daily_guidelines") or {}
    parts = [f"title={plan.title}"]
    if plan.description:
        parts.append(f"summary={plan.description[:160]}")
    if meta.get("plan_type"):
        parts.append(f"plan_type={meta.get('plan_type')}")
    if daily.get("calories") is not None:
        parts.append(f"calories={daily.get('calories')}")
    if warnings:
        parts.append("warnings=" + " | ".join(str(w)[:80] for w in warnings[:3]))
    return "; ".join(parts)


def summarize_active_calendar(db: Session, user_id: str) -> str | None:
    locale = calendar_repository.resolve_locale(None, calendar_repository.get_user_language(db, user_id))
    today = date.today()
    days = calendar_repository.get_plan_days(db, user_id, locale, today, today + timedelta(days=6))
    if not days:
        return None
    parts = [f"locale={locale}", f"{len(days)} planned days in next 7 days"]
    titles = [d.title for d in days[:3] if d.title]
    if titles:
        parts.append("upcoming: " + " | ".join(titles))
    warnings: list[str] = []
    for day in days:
        warnings.extend(calendar_repository.decode_json_list(day.warnings))
    if warnings:
        parts.append("warnings: " + " | ".join(warnings[:3]))
    return "; ".join(parts)


def build(db: Session, user: User) -> NutritionMemoryContext:
    """Build a NutritionMemoryContext from all DB tables for this user."""
    from app.repositories import nutrition_repository

    ctx = NutritionMemoryContext(user_id=user.id)

    # Profile
    profile = onboarding_repository.get_profile(db, user.id)
    if profile:
        ctx.height_cm = profile.height_cm
        ctx.weight_kg = profile.weight_kg
        ctx.target_weight_kg = profile.target_weight_kg
        ctx.waist_circumference = profile.waist_cm
        ctx.gender = profile.gender
        if profile.birth_date:
            ctx.age = _calc_age(profile.birth_date)

    # Medical flags (active only, excluding sentinel row)
    all_flags = onboarding_repository.get_medical_flags(db, user.id)
    ctx.active_medical_flags = [
        f.condition_code
        for f in all_flags
        if f.has_condition
        and f.condition_code != onboarding_repository.WARNING_SYMPTOMS_CODE
    ]

    # Medications & allergies
    meds = onboarding_repository.get_medications(db, user.id)
    ctx.medications = [m.name for m in meds]

    allergies = onboarding_repository.get_allergies(db, user.id)
    ctx.allergies = [a.allergen for a in allergies]

    # Warning symptoms
    ctx.warning_symptoms = onboarding_repository.get_warning_symptoms(db, user.id)

    # Latest risk assessment
    ra = onboarding_repository.get_latest_risk_assessment(db, user.id)
    if ra:
        ctx.risk_level = ra.risk_level
        ctx.clinical_review_required = ra.risk_level == "clinical_review_required"

    # Nutrition goal
    goal = nutrition_repository.get_nutrition_goal(db, user.id)
    if goal:
        ctx.goal_type = goal.goal_type

    # Lifestyle
    ls = onboarding_repository.get_lifestyle(db, user.id)
    if ls:
        ctx.activity_level = ls.activity_level
        ctx.sleep_hours = ls.sleep_hours
        ctx.stress_level = ls.stress_level
        ctx.work_schedule = ls.work_schedule
        ctx.cooking_ability = ls.cooking_ability
        ctx.food_budget = ls.food_budget
        ctx.eating_out_frequency = ls.eating_out_frequency
        ctx.travel_frequency = ls.travel_frequency
        ctx.budget_access_summary, ctx.cooking_access_summary = summarize_budget_and_access(ls)

    # Food preferences
    fp = onboarding_repository.get_food_preference(db, user.id)
    if fp:
        ctx.vegetarian = fp.vegetarian
        ctx.vegan = fp.vegan
        ctx.halal = fp.halal
        ctx.likes_iranian_food = fp.likes_iranian_food
        if fp.disliked_foods:
            try:
                ctx.disliked_foods = json.loads(fp.disliked_foods)
            except (json.JSONDecodeError, TypeError):
                ctx.disliked_foods = []
        if fp.favorite_foods:
            try:
                ctx.favorite_foods = json.loads(fp.favorite_foods)
            except (json.JSONDecodeError, TypeError):
                ctx.favorite_foods = []

    # Behavior
    bp = onboarding_repository.get_behavior_profile(db, user.id)
    if bp:
        ctx.emotional_eating = bp.emotional_eating
        ctx.night_eating = bp.night_eating
        ctx.meal_skipping = bp.meal_skipping
        ctx.cravings = _decode_json_list(bp.cravings)
        ctx.binge_history = bp.binge_history
        ctx.diet_history = bp.diet_history
        ctx.previous_failures = bp.previous_failures
        ctx.hunger_pattern = bp.hunger_pattern
        ctx.motivation_level = bp.motivation_level
        behavior_summary = summarize_behavior_profile(bp)
        ctx.diet_history_summary = behavior_summary.get("diet_history_summary")
        ctx.previous_failures_summary = behavior_summary.get("previous_failures_summary")
        ctx.craving_patterns = behavior_summary.get("craving_patterns")
        ctx.hard_meals = behavior_summary.get("hard_meals")
        ctx.emotional_eating_pattern = behavior_summary.get("emotional_eating_pattern")
        ctx.night_eating_pattern = behavior_summary.get("night_eating_pattern")
        ctx.skipped_meal_pattern = behavior_summary.get("skipped_meal_pattern")
        if bp.emotional_eating and ls and ls.stress_level is not None and ls.stress_level >= 4:
            ctx.stress_eating_pattern = "emotional eating reported with high baseline stress"
        if ctx.cravings and ls and ls.sleep_hours is not None and ls.sleep_hours < 6.5:
            ctx.sleep_craving_pattern = "cravings reported with short sleep baseline"

    checkins = progress_repository.get_recent_checkins(db, user.id, days=7)
    ctx.recent_checkin_summary = summarize_recent_checkins(checkins)
    checkin_signals = summarize_checkin_signals(checkins)
    ctx.energy_trend_summary = checkin_signals.get("energy_trend_summary")
    ctx.hunger_1_10_trend_summary = checkin_signals.get("hunger_1_10_trend_summary")
    ctx.daily_craving_summary = checkin_signals.get("daily_craving_summary")
    ctx.eating_location_summary = checkin_signals.get("eating_location_summary")
    ctx.planned_eating_out_summary = checkin_signals.get("planned_eating_out_summary")
    ctx.symptom_summary = checkin_signals.get("symptom_summary")
    ctx.adherence_summary = checkin_signals.get("adherence_summary")
    ctx.progress_history_summary, ctx.body_response_summary = summarize_progress_history(db, user.id)
    ctx.meal_history_summary = summarize_meal_history(db, user.id)
    ctx.weekly_insights_summary = summarize_weekly_insights(db, user.id)

    # Current active plan
    plan = nutrition_repository.get_active_plan(db, user.id)
    if plan:
        ctx.current_plan_id = plan.id
        ctx.current_plan_title = plan.title
        ctx.current_plan_summary = plan.description
        ctx.active_plan_summary = summarize_active_plan(db, plan)

    ctx.active_calendar_summary = summarize_active_calendar(db, user.id)

    return ctx
