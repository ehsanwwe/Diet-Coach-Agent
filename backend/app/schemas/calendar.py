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


class RegenerateDayRequest(BaseModel):
    plan_date: str = Field(..., description="ISO date YYYY-MM-DD")
    locale: str | None = Field(default=None, description="fa | en | ar")


class RegenerateDayResponse(BaseModel):
    locale: str
    plan_date: str
    day: PlanDaySchema
