from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import calendar_repository, nutrition_repository, onboarding_repository
from app.schemas.nutrition import AdaptPlanRequest
from app.services import nutrition_service
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.nutrition_memory_service import NutritionMemoryContext
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


def _active_plan(db: Session, user: User, plan_type: str = "full_plan"):
    plan = nutrition_repository.create_plan(
        db,
        user.id,
        title="Active plan",
        description="Current active plan",
        plan_metadata={
            "plan_type": plan_type,
            "daily_guidelines": {"calories": 1900},
            "warnings": [],
        },
        generated_by="mock",
    )
    nutrition_repository.add_plan_meal(
        db,
        plan.id,
        meal_time="dinner",
        name="Old dinner",
        description="Old dinner description",
        calories_estimate=500,
        protein_g=25,
        carbs_g=55,
        fat_g=15,
        notes=None,
        order_index=0,
    )
    db.flush()
    return plan


def _calendar_today(db: Session, user: User):
    cal = calendar_repository.get_or_create_calendar(db, user.id, "fa")
    day = calendar_repository.create_plan_day(
        db,
        calendar_id=cal.id,
        user_id=user.id,
        locale="fa",
        plan_date=date.today(),
        day_index=1,
        title="Old day",
        summary="Old summary",
        hydration_goal="۸ لیوان آب",
        notes=None,
        warnings=[],
    )
    calendar_repository.create_plan_day_meal(
        db,
        plan_day_id=day.id,
        locale="fa",
        meal_type="dinner",
        title="Old dinner",
        description="Old dinner description",
        portion_guidance="old portion",
        alternatives=[],
        preparation_notes=None,
    )
    db.flush()
    return day


def test_adapt_plan_no_active_plan_returns_safe_guidance(db_session: Session, test_user: User):
    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="I am hungry tonight"),
    )

    assert response.revision_applied is False
    assert response.revision_scope == "guidance_only"
    assert response.plan_id is None
    assert response.warnings


def test_adapt_plan_with_active_calendar_revises_today(
    db_session: Session, test_user: User
):
    _calendar_today(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="I am still hungry", recent_hunger="high"),
    )

    assert response.revision_applied is True
    assert response.revision_scope == "next_meal"
    assert response.revised_date == date.today().isoformat()

    day = calendar_repository.get_day_by_date(db_session, test_user.id, date.today(), "fa")
    meals = calendar_repository.get_day_meals(db_session, day.id)
    titles = [m.title for m in meals]
    assert any("ماست" in title or "عدسی" in title for title in titles)


def test_adapt_plan_with_active_nutrition_plan_updates_meals_and_metadata(
    db_session: Session, test_user: User
):
    plan = _active_plan(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="I am hungry after dinner", recent_hunger="high"),
    )

    assert response.revision_applied is True
    assert response.plan_id == plan.id
    assert response.changed_items

    meta = nutrition_repository.get_plan_metadata(plan)
    assert meta["last_revision"]["revision_applied"] is True
    meals = nutrition_repository.get_plan_meals(db_session, plan.id)
    assert any(m.name != "Old dinner" for m in meals)


def test_adapt_plan_high_risk_is_guidance_only(db_session: Session, test_user: User):
    _record_risk(db_session, test_user, "high")
    _active_plan(db_session, test_user)
    _calendar_today(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="change my plan because I am hungry"),
    )

    assert response.revision_applied is False
    assert response.revision_scope == "guidance_only"
    assert response.requires_human_review is True


def test_adapt_plan_clinical_review_has_no_strict_revision(
    db_session: Session, test_user: User
):
    _record_risk(db_session, test_user, "clinical_review_required")
    _active_plan(db_session, test_user)
    _calendar_today(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="change my plan"),
    )

    assert response.revision_applied is False
    assert response.revision_scope == "guidance_only"
    assert response.requires_human_review is True


def test_adapt_plan_overeating_slip_avoids_extreme_compensation(
    db_session: Session, test_user: User
):
    _calendar_today(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(reason="I ate too much and slipped at lunch"),
    )

    assert response.revision_scope == "remaining_day"
    assert response.revision_applied is True
    combined = " ".join(response.warnings + response.safety_notes).lower()
    assert "skip meal" not in combined
    assert "detox" not in combined
    assert "purge" not in combined


def test_adapt_plan_low_sleep_high_cravings_revises_next_meal(
    db_session: Session, test_user: User
):
    _calendar_today(db_session, test_user)

    response = nutrition_service.adapt_plan(
        db_session,
        test_user,
        AdaptPlanRequest(
            reason="I slept badly and have cravings",
            recent_sleep="4 hours",
            notes="strong sweet craving",
        ),
    )

    assert response.revision_scope == "next_meal"
    assert response.revision_applied is True
    assert response.changed_items


def test_ai_adapt_plan_schema_validates_revised_fields():
    parsed, result = NutritionAgentService().adapt_plan(
        NutritionMemoryContext(user_id="u1"),
        reason="hungry",
        recent_context={"hunger": "high"},
    )

    assert result.provider == "mock"
    assert parsed["revised_meals"]
    assert parsed["revised_day"]["meals"]
    assert parsed["changed_items"]
