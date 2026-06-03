"""
OnboardingService: orchestrates all onboarding step operations.

Keeps routes thin by handling business logic, validation, and error
propagation here. DB operations are delegated to onboarding_repository.
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.user import User
from app.repositories import onboarding_repository
from app.schemas.onboarding import (
    ONBOARDING_STEP_ORDER,
    BehaviorRequest,
    BehaviorResponse,
    LifestyleRequest,
    LifestyleResponse,
    MedicalFlagItem,
    MedicalRequest,
    MedicalResponse,
    OnboardingCompleteResponse,
    OnboardingStatusResponse,
    PreferencesRequest,
    PreferencesResponse,
    ProfileRequest,
    ProfileResponse,
)
from app.services import safety_guardrail_service


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _calculate_age(birth_date: date) -> int:
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def _age_to_birth_date(age: int) -> date:
    today = date.today()
    return date(today.year - age, today.month, today.day)


def _completed_steps(db: Session, user_id: str) -> list[str]:
    steps: list[str] = []
    if onboarding_repository.get_profile(db, user_id) is not None:
        steps.append("profile")
    if onboarding_repository.medical_data_exists(db, user_id):
        steps.append("medical")
    if onboarding_repository.get_lifestyle(db, user_id) is not None:
        steps.append("lifestyle")
    if onboarding_repository.get_food_preference(db, user_id) is not None:
        steps.append("preferences")
    if onboarding_repository.get_behavior_profile(db, user_id) is not None:
        steps.append("behavior")
    return steps


def _next_step(completed: list[str], is_onboarded: bool) -> str | None:
    if is_onboarded:
        return None
    for step in ONBOARDING_STEP_ORDER:
        if step not in completed:
            return step
    return "complete"


# ─── Step handlers ────────────────────────────────────────────────────────────

def get_status(db: Session, user: User) -> OnboardingStatusResponse:
    profile = onboarding_repository.get_profile(db, user.id)
    medical_exists = onboarding_repository.medical_data_exists(db, user.id)
    lifestyle = onboarding_repository.get_lifestyle(db, user.id)
    fp = onboarding_repository.get_food_preference(db, user.id)
    bp = onboarding_repository.get_behavior_profile(db, user.id)
    latest_ra = onboarding_repository.get_latest_risk_assessment(db, user.id)

    completed = _completed_steps(db, user.id)
    return OnboardingStatusResponse(
        user_id=user.id,
        is_onboarded=user.is_onboarded,
        completed_steps=completed,
        next_step=_next_step(completed, user.is_onboarded),
        risk_level=latest_ra.risk_level if latest_ra else None,
        profile_exists=profile is not None,
        medical_exists=medical_exists,
        lifestyle_exists=lifestyle is not None,
        preferences_exists=fp is not None,
        behavior_exists=bp is not None,
    )


def save_profile(db: Session, user: User, body: ProfileRequest) -> ProfileResponse:
    birth_date: date | None
    if body.birth_date is not None:
        birth_date = body.birth_date
    elif body.age is not None:
        birth_date = _age_to_birth_date(body.age)
    else:
        raise AppError("Either birth_date or age must be provided", status_code=400)

    profile = onboarding_repository.upsert_profile(
        db,
        user.id,
        full_name=body.full_name,
        gender=body.gender,
        birth_date=birth_date,
        height_cm=body.height_cm,
        weight_kg=body.current_weight_kg,
        target_weight_kg=body.target_weight_kg,
        waist_cm=body.waist_circumference_cm,
    )
    return ProfileResponse.model_validate(profile)


def save_medical(db: Session, user: User, body: MedicalRequest) -> MedicalResponse:
    flags_dict = body.condition_flags()
    flag_rows = onboarding_repository.replace_medical_flags(db, user.id, flags_dict)
    med_rows = onboarding_repository.replace_medications(db, user.id, body.medications)
    allergy_rows = onboarding_repository.replace_allergies(db, user.id, body.allergies)
    onboarding_repository.upsert_warning_symptoms(db, user.id, body.warning_symptoms)

    profile = onboarding_repository.get_profile(db, user.id)
    age: int | None = None
    if profile and profile.birth_date:
        age = _calculate_age(profile.birth_date)

    assessment = safety_guardrail_service.assess(
        medical_flags=flags_dict,
        medications=[m.name for m in med_rows],
        warning_symptoms=body.warning_symptoms,
        age=age,
    )

    return MedicalResponse(
        flags=[MedicalFlagItem.model_validate(f) for f in flag_rows],
        medications=[m.name for m in med_rows],
        allergies=[a.allergen for a in allergy_rows],
        warning_symptoms=body.warning_symptoms,
        risk_level=assessment.risk_level,  # type: ignore[arg-type]
        risk_flags=assessment.flags_triggered,
        clinical_review_required=assessment.clinical_review_required,
    )


def save_lifestyle(
    db: Session, user: User, body: LifestyleRequest
) -> LifestyleResponse:
    lp = onboarding_repository.upsert_lifestyle(
        db,
        user.id,
        sleep_hours=body.sleep_hours,
        stress_level=body.stress_level,
        work_schedule=body.work_schedule,
        activity_level=body.activity_level,
        exercise_days_per_week=body.exercise_days_per_week,
        cooking_ability=body.cooking_ability,
        food_budget=body.food_budget,
        eating_out_frequency=body.eating_out_frequency,
        travel_frequency=body.travel_frequency,
    )
    return LifestyleResponse.model_validate(lp)


def save_preferences(
    db: Session, user: User, body: PreferencesRequest
) -> PreferencesResponse:
    fp = onboarding_repository.upsert_food_preference(
        db,
        user.id,
        likes_iranian_food=body.likes_iranian_food,
        vegetarian=body.vegetarian,
        vegan=body.vegan,
        halal=body.halal,
        disliked_foods=body.disliked_foods,
        favorite_foods=body.favorite_foods,
        breakfast_habit=body.breakfast_habit,
        rice_frequency=body.rice_frequency,
        bread_frequency=body.bread_frequency,
        sweets_frequency=body.sweets_frequency,
        tea_frequency=body.tea_frequency,
        restaurant_frequency=body.restaurant_frequency,
    )
    return PreferencesResponse.model_validate(fp)


def save_behavior(
    db: Session, user: User, body: BehaviorRequest
) -> BehaviorResponse:
    bp = onboarding_repository.upsert_behavior_profile(
        db,
        user.id,
        emotional_eating=body.emotional_eating,
        night_eating=body.night_eating,
        meal_skipping=body.meal_skipping,
        cravings=body.cravings,
        binge_history=body.binge_history,
        diet_history=body.diet_history,
        previous_failures=body.previous_failures,
        hunger_pattern=body.hunger_pattern,
        motivation_level=body.motivation_level,
    )
    return BehaviorResponse.model_validate(bp)


def complete_onboarding(db: Session, user: User) -> OnboardingCompleteResponse:
    # Profile is the minimum required step
    profile = onboarding_repository.get_profile(db, user.id)
    if profile is None:
        raise AppError(
            "The profile step must be completed before finishing onboarding",
            status_code=400,
        )

    # Collect medical data (may not exist — defaults to low risk)
    all_flags = onboarding_repository.get_medical_flags(db, user.id)
    meds = onboarding_repository.get_medications(db, user.id)
    symptoms = onboarding_repository.get_warning_symptoms(db, user.id)

    flags_dict = {
        f.condition_code: f.has_condition
        for f in all_flags
        if f.condition_code != onboarding_repository.WARNING_SYMPTOMS_CODE
    }

    age: int | None = None
    if profile.birth_date:
        age = _calculate_age(profile.birth_date)

    assessment = safety_guardrail_service.assess(
        medical_flags=flags_dict,
        medications=[m.name for m in meds],
        warning_symptoms=symptoms,
        age=age,
    )

    onboarding_repository.create_risk_assessment(db, user.id, assessment)
    onboarding_repository.set_user_onboarded(db, user)

    completed = _completed_steps(db, user.id)

    if assessment.clinical_review_required:
        message = (
            "Onboarding complete. Based on your health information, we recommend "
            "consulting a healthcare professional before starting a nutrition plan."
        )
    elif assessment.risk_level == "high":
        message = (
            "Onboarding complete. Some health factors require extra care — "
            "your coach will tailor guidance accordingly."
        )
    else:
        message = "Onboarding complete. Your personalized nutrition journey starts now."

    return OnboardingCompleteResponse(
        user_id=user.id,
        is_onboarded=True,
        risk_level=assessment.risk_level,
        clinical_review_required=assessment.clinical_review_required,
        risk_flags=assessment.flags_triggered,
        completed_steps=completed,
        message=message,
    )
