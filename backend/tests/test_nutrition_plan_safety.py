from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import nutrition_repository, onboarding_repository
from app.services import nutrition_service
from app.services.safety_guardrail_service import SafetyAssessment


def _record_risk(db: Session, user: User, risk_level: str) -> None:
    onboarding_repository.create_risk_assessment(
        db,
        user.id,
        SafetyAssessment(
            risk_level=risk_level,
            flags_triggered=[risk_level],
            clinical_review_required=risk_level == "clinical_review_required",
        ),
    )
    db.flush()


def _complete_low_risk_profile(db: Session, user: User) -> None:
    onboarding_repository.upsert_profile(
        db,
        user.id,
        full_name="Test User",
        gender="female",
        birth_date=date(1990, 1, 1),
        height_cm=165,
        weight_kg=72,
        target_weight_kg=66,
        waist_cm=None,
    )
    nutrition_repository.upsert_nutrition_goal(
        db,
        user.id,
        goal_type="weight_loss",
        target_calories=None,
        notes=None,
    )
    onboarding_repository.replace_medical_flags(db, user.id, {"none": False})
    _record_risk(db, user, "low")
    onboarding_repository.upsert_lifestyle(
        db,
        user.id,
        sleep_hours=7,
        stress_level=2,
        work_schedule="office",
        activity_level="moderate",
        exercise_days_per_week=3,
        cooking_ability=4,
        food_budget="medium",
        eating_out_frequency="weekly",
        travel_frequency="rare",
    )
    onboarding_repository.upsert_food_preference(
        db,
        user.id,
        likes_iranian_food=True,
        vegetarian=False,
        vegan=False,
        halal=True,
        disliked_foods=[],
        favorite_foods=["عدسی"],
        breakfast_habit="regular",
        rice_frequency="moderate",
        bread_frequency="moderate",
        sweets_frequency="low",
        tea_frequency="daily",
        restaurant_frequency="weekly",
    )
    onboarding_repository.upsert_behavior_profile(
        db,
        user.id,
        emotional_eating=False,
        night_eating=False,
        meal_skipping=False,
        cravings=[],
        binge_history=False,
        diet_history="balanced",
        previous_failures="",
        hunger_pattern="stable",
        motivation_level=4,
    )
    db.flush()


def test_low_risk_incomplete_profile_returns_temporary_guidance(
    db_session: Session, test_user: User
):
    response = nutrition_service.generate_nutrition_plan(db_session, test_user)

    assert response.risk_level == "low"
    assert response.provider == "profile_gate"
    assert response.plan_type == "temporary_guidance"
    assert response.profile_complete is False
    assert response.missing_fields
    assert response.meals == []
    assert response.daily_guidelines is not None
    assert response.daily_guidelines.calories is None


def test_low_risk_sufficient_profile_uses_mock_full_plan(db_session: Session, test_user: User):
    _complete_low_risk_profile(db_session, test_user)

    response = nutrition_service.generate_nutrition_plan(db_session, test_user)

    assert response.risk_level == "low"
    assert response.provider == "mock"
    assert response.is_mock is True
    assert response.plan_type == "full_plan"
    assert response.profile_complete is True
    assert response.missing_fields == []
    assert response.meals
    assert response.daily_guidelines is not None
    assert response.daily_guidelines.calories is not None


def test_high_risk_plan_generation_returns_conservative_guidance(
    db_session: Session, test_user: User
):
    _record_risk(db_session, test_user, "high")

    response = nutrition_service.generate_nutrition_plan(db_session, test_user)

    assert response.risk_level == "high"
    assert response.provider == "safety_guard"
    assert response.is_mock is True
    assert response.plan_type == "conservative_guidance"
    assert response.meals == []
    assert response.daily_guidelines is not None
    assert response.daily_guidelines.calories is None
    assert response.warnings


def test_clinical_review_plan_generation_returns_wellness_guidance_only(
    db_session: Session, test_user: User
):
    _record_risk(db_session, test_user, "clinical_review_required")

    response = nutrition_service.generate_nutrition_plan(db_session, test_user)

    assert response.risk_level == "clinical_review_required"
    assert response.provider == "safety_guard"
    assert response.is_mock is True
    assert response.plan_type == "wellness_guidance"
    assert response.meals == []
    assert response.daily_guidelines is not None
    assert response.daily_guidelines.calories is None
    assert response.warnings
