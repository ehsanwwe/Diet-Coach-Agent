"""
Nutrition API endpoints — Phase 07.

All endpoints require a valid Bearer token (get_current_user dependency).
No anonymous access.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.calendar import (
    CalendarResponse,
    GenerateWeekRequest,
    GenerateWeekResponse,
    RegenerateDayRequest,
    RegenerateDayResponse,
)
from app.schemas.nutrition import (
    AdaptPlanRequest,
    AdaptPlanResponse,
    ContextGuidanceRequest,
    ContextGuidanceResponse,
    CravingSupportRequest,
    CravingSupportResponse,
    MealAnalysisResponse,
    MealAnalyzeRequest,
    NutritionPlanGenerateResponse,
    NutritionPlanResponse,
    NutritionProfileResponse,
    SlipRecoveryRequest,
    SlipRecoveryResponse,
    WhatToEatNowRequest,
    WhatToEatNowResponse,
)
from app.services import calendar_service, nutrition_service

router = APIRouter(tags=["nutrition"])


@router.get("/profile", response_model=NutritionProfileResponse)
def get_nutrition_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> NutritionProfileResponse:
    """Return the authenticated user's nutrition profile summary."""
    try:
        return nutrition_service.get_nutrition_profile(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to retrieve nutrition profile: {exc}", status_code=500)


@router.get("/plan", response_model=NutritionPlanResponse)
def get_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> NutritionPlanResponse:
    """Return the current active nutrition plan, or an empty state if none exists."""
    try:
        return nutrition_service.get_nutrition_plan(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to retrieve nutrition plan: {exc}", status_code=500)


@router.post("/plan/generate", response_model=NutritionPlanGenerateResponse, status_code=201)
def generate_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> NutritionPlanGenerateResponse:
    """
    Generate a new adaptive nutrition plan for the authenticated user.

    Applies safety guardrails. Clinical-review users receive wellness guidance only.
    Archives any previously active plan.
    """
    try:
        return nutrition_service.generate_nutrition_plan(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to generate nutrition plan: {exc}", status_code=500)


@router.post("/meal/analyze", response_model=MealAnalysisResponse, status_code=201)
def analyze_meal(
    body: MealAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> MealAnalysisResponse:
    """
    Analyze the nutritional quality of a meal text description.

    Returns protein, fiber, sugar, balance, portion, and improvement suggestions.
    Logs the meal entry to the database.
    """
    try:
        return nutrition_service.analyze_meal(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to analyze meal: {exc}", status_code=500)


@router.post("/what-to-eat-now", response_model=WhatToEatNowResponse)
def what_to_eat_now(
    body: WhatToEatNowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> WhatToEatNowResponse:
    """
    Suggest 2–3 practical meal or snack options based on available foods,
    hunger level, and user profile. Prioritizes Iranian/Persian food culture.
    """
    try:
        return nutrition_service.what_to_eat_now(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to get food suggestions: {exc}", status_code=500)


@router.post("/craving-support", response_model=CravingSupportResponse)
def craving_support(
    body: CravingSupportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CravingSupportResponse:
    """Return structured craving coaching with safety guardrails."""
    try:
        return nutrition_service.get_craving_support(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to get craving support: {exc}", status_code=500)


@router.post("/slip-recovery", response_model=SlipRecoveryResponse)
def slip_recovery(
    body: SlipRecoveryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SlipRecoveryResponse:
    """Return non-judgmental recovery guidance after overeating or breaking plan."""
    try:
        return nutrition_service.recover_from_slip(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to get slip recovery guidance: {exc}", status_code=500)


@router.post("/context-guidance", response_model=ContextGuidanceResponse)
def context_guidance(
    body: ContextGuidanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> ContextGuidanceResponse:
    """Return restaurant, party, travel, or work eating guidance."""
    try:
        return nutrition_service.get_restaurant_party_travel_guidance(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to get context guidance: {exc}", status_code=500)


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    start_date: str | None = Query(default=None, description="ISO date YYYY-MM-DD"),
    days: int = Query(default=30, ge=1, le=90),
    locale: str | None = Query(default=None, description="fa | en | ar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CalendarResponse:
    """Return the user's rolling meal plan calendar for the requested locale."""
    try:
        effective_locale = calendar_service.resolve_locale(db, current_user, locale)
        parsed_start: date | None = None
        if start_date:
            try:
                parsed_start = date.fromisoformat(start_date)
            except ValueError:
                raise_http_error("Invalid start_date format. Use YYYY-MM-DD.", status_code=422)
        return calendar_service.get_calendar(db, current_user, effective_locale, parsed_start, days)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to retrieve calendar: {exc}", status_code=500)


@router.post("/calendar/generate-week", response_model=GenerateWeekResponse, status_code=201)
def generate_calendar_week(
    body: GenerateWeekRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> GenerateWeekResponse:
    """Generate next 7 plan days for the user in the requested locale."""
    try:
        effective_locale = calendar_service.resolve_locale(db, current_user, body.locale)
        parsed_start: date | None = None
        if body.start_date:
            try:
                parsed_start = date.fromisoformat(body.start_date)
            except ValueError:
                raise_http_error("Invalid start_date format. Use YYYY-MM-DD.", status_code=422)
        return calendar_service.generate_week(
            db, current_user, effective_locale, parsed_start, body.force
        )
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to generate week plan: {exc}", status_code=500)


@router.post("/calendar/regenerate-day", response_model=RegenerateDayResponse, status_code=201)
def regenerate_calendar_day(
    body: RegenerateDayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> RegenerateDayResponse:
    """Regenerate a single planned day in the requested locale."""
    try:
        effective_locale = calendar_service.resolve_locale(db, current_user, body.locale)
        try:
            plan_date = date.fromisoformat(body.plan_date)
        except ValueError:
            raise_http_error("Invalid plan_date format. Use YYYY-MM-DD.", status_code=422)
        return calendar_service.regenerate_day(db, current_user, effective_locale, plan_date)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to regenerate day: {exc}", status_code=500)


@router.post("/adapt-plan", response_model=AdaptPlanResponse)
def adapt_plan(
    body: AdaptPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> AdaptPlanResponse:
    """
    Adapt the current nutrition plan based on user feedback.

    Updates persisted plan guidelines. Does not create extreme changes.
    Safety guardrails are applied.
    """
    try:
        return nutrition_service.adapt_plan(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Failed to adapt nutrition plan: {exc}", status_code=500)
