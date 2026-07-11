"""
Onboarding step request/response Pydantic v2 schemas.

Covers all 5 data-collection steps + goal step + status + complete.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ─── Shared literals ──────────────────────────────────────────────────────────

RiskLevel = Literal["low", "medium", "high", "clinical_review_required"]

ONBOARDING_STEP_ORDER = ["profile", "medical", "lifestyle", "preferences", "behavior"]


# ─── Goal ─────────────────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    goal_types: list[str] = Field(..., min_length=1)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    goal_types: list[str]

    @field_validator("goal_types", mode="before")
    @classmethod
    def deserialize_goal_types(cls, v: object) -> list[str]:
        """Read goal_types_json first; fall back to wrapping legacy goal_type."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else [result]
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return []

MEDICAL_CONDITION_CODES = [
    "diabetes",
    "kidney_disease",
    "liver_disease",
    "thyroid_issues",
    "high_blood_pressure",
    "high_cholesterol",
    "pcos",
    "pregnancy_breastfeeding",
    "eating_disorder_history",
    "bariatric_surgery",
]

FEMALE_ONLY_GOAL_TYPES = frozenset({
    "pcos_support",
    "pregnancy_breastfeeding_caution",
})

FEMALE_ONLY_MEDICAL_FIELDS = frozenset({
    "pcos",
    "pregnancy_breastfeeding",
})


# ─── Step 1: Profile ──────────────────────────────────────────────────────────

class ProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    gender: Literal["male", "female", "other", "prefer_not_to_say"]
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=8, le=120)
    height_cm: float = Field(..., ge=80.0, le=230.0)
    current_weight_kg: float = Field(..., ge=20.0, le=300.0)
    target_weight_kg: float | None = Field(default=None, ge=20.0, le=300.0)
    waist_circumference_cm: float | None = Field(default=None, ge=40.0, le=200.0)
    wrist_circumference_cm: float | None = Field(default=None, ge=8.0, le=35.0)
    thigh_circumference_cm: float | None = Field(default=None, ge=30.0, le=100.0)

    @model_validator(mode="after")
    def require_age_or_birth_date(self) -> "ProfileRequest":
        if self.birth_date is None and self.age is None:
            raise ValueError("Either birth_date or age must be provided")
        return self


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str | None
    gender: str | None
    height_cm: float | None
    weight_kg: float | None
    target_weight_kg: float | None
    waist_cm: float | None
    wrist_cm: float | None = None
    thigh_cm: float | None = None


# ─── Step 2: Medical ──────────────────────────────────────────────────────────

class MedicalRequest(BaseModel):
    diabetes: bool = False
    kidney_disease: bool = False
    liver_disease: bool = False
    thyroid_issues: bool = False
    high_blood_pressure: bool = False
    high_cholesterol: bool = False
    pcos: bool = False
    pregnancy_breastfeeding: bool = False
    eating_disorder_history: bool = False
    bariatric_surgery: bool = False
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    warning_symptoms: list[str] = Field(default_factory=list)

    def condition_flags(self) -> dict[str, bool]:
        """Return the 10 standard condition codes as a dict."""
        return {
            "diabetes": self.diabetes,
            "kidney_disease": self.kidney_disease,
            "liver_disease": self.liver_disease,
            "thyroid_issues": self.thyroid_issues,
            "high_blood_pressure": self.high_blood_pressure,
            "high_cholesterol": self.high_cholesterol,
            "pcos": self.pcos,
            "pregnancy_breastfeeding": self.pregnancy_breastfeeding,
            "eating_disorder_history": self.eating_disorder_history,
            "bariatric_surgery": self.bariatric_surgery,
        }


class MedicalFlagItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    condition_code: str
    has_condition: bool


class MedicalResponse(BaseModel):
    flags: list[MedicalFlagItem]
    medications: list[str]
    allergies: list[str]
    warning_symptoms: list[str]
    risk_level: RiskLevel
    risk_flags: list[str]
    clinical_review_required: bool


# ─── Step 3: Lifestyle ────────────────────────────────────────────────────────

