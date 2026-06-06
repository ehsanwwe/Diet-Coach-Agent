"""
CalendarService: rolling multilingual meal plan calendar logic.

Locale resolution order: request_locale > user pref > fa (default).
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import calendar_repository
from app.schemas.calendar import (
    CalendarMealSchema,
    CalendarResponse,
    CoverageSchema,
    GenerateWeekResponse,
    PlanDaySchema,
    RegenerateDayResponse,
    RenewalStatusSchema,
)
from app.services import nutrition_memory_service
from app.services.nutrition_agent_service import NutritionAgentService

logger = logging.getLogger(__name__)

_CLINICAL_WARNING_FA = (
    "بر اساس وضعیت پزشکی شما، پیش از اجرای این برنامه با پزشک یا متخصص تغذیه مشورت کنید."
)
_CLINICAL_WARNING_EN = (
    "Based on your medical profile, consult a doctor or dietitian before following this plan."
)
_CLINICAL_WARNING_AR = (
    "بناءً على وضعك الطبي، استشر طبيباً أو أخصائي تغذية قبل اتباع هذه الخطة."
)
_CLINICAL_WARNINGS = {"fa": _CLINICAL_WARNING_FA, "en": _CLINICAL_WARNING_EN, "ar": _CLINICAL_WARNING_AR}


def resolve_locale(db: Session, user: User, request_locale: str | None) -> str:
    user_lang = calendar_repository.get_user_language(db, user.id)
    return calendar_repository.resolve_locale(request_locale, user_lang)


def _day_to_schema(db: Session, day) -> PlanDaySchema:
    meals_db = calendar_repository.get_day_meals(db, day.id)
    meals = [
        CalendarMealSchema(
            id=m.id,
            meal_type=m.meal_type,
            title=m.title,
            description=m.description,
            portion_guidance=m.portion_guidance,
            alternatives=calendar_repository.decode_json_list(m.alternatives),
            preparation_notes=m.preparation_notes,
        )
        for m in meals_db
    ]
    return PlanDaySchema(
        id=day.id,
        plan_date=day.plan_date.isoformat(),
        day_index=day.day_index,
        title=day.title,
        summary=day.summary,
        hydration_goal=day.hydration_goal,
        notes=day.notes,
        warnings=calendar_repository.decode_json_list(day.warnings),
        meals=meals,
    )


def _compute_renewal_status(
    all_dates: list[date], today: date
) -> RenewalStatusSchema:
    if not all_dates:
        next_week_start = today
        next_week_end = today + timedelta(days=6)
        return RenewalStatusSchema(
            should_prompt_next_week=True,
            prompt_level="info",
            current_week_day_number=None,
            next_week_start_date=next_week_start.isoformat(),
            next_week_end_date=next_week_end.isoformat(),
        )

    sorted_dates = sorted(all_dates)
    earliest = sorted_dates[0]
    future_dates = [d for d in sorted_dates if d >= today]
    remaining = len(future_dates)

    if remaining == 0:
        next_week_start = today
        next_week_end = today + timedelta(days=6)
        return RenewalStatusSchema(
            should_prompt_next_week=True,
            prompt_level="warning",
            current_week_day_number=None,
            next_week_start_date=next_week_start.isoformat(),
            next_week_end_date=next_week_end.isoformat(),
        )

    days_since_start = max(0, (today - earliest).days)
    current_week_num = days_since_start // 7
    current_week_start = earliest + timedelta(days=current_week_num * 7)
    current_day_in_week = (today - current_week_start).days + 1

    next_week_start = current_week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)

    next_week_dates = [d for d in sorted_dates if next_week_start <= d <= next_week_end]
    next_week_planned = len(next_week_dates) > 0

    if remaining <= 2:
        prompt_level = "warning"
        should_prompt = True
    elif current_day_in_week >= 5 and not next_week_planned:
        prompt_level = "info"
        should_prompt = True
    else:
        prompt_level = "none"
        should_prompt = False

    return RenewalStatusSchema(
        should_prompt_next_week=should_prompt,
        prompt_level=prompt_level,
        current_week_day_number=current_day_in_week,
        next_week_start_date=next_week_start.isoformat(),
        next_week_end_date=next_week_end.isoformat(),
    )


def get_calendar(
    db: Session,
    user: User,
    locale: str,
    start_date: date | None,
    days: int,
) -> CalendarResponse:
    effective_start = start_date or date.today()
    effective_end = effective_start + timedelta(days=days - 1)

    cal = calendar_repository.get_active_calendar(db, user.id, locale)
    plan_days = calendar_repository.get_plan_days(
        db, user.id, locale, effective_start, effective_end
    )
    day_schemas = [_day_to_schema(db, d) for d in plan_days]

    # Coverage
    all_dates_in_range = {effective_start + timedelta(i) for i in range(days)}
    planned_dates_in_range = {date.fromisoformat(d.plan_date) for d in day_schemas}
    missing = sorted(all_dates_in_range - planned_dates_in_range)
    next_unplanned = missing[0].isoformat() if missing else None

    coverage = CoverageSchema(
        planned_days_count=len(planned_dates_in_range),
        missing_days_count=len(missing),
        next_unplanned_date=next_unplanned,
    )

    all_dates = calendar_repository.get_all_plan_dates(db, user.id, locale)
    renewal = _compute_renewal_status(all_dates, date.today())

    return CalendarResponse(
        calendar_id=cal.id if cal else None,
        locale=locale,
        start_date=effective_start.isoformat(),
        end_date=effective_end.isoformat(),
        days=day_schemas,
        coverage=coverage,
        renewal_status=renewal,
    )


def generate_week(
    db: Session,
    user: User,
    locale: str,
    start_date: date | None,
    force: bool,
) -> GenerateWeekResponse:
    # Determine start date
    if start_date is None:
        latest = calendar_repository.get_latest_plan_date(db, user.id, locale)
        if latest is None:
            start_date = date.today()
        else:
            start_date = latest + timedelta(days=1)

    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()
    plan_data, result = agent.generate_week_plan(ctx, locale)

    days_raw: list[dict] = plan_data.get("days") or []
    # Clamp to exactly 7
    days_raw = days_raw[:7]

    cal = calendar_repository.get_or_create_calendar(db, user.id, locale)
    generated: list[PlanDaySchema] = []
    skipped = 0

    clinical_warning = _CLINICAL_WARNINGS.get(locale, _CLINICAL_WARNING_FA) if ctx.clinical_review_required else None

    for i, day_raw in enumerate(days_raw):
        plan_date = start_date + timedelta(days=i)

        if not force and calendar_repository.day_exists(db, user.id, plan_date, locale):
            skipped += 1
            continue

        existing = calendar_repository.get_day_by_date(db, user.id, plan_date, locale)
        if existing and force:
            calendar_repository.delete_plan_day(db, existing)

        raw_warnings: list[str] = list(day_raw.get("warnings") or [])
        if clinical_warning and clinical_warning not in raw_warnings:
            raw_warnings.append(clinical_warning)

        day = calendar_repository.create_plan_day(
            db,
            calendar_id=cal.id,
            user_id=user.id,
            locale=locale,
            plan_date=plan_date,
            day_index=i + 1,
            title=day_raw.get("title") or f"Day {i + 1}",
            summary=day_raw.get("summary"),
            hydration_goal=day_raw.get("hydration_goal"),
            notes=day_raw.get("notes"),
            warnings=raw_warnings,
        )

        meals_raw: list[dict] = day_raw.get("meals") or []
        for meal_raw in meals_raw:
            calendar_repository.create_plan_day_meal(
                db,
                plan_day_id=day.id,
                locale=locale,
                meal_type=meal_raw.get("meal_type", "snack"),
                title=meal_raw.get("title", "—"),
                description=meal_raw.get("description"),
                portion_guidance=meal_raw.get("portion_guidance"),
                alternatives=meal_raw.get("alternatives") or [],
                preparation_notes=meal_raw.get("preparation_notes"),
            )

        generated.append(_day_to_schema(db, day))

    # Update calendar range
    if generated:
        all_dates = [date.fromisoformat(d.plan_date) for d in generated]
        calendar_repository.update_calendar_range(db, cal, min(all_dates), max(all_dates))

    db.commit()

    return GenerateWeekResponse(
        locale=locale,
        generated_days=len(generated),
        skipped_days=skipped,
        days=generated,
    )


def regenerate_day(
    db: Session,
    user: User,
    locale: str,
    plan_date: date,
) -> RegenerateDayResponse:
    existing = calendar_repository.get_day_by_date(db, user.id, plan_date, locale)
    if existing:
        calendar_repository.delete_plan_day(db, existing)

    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()
    plan_data, _ = agent.generate_week_plan(ctx, locale)

    days_raw: list[dict] = plan_data.get("days") or []
    day_raw = days_raw[0] if days_raw else {}

    cal = calendar_repository.get_or_create_calendar(db, user.id, locale)
    raw_warnings: list[str] = list(day_raw.get("warnings") or [])
    if ctx.clinical_review_required:
        cw = _CLINICAL_WARNINGS.get(locale, _CLINICAL_WARNING_FA)
        if cw not in raw_warnings:
            raw_warnings.append(cw)

    day = calendar_repository.create_plan_day(
        db,
        calendar_id=cal.id,
        user_id=user.id,
        locale=locale,
        plan_date=plan_date,
        day_index=1,
        title=day_raw.get("title") or "—",
        summary=day_raw.get("summary"),
        hydration_goal=day_raw.get("hydration_goal"),
        notes=day_raw.get("notes"),
        warnings=raw_warnings,
    )
    for meal_raw in (day_raw.get("meals") or []):
        calendar_repository.create_plan_day_meal(
            db,
            plan_day_id=day.id,
            locale=locale,
            meal_type=meal_raw.get("meal_type", "snack"),
            title=meal_raw.get("title", "—"),
            description=meal_raw.get("description"),
            portion_guidance=meal_raw.get("portion_guidance"),
            alternatives=meal_raw.get("alternatives") or [],
            preparation_notes=meal_raw.get("preparation_notes"),
        )

    db.commit()
    return RegenerateDayResponse(
        locale=locale,
        plan_date=plan_date.isoformat(),
        day=_day_to_schema(db, day),
    )
