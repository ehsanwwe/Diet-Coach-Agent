"""
NutritionService: business logic for all 6 nutrition endpoints.

Responsibilities:
- Collect user context via NutritionMemoryService
- Apply safety guardrails before AI calls
- Delegate AI work to NutritionAgentService
- Persist results via NutritionRepository
- Return structured response dicts
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import calendar_repository, nutrition_repository, onboarding_repository
from app.schemas.nutrition import (
    AdaptPlanRequest,
    AdaptPlanResponse,
    BehaviorSummary,
    DailyGuidelines,
    FoodOption,
    LifestyleSummary,
    MealAnalysisResponse,
    MealAnalyzeRequest,
    MealItem,
    MedicalSummary,
    NutritionPlanGenerateResponse,
    NutritionPlanResponse,
    NutritionProfileResponse,
    PreferencesSummary,
    ProfileSummary,
    WhatToEatNowRequest,
    WhatToEatNowResponse,
)
from app.services import nutrition_memory_service
from app.services.nutrition_agent_service import NutritionAgentService

_CLINICAL_REVIEW_WELLNESS_GUIDANCE = (
    "بر اساس اطلاعات پزشکی شما، لطفاً پیش از شروع هر برنامه غذایی با پزشک یا "
    "متخصص تغذیه مشورت کنید. این اپلیکیشن جایگزین مشاوره پزشکی نیست."
)

_HIGH_RISK_WELLNESS_GUIDANCE = (
    "با توجه به وضعیت سلامتی شما، مشاوره با متخصص تغذیه توصیه می‌شود. "
    "برنامه زیر راهنمایی کلی است و جایگزین نظر پزشک نمی‌شود."
)

_HIGH_RISK_CONSERVATIVE_SUMMARY = (
    "به دلیل ریسک سلامتی بالا، این بخش فقط راهنمایی کلی و محافظه‌کارانه ارائه می‌دهد. "
    "برای برنامه دقیق، مقدار کالری، یا تغییرات مرتبط با بیماری، لطفاً با پزشک یا متخصص تغذیه هماهنگ کنید."
)


# ─── Helper ───────────────────────────────────────────────────────────────────

_TEMPORARY_GUIDANCE_SUMMARY = (
    "برای ساخت یک برنامه غذایی کامل و شخصی‌سازی‌شده هنوز چند داده کلیدی کم است. "
    "تا تکمیل اطلاعات، این راهنمایی موقت فقط بر انتخاب‌های متعادل، وعده‌های منظم، آب کافی، "
    "و پرهیز از رژیم‌های سخت تمرکز دارد."
)

_TEMPORARY_GUIDANCE_NOTES = (
    "پس از تکمیل اطلاعات پایه، برنامه دقیق‌تر با وعده‌ها، جایگزین‌ها و هدف‌های قابل پایش ساخته می‌شود."
)


_ADAPT_NO_ACTIVE_PLAN_WARNING = (
    "فعلاً برنامه فعالی برای بازبینی پیدا نشد. تا ساخت برنامه، فقط راهنمایی ایمن و موقت ارائه می‌شود."
)
_ADAPT_HUMAN_REVIEW_WARNING = (
    "با توجه به ریسک یا علائم گزارش‌شده، قبل از تغییر جدی برنامه با پزشک یا متخصص تغذیه مشورت کنید."
)
_ADAPT_NO_EXTREME_COMPENSATION = (
    "برای جبران پرخوری یا لغزش، حذف وعده، روزه‌داری سخت، دیتاکس، پاکسازی یا ورزش افراطی توصیه نمی‌شود."
)


def _guidelines_from_dict(d: dict) -> DailyGuidelines | None:
    g = d.get("daily_guidelines") or d.get("updated_guidelines")
    if not g:
        return None
    return DailyGuidelines(
        calories=g.get("calories"),
        protein_g=g.get("protein_g"),
        carbs_g=g.get("carbs_g"),
        fat_g=g.get("fat_g"),
        fiber_g=g.get("fiber_g"),
        water_liters=g.get("water_liters"),
        notes=g.get("notes"),
    )


def _meal_items_from_list(meals: list[dict], plan_id: str | None = None) -> list[MealItem]:
    items = []
    for i, m in enumerate(meals):
        items.append(
            MealItem(
                id=None,
                meal_time=m.get("meal_time", "snack"),
                name=m.get("name", "وعده غذایی"),
                description=m.get("description"),
                calories_estimate=m.get("calories_estimate"),
                protein_g=m.get("protein_g"),
                carbs_g=m.get("carbs_g"),
                fat_g=m.get("fat_g"),
                notes=m.get("notes"),
                order_index=i,
            )
        )
    return items


def _missing_plan_profile_fields(db: Session, user: User, ctx) -> list[str]:
    """Return missing fields that block a full strict personalized plan."""
    missing: list[str] = []

    if ctx.age is None:
        missing.append("age_or_birth_date")
    if not ctx.gender:
        missing.append("gender")
    if ctx.height_cm is None:
        missing.append("height")
    if ctx.weight_kg is None:
        missing.append("current_weight")
    if not ctx.goal_type:
        missing.append("main_goal")
    if ctx.goal_type in {"weight_loss", "weight_gain", "muscle_gain"} and ctx.target_weight_kg is None:
        missing.append("target_weight")

    if (
        onboarding_repository.get_latest_risk_assessment(db, user.id) is None
        or not onboarding_repository.medical_data_exists(db, user.id)
    ):
        missing.append("medical_safety_screen")

    lifestyle = onboarding_repository.get_lifestyle(db, user.id)
    if lifestyle is None:
        missing.append("lifestyle_basics")
    else:
        if not ctx.activity_level:
            missing.append("activity_level")
        if ctx.cooking_ability is None:
            missing.append("cooking_ability")
        if not ctx.food_budget:
            missing.append("budget_or_food_access")

    if onboarding_repository.get_food_preference(db, user.id) is None:
        missing.append("food_preferences")

    if onboarding_repository.get_behavior_profile(db, user.id) is None:
        missing.append("behavior_or_diet_history")

    return list(dict.fromkeys(missing))


def _temporary_guidance_plan(missing_fields: list[str]) -> dict:
    return {
        "title": "راهنمایی موقت تغذیه",
        "summary": _TEMPORARY_GUIDANCE_SUMMARY,
        "daily_guidelines": {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "fiber_g": None,
            "water_liters": 2.0,
            "notes": _TEMPORARY_GUIDANCE_NOTES,
        },
        "meals": [],
        "warnings": [
            "برای برنامه کامل، اطلاعات بیشتری لازم است: " + "، ".join(missing_fields)
        ],
    }


def _adapt_text(body: AdaptPlanRequest) -> str:
    values = [
        body.reason,
        body.recent_hunger,
        body.recent_sleep,
        body.recent_stress,
        body.recent_adherence,
        body.notes,
    ]
    return " ".join(v for v in values if v).lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(k in text for k in keywords)


def _adapt_decision(
    db: Session,
    user: User,
    ctx,
    body: AdaptPlanRequest,
    plan_db,
) -> dict:
    text = _adapt_text(body)
    locale = calendar_repository.resolve_locale(None, calendar_repository.get_user_language(db, user.id))
    today = date.today()
    today_day = calendar_repository.get_day_by_date(db, user.id, today, locale)
    next_days = calendar_repository.get_plan_days(db, user.id, locale, today, today + timedelta(days=6))
    plan_meta = nutrition_repository.get_plan_metadata(plan_db) if plan_db else {}
    plan_type = plan_meta.get("plan_type")

    red_flag = _contains_any(text, (
        "chest pain", "blood in stool", "faint", "severe dizziness", "suicide",
        "درد قفسه", "خون در مدفوع", "غش", "سرگیجه شدید", "خودکشی",
    ))
    dangerous_compensation = _contains_any(text, (
        "fast", "fasting", "skip meal", "detox", "purge", "800 calories", "under 1200",
        "روزه", "حذف وعده", "دیتاکس", "پاکسازی", "۸۰۰ کالری", "800 کالری",
    ))

    if ctx.clinical_review_required:
        return {
            "scope": "guidance_only",
            "target_date": None,
            "locale": locale,
            "requires_human_review": True,
            "reason": "clinical_review_required",
        }
    if ctx.risk_level == "high":
        return {
            "scope": "guidance_only",
            "target_date": None,
            "locale": locale,
            "requires_human_review": True,
            "reason": "high_risk",
        }
    if red_flag or dangerous_compensation:
        return {
            "scope": "guidance_only",
            "target_date": None,
            "locale": locale,
            "requires_human_review": red_flag,
            "reason": "red_flag_or_unsafe_compensation",
        }
    if plan_type in {"temporary_guidance", "wellness_guidance", "conservative_guidance"}:
        return {
            "scope": "guidance_only",
            "target_date": None,
            "locale": locale,
            "requires_human_review": False,
            "reason": f"plan_type:{plan_type}",
        }
    if not plan_db and not next_days:
        return {
            "scope": "guidance_only",
            "target_date": None,
            "locale": locale,
            "requires_human_review": False,
            "reason": "no_active_plan",
        }
    if _contains_any(text, ("week", "travel", "trip", "schedule", "هفته", "سفر", "برنامه کاری")) and next_days:
        return {
            "scope": "week",
            "target_date": today,
            "locale": locale,
            "requires_human_review": False,
            "reason": "schedule_or_week_change",
        }
    if today_day:
        scope = "next_meal" if _contains_any(text, ("hungry", "hunger", "craving", "sleep", "گرسنه", "هوس", "خواب")) else "today"
        if _contains_any(text, ("overeating", "slip", "ate too much", "پرخوری", "لغزش", "زیاد خوردم")):
            scope = "remaining_day"
        return {
            "scope": scope,
            "target_date": today,
            "locale": locale,
            "requires_human_review": False,
            "reason": "active_calendar_day",
        }
    return {
        "scope": "today" if plan_db else "guidance_only",
        "target_date": today if plan_db else None,
        "locale": locale,
        "requires_human_review": False,
        "reason": "active_nutrition_plan",
    }


def _meals_from_adapt_data(data: dict) -> list[dict]:
    revised_day = data.get("revised_day") or {}
    meals = revised_day.get("meals") or data.get("revised_meals") or []
    return meals if isinstance(meals, list) else []


def _apply_calendar_revision(
    db: Session,
    user: User,
    *,
    locale: str,
    target_date: date,
    data: dict,
    warnings: list[str],
) -> tuple[bool, list[str]]:
    day = calendar_repository.get_day_by_date(db, user.id, target_date, locale)
    if day is None:
        return False, []

    revised_day = data.get("revised_day") or {}
    revised_meals = _meals_from_adapt_data(data)
    if not revised_meals:
        return False, []

    merged_warnings = list(dict.fromkeys(list(revised_day.get("warnings") or []) + warnings))
    calendar_repository.update_plan_day(
        db,
        day,
        title=revised_day.get("title"),
        summary=revised_day.get("summary") or data.get("summary"),
        hydration_goal=revised_day.get("hydration_goal"),
        notes=revised_day.get("notes") or data.get("monitoring_notes"),
        warnings=merged_warnings,
    )
    calendar_repository.replace_day_meals(
        db,
        day.id,
        locale=locale,
        meals=revised_meals,
    )
    return True, [
        meal.get("meal_type") or meal.get("title") or "meal"
        for meal in revised_meals
    ]


def _apply_nutrition_plan_meal_revision(db: Session, plan_db, data: dict) -> list[str]:
    revised_meals = _meals_from_adapt_data(data)
    if not revised_meals:
        return []
    existing = nutrition_repository.get_plan_meals(db, plan_db.id)
    by_time = {m.meal_time: m for m in existing}
    changed: list[str] = []
    for idx, meal in enumerate(revised_meals):
        meal_time = meal.get("meal_type") or meal.get("meal_time") or "snack"
        title = meal.get("title") or meal.get("name") or "وعده غذایی"
        target = by_time.get(meal_time)
        if target:
            target.name = title
            target.description = meal.get("description")
            target.notes = meal.get("portion_guidance") or meal.get("preparation_notes")
            changed.append(meal_time)
        else:
            nutrition_repository.add_plan_meal(
                db,
                plan_db.id,
                meal_time=meal_time,
                name=title,
                description=meal.get("description"),
                calories_estimate=None,
                protein_g=None,
                carbs_g=None,
                fat_g=None,
                notes=meal.get("portion_guidance") or meal.get("preparation_notes"),
                order_index=len(existing) + idx,
            )
            changed.append(meal_time)
    db.flush()
    return changed


# ─── 1. GET /nutrition/profile ────────────────────────────────────────────────

def get_nutrition_profile(db: Session, user: User) -> NutritionProfileResponse:
    ctx = nutrition_memory_service.build(db, user)
    missing: list[str] = []

    profile_summary: ProfileSummary | None = None
    if ctx.weight_kg or ctx.height_cm:
        profile_summary = ProfileSummary(
            height_cm=ctx.height_cm,
            weight_kg=ctx.weight_kg,
            target_weight_kg=ctx.target_weight_kg,
            gender=ctx.gender,
            age=ctx.age,
            goal_type=ctx.goal_type,
        )
    else:
        missing.append("profile")

    medical_summary: MedicalSummary | None = None
    if ctx.active_medical_flags or ctx.medications or ctx.allergies:
        medical_summary = MedicalSummary(
            active_conditions=ctx.active_medical_flags,
            medications=ctx.medications,
            allergies=ctx.allergies,
            has_warning_symptoms=len(ctx.warning_symptoms) > 0,
        )

    lifestyle_summary: LifestyleSummary | None = None
    if ctx.activity_level or ctx.sleep_hours is not None:
        lifestyle_summary = LifestyleSummary(
            activity_level=ctx.activity_level,
            sleep_hours=ctx.sleep_hours,
            stress_level=ctx.stress_level,
            work_schedule=ctx.work_schedule,
            cooking_ability=ctx.cooking_ability,
            food_budget=ctx.food_budget,
        )
    else:
        missing.append("lifestyle")

    preferences_summary: PreferencesSummary | None = None
    fp = onboarding_repository.get_food_preference(db, user.id)
    if fp:
        preferences_summary = PreferencesSummary(
            vegetarian=ctx.vegetarian,
            vegan=ctx.vegan,
            halal=ctx.halal,
            likes_iranian_food=ctx.likes_iranian_food,
            disliked_foods=ctx.disliked_foods,
            favorite_foods=ctx.favorite_foods,
        )
    else:
        missing.append("preferences")

    behavior_summary: BehaviorSummary | None = None
    bp = onboarding_repository.get_behavior_profile(db, user.id)
    if bp:
        behavior_summary = BehaviorSummary(
            emotional_eating=ctx.emotional_eating,
            night_eating=ctx.night_eating,
            meal_skipping=ctx.meal_skipping,
            motivation_level=ctx.motivation_level,
        )
    else:
        missing.append("behavior")

    return NutritionProfileResponse(
        user_id=user.id,
        onboarding_complete=user.is_onboarded,
        risk_level=ctx.risk_level,
        clinical_review_required=ctx.clinical_review_required,
        profile=profile_summary,
        medical=medical_summary,
        lifestyle=lifestyle_summary,
        preferences=preferences_summary,
        behavior=behavior_summary,
        missing_sections=missing,
    )


# ─── 2. GET /nutrition/plan ───────────────────────────────────────────────────

def get_nutrition_plan(db: Session, user: User) -> NutritionPlanResponse:
    plan = nutrition_repository.get_active_plan(db, user.id)
    if plan is None:
        return NutritionPlanResponse(
            has_plan=False,
            summary="هنوز برنامه‌ای وجود ندارد. لطفاً از /nutrition/plan/generate استفاده کنید.",
        )

    meals_db = nutrition_repository.get_plan_meals(db, plan.id)
    meal_items = [
        MealItem(
            id=m.id,
            meal_time=m.meal_time,
            name=m.name,
            description=m.description,
            calories_estimate=m.calories_estimate,
            protein_g=m.protein_g,
            carbs_g=m.carbs_g,
            fat_g=m.fat_g,
            notes=m.notes,
            order_index=m.order_index,
        )
        for m in meals_db
    ]

    meta = nutrition_repository.get_plan_metadata(plan)
    guidelines = _guidelines_from_dict(meta)
    warnings = meta.get("warnings") or []

    ra = onboarding_repository.get_latest_risk_assessment(db, user.id)
    risk_level = ra.risk_level if ra else "low"

    return NutritionPlanResponse(
        has_plan=True,
        plan_id=plan.id,
        status=plan.status,
        risk_level=risk_level,
        plan_type=meta.get("plan_type"),
        profile_complete=meta.get("profile_complete"),
        missing_fields=meta.get("missing_fields") or [],
        summary=plan.description,
        daily_guidelines=guidelines,
        meals=meal_items,
        warnings=warnings,
        provider=plan.generated_by,
        is_mock=plan.generated_by == "mock",
        generated_at=plan.created_at,
    )


# ─── 3. POST /nutrition/plan/generate ────────────────────────────────────────

def generate_nutrition_plan(db: Session, user: User) -> NutritionPlanGenerateResponse:
    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()
    missing_fields = _missing_plan_profile_fields(db, user, ctx)
    profile_complete = len(missing_fields) == 0
    plan_type = "full_plan"

    # Safety guardrail: clinical users get wellness guidance only
    if ctx.clinical_review_required:
        plan_type = "wellness_guidance"
        plan_data: dict = {
            "title": "راهنمایی کلی سلامت",
            "summary": _CLINICAL_REVIEW_WELLNESS_GUIDANCE,
            "daily_guidelines": {
                "calories": None,
                "protein_g": None,
                "carbs_g": None,
                "fat_g": None,
                "fiber_g": None,
                "water_liters": 2.0,
                "notes": "لطفاً پیش از شروع هر برنامه غذایی با پزشک مشورت کنید.",
            },
            "meals": [],
            "warnings": [_CLINICAL_REVIEW_WELLNESS_GUIDANCE],
        }
        provider_name = "safety_guard"
        is_mock = True
    elif ctx.risk_level == "high":
        plan_type = "conservative_guidance"
        plan_data = {
            "title": "راهنمایی کلی تغذیه",
            "summary": _HIGH_RISK_CONSERVATIVE_SUMMARY,
            "daily_guidelines": {
                "calories": None,
                "protein_g": None,
                "carbs_g": None,
                "fat_g": None,
                "fiber_g": None,
                "water_liters": 2.0,
                "notes": "برای تعیین مقادیر دقیق انرژی و درشت‌مغذی‌ها نیاز به بررسی متخصص دارید.",
            },
            "meals": [],
            "warnings": [_HIGH_RISK_WELLNESS_GUIDANCE],
        }
        provider_name = "safety_guard"
        is_mock = True
    elif not profile_complete:
        plan_type = "temporary_guidance"
        plan_data = _temporary_guidance_plan(missing_fields)
        provider_name = "profile_gate"
        is_mock = True
    else:
        plan_data, result = agent.generate_plan(ctx)
        provider_name = result.provider
        is_mock = result.is_mock

    # Persist
    nutrition_repository.archive_active_plans(db, user.id)
    plan_meta = {
        "daily_guidelines": plan_data.get("daily_guidelines"),
        "warnings": plan_data.get("warnings") or [],
        "provider": provider_name,
        "plan_type": plan_type,
        "profile_complete": profile_complete,
        "missing_fields": missing_fields,
    }
    plan_db = nutrition_repository.create_plan(
        db,
        user.id,
        title=plan_data.get("title", "برنامه تغذیه"),
        description=plan_data.get("summary"),
        plan_metadata=plan_meta,
        generated_by=provider_name if not is_mock else "mock",
    )

    meals_raw = plan_data.get("meals") or []
    for i, m in enumerate(meals_raw):
        nutrition_repository.add_plan_meal(
            db,
            plan_db.id,
            meal_time=m.get("meal_time", "snack"),
            name=m.get("name", "وعده غذایی"),
            description=m.get("description"),
            calories_estimate=m.get("calories_estimate"),
            protein_g=m.get("protein_g"),
            carbs_g=m.get("carbs_g"),
            fat_g=m.get("fat_g"),
            notes=m.get("notes"),
            order_index=i,
        )

    db.commit()

    # Build response
    meal_items = _meal_items_from_list(meals_raw)
    guidelines = _guidelines_from_dict(plan_data)
    warnings = plan_data.get("warnings") or []

    return NutritionPlanGenerateResponse(
        has_plan=True,
        plan_id=plan_db.id,
        status="active",
        risk_level=ctx.risk_level,
        plan_type=plan_type,
        profile_complete=profile_complete,
        missing_fields=missing_fields,
        summary=plan_data.get("summary"),
        daily_guidelines=guidelines,
        meals=meal_items,
        warnings=warnings,
        provider=provider_name,
        is_mock=is_mock,
        generated_at=plan_db.created_at,
    )


# ─── 4. POST /nutrition/meal/analyze ─────────────────────────────────────────

def analyze_meal(
    db: Session, user: User, body: MealAnalyzeRequest
) -> MealAnalysisResponse:
    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()

    analysis, result = agent.analyze_meal(
        ctx,
        meal_text=body.meal_text,
        meal_time=body.meal_time,
        meal_context=body.context,
    )

    # Safety: append clinical reminder if needed
    warnings = list(analysis.get("warnings") or [])
    if ctx.clinical_review_required:
        warnings.append(_CLINICAL_REVIEW_WELLNESS_GUIDANCE)

    # Persist meal entry
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    meal_entry = nutrition_repository.create_meal_entry(
        db,
        user.id,
        meal_time=body.meal_time if body.meal_time != "unknown" else None,
        description=body.meal_text,
        analysis_result=analysis,
        logged_at=now,
    )
    db.commit()

    return MealAnalysisResponse(
        meal_id=meal_entry.id,
        quality_score=analysis.get("quality_score"),
        analysis_summary=analysis.get("analysis_summary", "تحلیل انجام شد."),
        protein=analysis.get("protein", ""),
        fiber=analysis.get("fiber", ""),
        sugar=analysis.get("sugar", ""),
        balance=analysis.get("balance", ""),
        portion=analysis.get("portion", ""),
        suggestions=analysis.get("suggestions") or [],
        warnings=warnings,
        provider=result.provider,
        is_mock=result.is_mock,
    )


# ─── 5. POST /nutrition/what-to-eat-now ──────────────────────────────────────

def what_to_eat_now(
    db: Session, user: User, body: WhatToEatNowRequest
) -> WhatToEatNowResponse:
    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()

    data, result = agent.what_to_eat_now(
        ctx,
        available_foods=body.available_foods,
        hunger_level=body.hunger_level,
        meal_context=body.meal_context,
        time_available_minutes=body.time_available_minutes,
    )

    options = [
        FoodOption(
            name=o.get("name", "گزینه غذایی"),
            description=o.get("description"),
            calories_estimate=o.get("calories_estimate"),
            prep_time_minutes=o.get("prep_time_minutes"),
            tags=o.get("tags") or [],
        )
        for o in (data.get("options") or [])
    ]

    warnings = list(data.get("warnings") or [])
    if ctx.clinical_review_required:
        warnings.append(_CLINICAL_REVIEW_WELLNESS_GUIDANCE)

    return WhatToEatNowResponse(
        options=options,
        reasoning_summary=data.get("reasoning_summary", ""),
        warnings=warnings,
        provider=result.provider,
        is_mock=result.is_mock,
    )


# ─── 6. POST /nutrition/adapt-plan ───────────────────────────────────────────

def adapt_plan(
    db: Session, user: User, body: AdaptPlanRequest
) -> AdaptPlanResponse:
    ctx = nutrition_memory_service.build(db, user)
    agent = NutritionAgentService()
    plan_db = nutrition_repository.get_active_plan(db, user.id)
    decision = _adapt_decision(db, user, ctx, body, plan_db)

    recent_ctx: dict = {}
    if body.recent_hunger:
        recent_ctx["hunger"] = body.recent_hunger
    if body.recent_sleep:
        recent_ctx["sleep"] = body.recent_sleep
    if body.recent_stress:
        recent_ctx["stress"] = body.recent_stress
    if body.recent_adherence:
        recent_ctx["adherence"] = body.recent_adherence
    if body.notes:
        recent_ctx["notes"] = body.notes
    prompt_decision = dict(decision)
    if prompt_decision.get("target_date") is not None:
        prompt_decision["target_date"] = prompt_decision["target_date"].isoformat()
    recent_ctx["revision_decision"] = prompt_decision

    data, result = agent.adapt_plan(ctx, reason=body.reason, recent_context=recent_ctx)
    fallback_reason = (result.raw_metadata or {}).get("fallback_reason") if result.raw_metadata else None

    warnings = list(data.get("warnings") or [])
    if ctx.clinical_review_required:
        warnings.append(_CLINICAL_REVIEW_WELLNESS_GUIDANCE)
    elif ctx.risk_level == "high":
        warnings.append(_HIGH_RISK_WELLNESS_GUIDANCE)
    if decision["requires_human_review"]:
        warnings.append(_ADAPT_HUMAN_REVIEW_WARNING)
    if decision["reason"] == "red_flag_or_unsafe_compensation":
        warnings.append(_ADAPT_NO_EXTREME_COMPENSATION)
    if decision["reason"] == "no_active_plan":
        warnings.append(_ADAPT_NO_ACTIVE_PLAN_WARNING)
    warnings.extend(data.get("safety_notes") or [])
    warnings = list(dict.fromkeys(warnings))

    guidelines = _guidelines_from_dict(data)

    plan_id: str | None = None
    revision_applied = False
    changed_items = list(data.get("changed_items") or [])
    revised_date: str | None = None

    if decision["scope"] in {"next_meal", "today", "remaining_day", "week"} and decision["target_date"]:
        applied, calendar_changed = _apply_calendar_revision(
            db,
            user,
            locale=decision["locale"],
            target_date=decision["target_date"],
            data=data,
            warnings=warnings,
        )
        if applied:
            revision_applied = True
            revised_date = decision["target_date"].isoformat()
            changed_items = list(dict.fromkeys(changed_items + calendar_changed))

    if plan_db and not revision_applied and decision["scope"] != "guidance_only":
        plan_changed = _apply_nutrition_plan_meal_revision(db, plan_db, data)
        if plan_changed:
            revision_applied = True
            changed_items = list(dict.fromkeys(changed_items + plan_changed))
            revised_date = decision["target_date"].isoformat() if decision["target_date"] else None

    if plan_db:
        plan_meta = nutrition_repository.get_plan_metadata(plan_db)
        if guidelines:
            plan_meta["daily_guidelines"] = {
                "calories": guidelines.calories,
                "protein_g": guidelines.protein_g,
                "carbs_g": guidelines.carbs_g,
                "fat_g": guidelines.fat_g,
                "fiber_g": guidelines.fiber_g,
                "water_liters": guidelines.water_liters,
                "notes": guidelines.notes,
            }
        plan_meta["warnings"] = warnings
        plan_meta["adapted_by"] = result.provider
        plan_meta["last_revision"] = {
            "revision_applied": revision_applied,
            "revision_scope": decision["scope"],
            "revised_date": revised_date,
            "changed_items": changed_items,
            "reason_for_changes": data.get("reason_for_changes") or decision["reason"],
            "safety_notes": data.get("safety_notes") or [],
            "requires_human_review": bool(data.get("requires_human_review") or decision["requires_human_review"]),
            "fallback_reason": fallback_reason,
            "revised_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }
        if data.get("revised_meals"):
            plan_meta["last_revised_meals"] = data.get("revised_meals")
        summary = plan_db.description or ""
        adaptation_note = f" | تطبیق: {body.reason[:80]}"
        nutrition_repository.update_plan_metadata(
            db,
            plan_db,
            description=summary + adaptation_note,
            plan_metadata=plan_meta,
        )
        db.commit()
        plan_id = plan_db.id
    elif revision_applied:
        db.commit()

    return AdaptPlanResponse(
        plan_id=plan_id,
        changes=data.get("changes") or [],
        updated_guidelines=guidelines,
        warnings=warnings,
        revision_applied=revision_applied,
        revision_scope=decision["scope"],
        revised_date=revised_date,
        changed_items=changed_items,
        reason_for_changes=data.get("reason_for_changes") or decision["reason"],
        safety_notes=data.get("safety_notes") or [],
        requires_human_review=bool(data.get("requires_human_review") or decision["requires_human_review"]),
        fallback_reason=fallback_reason,
        provider=result.provider,
        is_mock=result.is_mock,
    )