class LifestyleRequest(BaseModel):
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    stress_level: int = Field(..., ge=1, le=10)
    work_schedule: str = Field(..., max_length=50)
    activity_level: str = Field(..., max_length=50)
    exercise_days_per_week: int = Field(..., ge=0, le=7)
    cooking_ability: int = Field(..., ge=1, le=5)
    food_budget: str = Field(..., max_length=50)
    eating_out_frequency: str | None = Field(None, max_length=50)
    travel_frequency: str | None = Field(None, max_length=50)


class LifestyleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    sleep_hours: float | None
    stress_level: int | None
    work_schedule: str | None
    activity_level: str | None
    exercise_days_per_week: int | None
    cooking_ability: int | None
    food_budget: str | None
    eating_out_frequency: str | None
    travel_frequency: str | None


# ─── Step 4: Preferences ─────────────────────────────────────────────────────

class PreferencesRequest(BaseModel):
    likes_iranian_food: bool = True
    vegetarian: bool = False
    vegan: bool = False
    halal: bool = True
    disliked_foods: list[str] = Field(default_factory=list)
    favorite_foods: list[str] = Field(default_factory=list)
    breakfast_habit: str = Field(default="", max_length=50)
    rice_frequency: str = Field(default="", max_length=50)
    bread_frequency: str = Field(default="", max_length=50)
    sweets_frequency: str = Field(default="", max_length=50)
    tea_frequency: str = Field(default="", max_length=50)
    restaurant_frequency: str = Field(default="", max_length=50)


class PreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    likes_iranian_food: bool
    vegetarian: bool
    vegan: bool
    halal: bool
    disliked_foods: list[str]
    favorite_foods: list[str]
    breakfast_habit: str | None = None
    rice_frequency: str | None = None
    bread_frequency: str | None = None
    sweets_frequency: str | None = None
    tea_frequency: str | None = None
    restaurant_frequency: str | None = None

    @field_validator("disliked_foods", "favorite_foods", mode="before")
    @classmethod
    def deserialize_text_list(cls, v: object) -> list[str]:
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else []
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return v if isinstance(v, list) else []


# ─── Step 5: Behavior ────────────────────────────────────────────────────────

class BehaviorRequest(BaseModel):
    emotional_eating: bool = False
    night_eating: bool = False
    meal_skipping: bool = False
    cravings: list[str] = Field(default_factory=list)
    binge_history: bool = False
    diet_history: str = Field(default="", max_length=2000)
    previous_failures: str = Field(default="", max_length=2000)
    hunger_patterns: list[str] = Field(default_factory=list)
    motivation_level: int = Field(default=5, ge=1, le=10)


class BehaviorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    emotional_eating: bool
    night_eating: bool
    meal_skipping: bool
    cravings: list[str]
    binge_history: bool
    diet_history: str | None = None
    previous_failures: str | None = None
    hunger_patterns: list[str] = Field(default_factory=list)
    motivation_level: int | None = None

    @field_validator("cravings", mode="before")
    @classmethod
    def deserialize_cravings(cls, v: object) -> list[str]:
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else []
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return v if isinstance(v, list) else []

    @field_validator("hunger_patterns", mode="before")
    @classmethod
    def deserialize_hunger_patterns(cls, v: object) -> list[str]:
        """Read hunger_patterns JSON; fall back to wrapping legacy hunger_pattern."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else [result]
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return []


# ─── Status ───────────────────────────────────────────────────────────────────

class OnboardingStatusResponse(BaseModel):
    user_id: str
    is_onboarded: bool
    completed_steps: list[str]
    next_step: str | None
    risk_level: str | None
    profile_exists: bool
    medical_exists: bool
    lifestyle_exists: bool
    preferences_exists: bool
    behavior_exists: bool
    gender: str | None = None


# ─── Complete ─────────────────────────────────────────────────────────────────

class OnboardingCompleteResponse(BaseModel):
    user_id: str
    is_onboarded: bool
    risk_level: str
    clinical_review_required: bool
    risk_flags: list[str]
    completed_steps: list[str]
    message: str
