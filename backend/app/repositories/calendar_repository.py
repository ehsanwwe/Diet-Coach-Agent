"""
CalendarRepository: DB access for multilingual rolling meal plan calendar.

Uses SQLAlchemy 2.x select() + session.execute() throughout.
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import UserLanguagePreference
from app.models.calendar import NutritionPlanCalendar, NutritionPlanDay, NutritionPlanDayMeal

VALID_LOCALES = frozenset({"fa", "en", "ar"})


# ─── Locale resolution ────────────────────────────────────────────────────────

def get_user_language(db: Session, user_id: str) -> str | None:
    result = db.execute(
        select(UserLanguagePreference).where(UserLanguagePreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    return pref.language_code if pref else None


def resolve_locale(request_locale: str | None, user_locale: str | None) -> str:
    if request_locale and request_locale in VALID_LOCALES:
        return request_locale
    if user_locale and user_locale in VALID_LOCALES:
        return user_locale
    return "fa"


# ─── NutritionPlanCalendar ────────────────────────────────────────────────────

def get_active_calendar(db: Session, user_id: str, locale: str) -> NutritionPlanCalendar | None:
    result = db.execute(
        select(NutritionPlanCalendar)
        .where(
            NutritionPlanCalendar.user_id == user_id,
            NutritionPlanCalendar.locale == locale,
            NutritionPlanCalendar.status == "active",
        )
        .order_by(NutritionPlanCalendar.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_or_create_calendar(
    db: Session, user_id: str, locale: str
) -> NutritionPlanCalendar:
    cal = get_active_calendar(db, user_id, locale)
    if cal is None:
        cal = NutritionPlanCalendar(user_id=user_id, locale=locale, status="active")
        db.add(cal)
        db.flush()
    return cal


def update_calendar_range(
    db: Session,
    calendar: NutritionPlanCalendar,
    start_date: date,
    end_date: date,
) -> NutritionPlanCalendar:
    if calendar.start_date is None or start_date < calendar.start_date:
        calendar.start_date = start_date
    if calendar.end_date is None or end_date > calendar.end_date:
        calendar.end_date = end_date
    db.flush()
    return calendar


# ─── NutritionPlanDay ─────────────────────────────────────────────────────────

def get_plan_days(
    db: Session,
    user_id: str,
    locale: str,
    start_date: date,
    end_date: date,
) -> list[NutritionPlanDay]:
    result = db.execute(
        select(NutritionPlanDay)
        .where(
            NutritionPlanDay.user_id == user_id,
            NutritionPlanDay.locale == locale,
            NutritionPlanDay.plan_date >= start_date,
            NutritionPlanDay.plan_date <= end_date,
        )
        .order_by(NutritionPlanDay.plan_date)
    )
    return list(result.scalars().all())


def get_all_plan_dates(db: Session, user_id: str, locale: str) -> list[date]:
    result = db.execute(
        select(NutritionPlanDay.plan_date)
        .where(
            NutritionPlanDay.user_id == user_id,
            NutritionPlanDay.locale == locale,
        )
        .order_by(NutritionPlanDay.plan_date)
    )
    return [row[0] for row in result.all()]


def get_latest_plan_date(db: Session, user_id: str, locale: str) -> date | None:
    result = db.execute(
        select(NutritionPlanDay.plan_date)
        .where(
            NutritionPlanDay.user_id == user_id,
            NutritionPlanDay.locale == locale,
        )
        .order_by(NutritionPlanDay.plan_date.desc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


def get_day_by_date(
    db: Session, user_id: str, plan_date: date, locale: str
) -> NutritionPlanDay | None:
    result = db.execute(
        select(NutritionPlanDay).where(
            NutritionPlanDay.user_id == user_id,
            NutritionPlanDay.plan_date == plan_date,
            NutritionPlanDay.locale == locale,
        )
    )
    return result.scalar_one_or_none()


def day_exists(db: Session, user_id: str, plan_date: date, locale: str) -> bool:
    return get_day_by_date(db, user_id, plan_date, locale) is not None


def create_plan_day(
    db: Session,
    *,
    calendar_id: str,
    user_id: str,
    locale: str,
    plan_date: date,
    day_index: int,
    title: str,
    summary: str | None,
    hydration_goal: str | None,
    notes: str | None,
    warnings: list[str] | None,
) -> NutritionPlanDay:
    day = NutritionPlanDay(
        calendar_id=calendar_id,
        user_id=user_id,
        locale=locale,
        plan_date=plan_date,
        day_index=day_index,
        title=title,
        summary=summary,
        hydration_goal=hydration_goal,
        notes=notes,
        warnings=json.dumps(warnings or [], ensure_ascii=False),
    )
    db.add(day)
    db.flush()
    return day


def delete_plan_day(db: Session, day: NutritionPlanDay) -> None:
    db.delete(day)
    db.flush()


# ─── NutritionPlanDayMeal ─────────────────────────────────────────────────────

def get_day_meals(db: Session, plan_day_id: str) -> list[NutritionPlanDayMeal]:
    result = db.execute(
        select(NutritionPlanDayMeal)
        .where(NutritionPlanDayMeal.plan_day_id == plan_day_id)
        .order_by(NutritionPlanDayMeal.id)
    )
    return list(result.scalars().all())


def create_plan_day_meal(
    db: Session,
    *,
    plan_day_id: str,
    locale: str,
    meal_type: str,
    title: str,
    description: str | None,
    portion_guidance: str | None,
    alternatives: list[str] | None,
    preparation_notes: str | None,
) -> NutritionPlanDayMeal:
    meal = NutritionPlanDayMeal(
        plan_day_id=plan_day_id,
        locale=locale,
        meal_type=meal_type,
        title=title,
        description=description,
        portion_guidance=portion_guidance,
        alternatives=json.dumps(alternatives or [], ensure_ascii=False),
        preparation_notes=preparation_notes,
    )
    db.add(meal)
    db.flush()
    return meal


def decode_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
