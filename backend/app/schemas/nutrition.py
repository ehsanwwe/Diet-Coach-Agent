"""
Nutrition API request/response schemas (Pydantic v2).

Covers all 6 nutrition endpoints: profile, plan GET, plan generate,
meal analyze, what-to-eat-now, and adapt-plan.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ─── Shared sub-schemas ───────────────────────────────────────────────────────

class DailyGuidelines(BaseModel):
    calories: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    water_liters: float | None = None
    notes: str | None = None


class MealItem(BaseModel):
    id: str | None = None
    meal_time: str
    name: str
    description: str | None = None
    calories_estimate: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    notes: str | None = None
    order_index: int = 0


class FoodOption(BaseModel):
    name: str
    description: str | None = None
    calories_estimate: int | None = None
    prep_time_minutes: int | None = None
    tags: list[str] = Field(default_factory=list)


# ─── Profile sub-schemas ──────────────────────────────────────────────────────

class ProfileSummary(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    target_weight_kg: float | None = None
    gender: str | None = None
    age: int | None = None
    goal_type: str | None = None


class MedicalSummary(BaseModel):
    active_conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    has_warning_symptoms: bool = False


class LifestyleSummary(BaseModel):
    activity_level: str | None = None
    sleep_hours: float | None = None
    stress_level: int | None = None
    work_schedule: str | None = None
    cooking_ability: int | None = None
    food_budget: str | None = None


class PreferencesSummary(BaseModel):
    vegetarian: bool = False
    vegan: bool = False
    halal: bool = True
    likes_iranian_food: bool = True
    disliked_foods: list[str] = Field(default_factory=list)
    favorite_foods: list[str] = Field(default_factory=list)


class BehaviorSummary(BaseModel):
    emotional_eating: bool = False
    night_eating: bool = False
    meal_skipping: bool = False
    motivation_level: int | None = None


# ─── 1. GET /nutrition/profile ────────────────────────────────────────────────

class NutritionProfileResponse(BaseModel):
    user_id: str
    onboarding_complete: bool
    risk_level: str
    clinical_review_required: bool
    profile: ProfileSummary | None = None
    medical: MedicalSummary | None = None
    lifestyle: LifestyleSummary | None = None
    preferences: PreferencesSummary | None = None
    behavior: BehaviorSummary | None = None
    missing_sections: list[str] = Field(default_factory=list)


# ─── 2. GET /nutrition/plan ───────────────────────────────────────────────────

class NutritionPlanResponse(BaseModel):
    has_plan: bool
    plan_id: str | None = None
    status: str | None = None
    risk_level: str | None = None
    plan_type: str | None = None
    profile_complete: bool | None = None
    missing_fields: list[str] = Field(default_factory=list)
    summary: str | None = None
    daily_guidelines: DailyGuidelines | None = None
    meals: list[MealItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provider: str | None = None
    is_mock: bool = True
    generated_at: datetime | None = None


# ─── 3. POST /nutrition/plan/generate ────────────────────────────────────────

class NutritionPlanGenerateResponse(NutritionPlanResponse):
    pass


# ─── 4. POST /nutrition/meal/analyze ─────────────────────────────────────────

class MealAnalyzeRequest(BaseModel):
    meal_text: str = Field(..., min_length=3, max_length=2000)
    meal_time: Literal["breakfast", "lunch", "dinner", "snack", "unknown"] = "unknown"
    context: str | None = Field(default=None, max_length=500)


class MealAnalysisResponse(BaseModel):
    meal_id: str | None = None
    quality_score: int | None = None
    analysis_summary: str
    protein: str = ""
    fiber: str = ""
    sugar: str = ""
    balance: str = ""
    portion: str = ""
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provider: str = "mock"
    is_mock: bool = True


# ─── 5. POST /nutrition/what-to-eat-now ──────────────────────────────────────

class WhatToEatNowRequest(BaseModel):
    available_foods: list[str] = Field(default_factory=list, max_length=20)
    hunger_level: Literal["low", "medium", "high"] = "medium"
    meal_context: str | None = Field(default=None, max_length=500)
    time_available_minutes: int | None = Field(default=None, ge=1, le=180)


class WhatToEatNowResponse(BaseModel):
    options: list[FoodOption] = Field(default_factory=list)
    reasoning_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    provider: str = "mock"
    is_mock: bool = True


# ─── 6. POST /nutrition/adapt-plan ───────────────────────────────────────────

class AdaptPlanRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)
    recent_hunger: str | None = Field(default=None, max_length=200)
    recent_sleep: str | None = Field(default=None, max_length=200)
    recent_stress: str | None = Field(default=None, max_length=200)
    recent_adherence: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)


class AdaptPlanResponse(BaseModel):
    plan_id: str | None = None
    changes: list[str] = Field(default_factory=list)
    updated_guidelines: DailyGuidelines | None = None
    warnings: list[str] = Field(default_factory=list)
    revision_applied: bool = False
    revision_scope: Literal["none", "next_meal", "today", "remaining_day", "week", "guidance_only"] = "none"
    revised_date: str | None = None
    changed_items: list[str] = Field(default_factory=list)
    reason_for_changes: str | None = None
    safety_notes: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    fallback_reason: str | None = None
    provider: str = "mock"
    is_mock: bool = True
