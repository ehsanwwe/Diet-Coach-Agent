"""
Pydantic contracts for structured AI provider outputs.

These schemas validate provider JSON before nutrition services consume it.
They are intentionally tolerant of extra fields so existing providers can add
metadata without breaking endpoints, while required user-facing fields must
still be present and correctly shaped.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _AIBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class AIDailyGuidelines(_AIBaseModel):
    calories: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    water_liters: float | None = None
    notes: str | None = None


class AIPlanMeal(_AIBaseModel):
    meal_time: Literal["breakfast", "lunch", "dinner", "snack"]
    name: str = Field(min_length=1)
    description: str | None = None
    calories_estimate: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    notes: str | None = None


class AIPlanResponse(_AIBaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    daily_guidelines: AIDailyGuidelines
    meals: list[AIPlanMeal] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assessment_summary: str | None = None
    nutrition_diagnosis: str | None = None
    intervention_summary: str | None = None
    monitoring_notes: str | None = None


class AIMealAnalysisResponse(_AIBaseModel):
    quality_score: int | None = Field(default=None, ge=1, le=10)
    analysis_summary: str = Field(min_length=1)
    protein: str = ""
    fiber: str = ""
    sugar: str = ""
    balance: str = ""
    portion: str = ""
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assessment_summary: str | None = None
    nutrition_diagnosis: str | None = None
    intervention_summary: str | None = None
    monitoring_notes: str | None = None


class AIFoodOption(_AIBaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    calories_estimate: int | None = None
    prep_time_minutes: int | None = None
    tags: list[str] = Field(default_factory=list)


class AIWhatToEatNowResponse(_AIBaseModel):
    options: list[AIFoodOption] = Field(min_length=1)
    reasoning_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    assessment_summary: str | None = None
    intervention_summary: str | None = None
    monitoring_notes: str | None = None


class AIChatResponse(_AIBaseModel):
    reply: str = Field(min_length=1)
    assessment_summary: str | None = None
    monitoring_notes: str | None = None


class AIWeekMeal(_AIBaseModel):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    portion_guidance: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    preparation_notes: str | None = None


class AIWeekDay(_AIBaseModel):
    day_index: int = Field(ge=1, le=7)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    hydration_goal: str | None = None
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)
    meals: list[AIWeekMeal] = Field(min_length=1)
    assessment_summary: str | None = None
    intervention_summary: str | None = None
    monitoring_notes: str | None = None


class AIWeekPlanResponse(_AIBaseModel):
    locale: Literal["fa", "en", "ar"]
    days: list[AIWeekDay] = Field(min_length=7)


class AIAdaptPlanResponse(_AIBaseModel):
    changes: list[str] = Field(default_factory=list)
    updated_guidelines: AIDailyGuidelines | None = None
    warnings: list[str] = Field(default_factory=list)
    summary: str | None = None
    assessment_summary: str | None = None
    nutrition_diagnosis: str | None = None
    intervention_summary: str | None = None
    monitoring_notes: str | None = None
    revised_meals: list[AIWeekMeal] = Field(default_factory=list)
    revised_day: AIWeekDay | None = None
    changed_items: list[str] = Field(default_factory=list)
    reason_for_changes: str | None = None
    safety_notes: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    follow_up_question: str | None = None


AI_TASK_SCHEMAS: dict[str, type[_AIBaseModel]] = {
    "generate_plan": AIPlanResponse,
    "analyze_meal": AIMealAnalysisResponse,
    "what_to_eat_now": AIWhatToEatNowResponse,
    "chat_message": AIChatResponse,
    "generate_week_fa": AIWeekPlanResponse,
    "generate_week_en": AIWeekPlanResponse,
    "generate_week_ar": AIWeekPlanResponse,
    "adapt_plan": AIAdaptPlanResponse,
}
