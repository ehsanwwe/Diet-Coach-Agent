"""Progress API request/response schemas (Pydantic v2). PROG-01, PROG-02, PROG-03."""
from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class CheckInRequest(BaseModel):
    check_date: date
    weight_kg: float | None = Field(None, ge=20, le=300)
    waist_cm: float | None = Field(None, ge=30, le=250)
    hunger_level: int | None = Field(None, ge=1, le=5)
    hunger_level_1_10: int | None = Field(None, ge=1, le=10)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    sleep_quality: int | None = Field(None, ge=1, le=5)
    energy_level: int | None = Field(None, ge=1, le=5)
    stress_level: int | None = Field(None, ge=1, le=5)
    activity_minutes: int | None = Field(None, ge=0, le=1440)
    cravings: str | None = Field(None, max_length=1000)
    craving_type: str | None = Field(None, max_length=100)
    eating_location: str | None = Field(None, max_length=50)
    planned_eating_out: bool | None = None
    adherence_level: int | None = Field(None, ge=1, le=5)
    symptoms: str | None = Field(None, max_length=1000)
    adherence_notes: str | None = Field(None, max_length=2000)


class CheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    check_date: date
    weight_kg: float | None
    waist_cm: float | None = None
    hunger_level: int | None
    hunger_level_1_10: int | None = None
    sleep_hours: float | None
    sleep_quality: int | None = None
    energy_level: int | None = None
    stress_level: int | None
    activity_minutes: int | None
    cravings: str | None = None
    craving_type: str | None = None
    eating_location: str | None = None
    planned_eating_out: bool | None = None
    adherence_level: int | None = None
    symptoms: str | None = None
    adherence_notes: str | None
    adaptation_hint: bool = False
    human_review_recommended: bool = False
    safety_notes: list[str] = Field(default_factory=list)
    created_at: datetime


class BehaviorWin(BaseModel):
    key: str            # stable id: "sleep" | "activity" | "logging" | "low_stress" | "low_hunger" | "hydration" | "protein" | "fiber"
    label_key: str      # dictionary key, e.g. "winSleep"
    achieved: bool
    value: str | None = None   # e.g. "7.2"
    tracked: bool = True        # false for protein/fiber/hydration in v1


class WeightTrend(BaseModel):
    first: float
    last: float
    delta: float


class ProgressSummaryResponse(BaseModel):
    has_data: bool
    recent_checkins: list[CheckInResponse] = Field(default_factory=list)
    weight_series: list[float] = Field(default_factory=list)
    latest_weight_kg: float | None = None
    weight_trend: WeightTrend | None = None
    avg_energy_level: float | None = None
    avg_hunger_level_1_10: float | None = None
    craving_summary: str | None = None
    eating_location_summary: str | None = None
    symptom_summary: str | None = None
    adaptation_hint: bool = False
    human_review_recommended: bool = False
    behavior_wins: list[BehaviorWin] = Field(default_factory=list)
    logging_streak: int = 0
    empty_state_message: str | None = None


class WeeklyReportData(BaseModel):
    weight_trend: WeightTrend | None = None
    weight_series: list[float] = Field(default_factory=list)
    avg_hunger: float | None = None
    avg_hunger_level_1_10: float | None = None
    avg_sleep: float | None = None
    avg_sleep_quality: float | None = None
    avg_energy_level: float | None = None
    avg_stress: float | None = None
    total_activity_minutes: int = 0
    logging_days: int = 0
    adherence_pct: int = 0
    craving_summary: str | None = None
    eating_location_summary: str | None = None
    symptom_summary: str | None = None
    adaptation_hint: bool = False
    human_review_recommended: bool = False
    sleep_stress_note: str | None = None
    suggested_focus: str


class WeeklyReportResponse(BaseModel):
    has_report: bool
    week_start: date | None = None
    week_end: date | None = None
    report: WeeklyReportData | None = None
    empty_state_message: str | None = None
