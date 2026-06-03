"""
NutritionMemoryService: collects and compacts user context from DB for AI prompts.

Returns NutritionMemoryContext — the single source of truth for all prompt building.
Raw file paths, tokens, and secrets are never included.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import onboarding_repository


@dataclass
class NutritionMemoryContext:
    user_id: str
    # Anthropometrics
    height_cm: float | None = None
    weight_kg: float | None = None
    target_weight_kg: float | None = None
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
    motivation_level: int | None = None
    # Current active plan
    current_plan_id: str | None = None
    current_plan_title: str | None = None
    current_plan_summary: str | None = None

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
        return d


def _calc_age(birth_date: date) -> int:
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


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
        ctx.motivation_level = bp.motivation_level

    # Current active plan
    plan = nutrition_repository.get_active_plan(db, user.id)
    if plan:
        ctx.current_plan_id = plan.id
        ctx.current_plan_title = plan.title
        ctx.current_plan_summary = plan.description

    return ctx
