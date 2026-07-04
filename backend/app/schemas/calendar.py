"""
Calendar API schemas (Pydantic v2).

Covers GET /nutrition/calendar, POST /nutrition/calendar/generate-week,
and POST /nutrition/calendar/regenerate-day.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CalendarMealSchema(BaseModel):
    id: str
    meal_type: str
    title: str
    description: str | None = None
    portion_guidance: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    preparation_notes: str | None = None
    # Enriched meal fields
    meal_slot: str | None = None
    meal_order: int | None = None
    time_window_start: str | None = None
    time_window_end: str | None = None
    calories_estimate: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    food_items: list[dict] = Field(default_factory=list)
    workout_relation: str | None = None
    rest_day_note: str | None = None
    drink_guidance: str | None = None


class PlanDaySchema(BaseModel):
    id: str
    plan_date: str  # ISO date YYYY-MM-DD
    day_index: int
    title: str
    summary: str | None = None
    hydration_goal: str | None = None
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)
    meals: list[CalendarMealSchema] = Field(default_factory=list)
    # Enriched day fields
    diet_type: str | None = None
    diet_goal: str | None = None
    difficulty_level: str | None = None
    daily_calories: int | None = None
    daily_macros: dict | None = None
    day_type: str | None = None
    training_guidance: str | None = None
    sleep_wake_guidance: str | None = None
    wake_time: str | None = None
    sleep_time: str | None = None
    dinner_to_sleep_gap: str | None = None
    hydration_plan: str | None = None
    drinks_plan: str | None = None
    cheat_meal_guidance: str | None = None
    allowed_foods: list[str] = Field(default_factory=list)
    limited_foods: list[str] = Field(default_factory=list)
    forbidden_foods: list[str] = Field(default_factory=list)
    medical_warnings: list[str] = Field(default_factory=list)
    restaurant_party_travel_guidance: str | None = None
    supplements_vitamins_guidance: str | None = None
    progress_tracking_guidance: str | None = None
    adjustment_rules: str | None = None
    budget_tier: str | None = None
    budget_guidance: str | None = None
    shopping_notes: str | None = None


class CoverageSchema(BaseModel):
    planned_days_count: int
    missing_days_count: int
    next_unplanned_date: str | None = None


class RenewalStatusSchema(BaseModel):
    should_prompt_next_week: bool
    prompt_level: str  # none | info | warning
    current_week_day_number: int | None = None
    next_week_start_date: str | None = None
    next_week_end_date: str | None = None


class CalendarResponse(BaseModel):
    calendar_id: str | None = None
    locale: str
    start_date: str | None = None
    end_date: str | None = None
    days: list[PlanDaySchema] = Field(default_factory=list)
    coverage: CoverageSchema
    renewal_status: RenewalStatusSchema


class GenerateWeekRequest(BaseModel):
    start_date: str | None = Field(
        default=None,
        description="ISO date YYYY-MM-DD. If omitted, starts after latest planned day.",
    )
    force: bool = Field(
        default=False,
        description="If true, overwrite already-planned days in the target range.",
    )
    locale: str | None = Field(
        default=None,
        description="fa | en | ar. Defaults to user preference or fa.",
    )


class GenerateWeekResponse(BaseModel):
    locale: str
    generated_days: int
    skipped_days: int
    days: list[PlanDaySchema] = Field(default_factory=list)


class GenerateWeekJobCreated(BaseModel):
    job_id: str
    status: str
    stage: str
    current_day_index: int | None = None
    total_days: int = 7
    message: str
    error: str | None = None
    result: GenerateWeekResponse | None = None
    updated_at: str


class GenerateWeekJobStatus(GenerateWeekJobCreated):
    pass


class RegenerateDayRequest(BaseModel):
    plan_date: str = Field(..., description="ISO date YYYY-MM-DD")
    locale: str | None = Field(default=None, description="fa | en | ar")


class RegenerateDayResponse(BaseModel):
    locale: str
    plan_date: str
    day: PlanDaySchema
