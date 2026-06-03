"""
Onboarding endpoints.

All routes require authentication. Anonymous access is rejected by
the get_current_user dependency.

ONB-01: GET  /onboarding/status
ONB-02: POST /onboarding/profile
ONB-03: POST /onboarding/medical
ONB-04: POST /onboarding/lifestyle
ONB-05: POST /onboarding/preferences
ONB-06: POST /onboarding/behavior
ONB-07: POST /onboarding/complete
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.onboarding import (
    BehaviorRequest,
    BehaviorResponse,
    LifestyleRequest,
    LifestyleResponse,
    MedicalRequest,
    MedicalResponse,
    OnboardingCompleteResponse,
    OnboardingStatusResponse,
    PreferencesRequest,
    PreferencesResponse,
    ProfileRequest,
    ProfileResponse,
)
from app.services import onboarding_service

router = APIRouter(tags=["onboarding"])


@router.get("/status", response_model=SuccessResponse[OnboardingStatusResponse])
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[OnboardingStatusResponse]:
    """Return the current onboarding progress for the authenticated user."""
    try:
        result = onboarding_service.get_status(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/profile", response_model=SuccessResponse[ProfileResponse])
def save_profile(
    body: ProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[ProfileResponse]:
    """Save or update basic profile data (Step 1)."""
    try:
        result = onboarding_service.save_profile(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/medical", response_model=SuccessResponse[MedicalResponse])
def save_medical(
    body: MedicalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[MedicalResponse]:
    """Save or replace medical safety data (Step 2). Returns preliminary risk level."""
    try:
        result = onboarding_service.save_medical(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/lifestyle", response_model=SuccessResponse[LifestyleResponse])
def save_lifestyle(
    body: LifestyleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[LifestyleResponse]:
    """Save or update lifestyle data (Step 3)."""
    try:
        result = onboarding_service.save_lifestyle(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/preferences", response_model=SuccessResponse[PreferencesResponse])
def save_preferences(
    body: PreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[PreferencesResponse]:
    """Save or update food preferences (Step 4)."""
    try:
        result = onboarding_service.save_preferences(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/behavior", response_model=SuccessResponse[BehaviorResponse])
def save_behavior(
    body: BehaviorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[BehaviorResponse]:
    """Save or update behavior and habit profile (Step 5)."""
    try:
        result = onboarding_service.save_behavior(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)


@router.post("/complete", response_model=SuccessResponse[OnboardingCompleteResponse])
def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[OnboardingCompleteResponse]:
    """
    Finalize onboarding.

    Requires the profile step to be completed. Runs the final safety risk
    assessment, creates a NutritionRiskAssessment record, and sets
    user.is_onboarded = True.

    Does not generate a diet plan and does not call AI/OpenClaw.
    """
    try:
        result = onboarding_service.complete_onboarding(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code, detail=exc.detail)
    return SuccessResponse(data=result)
