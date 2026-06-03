"""
Nutrition API endpoints — Phase 07.

All endpoints require a valid Bearer token (get_current_user dependency).
No anonymous access.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.nutrition import (
    AdaptPlanRequest,
    AdaptPlanResponse,
    MealAnalysisResponse,
    MealAnalyzeRequest,
    NutritionPlanGenerateResponse,
    NutritionPlanResponse,
    NutritionProfileResponse,
    WhatToEatNowRequest,
    WhatToEatNowResponse,
)
from app.services import nutrition_service

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
