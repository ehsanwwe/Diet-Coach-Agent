"""
CalendarRepository: DB access for multilingual rolling meal plan calendar.

Uses SQLAlchemy 2.x select() + session.execute() throughout.
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy import delete, select
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
    # Enriched fields
    diet_type: str | None = None,
    diet_goal: str | None = None,
    difficulty_level: str | None = None,
    daily_calories: int | None = None,
    daily_macros: dict | None = None,
    day_type: str | None = None,
    training_guidance: str | None = None,
    sleep_wake_guidance: str | None = None,
    wake_time: str | None = None,
    sleep_time: str | None = None,
    dinner_to_sleep_gap: str | None = None,
    hydration_plan: str | None = None,
    drinks_plan: str | None = None,
    cheat_meal_guidance: str | None = None,
    allowed_foods: list[str] | None = None,
    limited_foods: list[str] | None = None,
    forbidden_foods: list[str] | None = None,
    medical_warnings: list[str] | None = None,
    restaurant_party_travel_guidance: str | None = None,
    supplements_vitamins_guidance: str | None = None,
    progress_tracking_guidance: str | None = None,
    adjustment_rules: str | None = None,
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
        diet_type=diet_type,
        diet_goal=diet_goal,
        difficulty_level=difficulty_level,
        daily_calories=daily_calories,
        daily_macros=json.dumps(daily_macros, ensure_ascii=False) if daily_macros else None,
        day_type=day_type,
        training_guidance=training_guidance,
        sleep_wake_guidance=sleep_wake_guidance,
        wake_time=wake_time,
        sleep_time=sleep_time,
        dinner_to_sleep_gap=dinner_to_sleep_gap,
        hydration_plan=hydration_plan,
        drinks_plan=drinks_plan,
        cheat_meal_guidance=cheat_meal_guidance,
        allowed_foods=json.dumps(allowed_foods or [], ensure_ascii=False),
        limited_foods=json.dumps(limited_foods or [], ensure_ascii=False),
        forbidden_foods=json.dumps(forbidden_foods or [], ensure_ascii=False),
        medical_warnings=json.dumps(medical_warnings or [], ensure_ascii=False),
        restaurant_party_travel_guidance=restaurant_party_travel_guidance,
        supplements_vitamins_guidance=supplements_vitamins_guidance,
        progress_tracking_guidance=progress_tracking_guidance,
        adjustment_rules=adjustment_rules,
    )
    db.add(day)
    db.flush()
    return day


def delete_plan_day(db: Session, day: NutritionPlanDay) -> None:
    db.delete(day)
    db.flush()


def update_plan_day(
    db: Session,
    day: NutritionPlanDay,
    *,
    title: str | None = None,
    summary: str | None = None,
    hydration_goal: str | None = None,
    notes: str | None = None,
    warnings: list[str] | None = None,
) -> NutritionPlanDay:
    if title:
        day.title = title
    if summary is not None:
        day.summary = summary
    if hydration_goal is not None:
        day.hydration_goal = hydration_goal
    if notes is not None:
        day.notes = notes
    if warnings is not None:
        day.warnings = json.dumps(warnings, ensure_ascii=False)
    db.flush()
    return day


# ─── NutritionPlanDayMeal ─────────────────────────────────────────────────────

def get_day_meals(db: Session, plan_day_id: str) -> list[NutritionPlanDayMeal]:
    result = db.execute(
        select(NutritionPlanDayMeal)
        .where(NutritionPlanDayMeal.plan_day_id == plan_day_id)
        .order_by(NutritionPlanDayMeal.meal_order.asc().nulls_last(), NutritionPlanDayMeal.id)
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
    # Enriched fields
    meal_slot: str | None = None,
    meal_order: int | None = None,
    time_window_start: str | None = None,
    time_window_end: str | None = None,
    calories_estimate: int | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
    food_items: list[dict] | None = None,
    workout_relation: str | None = None,
    rest_day_note: str | None = None,
    drink_guidance: str | None = None,
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
        meal_slot=meal_slot or meal_type,
        meal_order=meal_order,
        time_window_start=time_window_start,
        time_window_end=time_window_end,
        calories_estimate=calories_estimate,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        food_items=json.dumps(food_items or [], ensure_ascii=False),
        workout_relation=workout_relation,
        rest_day_note=rest_day_note,
        drink_guidance=drink_guidance,
    )
    db.add(meal)
    db.flush()
    return meal


def replace_day_meals(
    db: Session,
    plan_day_id: str,
    *,
    locale: str,
    meals: list[dict],
) -> list[NutritionPlanDayMeal]:
    db.execute(delete(NutritionPlanDayMeal).where(NutritionPlanDayMeal.plan_day_id == plan_day_id))
    rows: list[NutritionPlanDayMeal] = []
    for meal in meals:
        rows.append(
            create_plan_day_meal(
                db,
                plan_day_id=plan_day_id,
                locale=locale,
                meal_type=meal.get("meal_type", "snack"),
                title=meal.get("title") or meal.get("name") or "—",
                description=meal.get("description"),
                portion_guidance=meal.get("portion_guidance") or meal.get("notes"),
                alternatives=meal.get("alternatives") or [],
                preparation_notes=meal.get("preparation_notes"),
            )
        )
    return rows


def decode_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def decode_json_dict(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None
