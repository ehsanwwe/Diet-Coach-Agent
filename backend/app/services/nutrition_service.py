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
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import nutrition_repository, onboarding_repository
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


# ─── Helper ───────────────────────────────────────────────────────────────────

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

    # Safety guardrail: clinical users get wellness guidance only
    if ctx.clinical_review_required:
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
    else:
        plan_data, result = agent.generate_plan(ctx)
        provider_name = result.provider
        is_mock = result.is_mock

        # High-risk: append wellness reminder to warnings
        if ctx.risk_level == "high":
            w = plan_data.get("warnings") or []
            if _HIGH_RISK_WELLNESS_GUIDANCE not in w:
                w.append(_HIGH_RISK_WELLNESS_GUIDANCE)
            plan_data["warnings"] = w

    # Persist
    nutrition_repository.archive_active_plans(db, user.id)
    plan_meta = {
        "daily_guidelines": plan_data.get("daily_guidelines"),
        "warnings": plan_data.get("warnings") or [],
        "provider": provider_name,
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

    data, result = agent.adapt_plan(ctx, reason=body.reason, recent_context=recent_ctx)

    warnings = list(data.get("warnings") or [])
    if ctx.clinical_review_required:
        warnings.append(_CLINICAL_REVIEW_WELLNESS_GUIDANCE)
    elif ctx.risk_level == "high":
        warnings.append(_HIGH_RISK_WELLNESS_GUIDANCE)

    guidelines = _guidelines_from_dict(data)

    # Update persisted plan metadata if an active plan exists
    plan_db = nutrition_repository.get_active_plan(db, user.id)
    plan_id: str | None = None
    if plan_db and guidelines:
        plan_meta = nutrition_repository.get_plan_metadata(plan_db)
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

    return AdaptPlanResponse(
        plan_id=plan_id,
        changes=data.get("changes") or [],
        updated_guidelines=guidelines,
        warnings=warnings,
        provider=result.provider,
        is_mock=result.is_mock,
    )
