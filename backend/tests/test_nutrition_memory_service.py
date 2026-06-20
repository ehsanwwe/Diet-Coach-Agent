from __future__ import annotations

from datetime import date, datetime, timedelta
import json

from sqlalchemy.orm import Session

from app.models.progress import ProgressEntry
from app.models.user import User
from app.repositories import calendar_repository, nutrition_repository, onboarding_repository, progress_repository
from app.services import nutrition_memory_service, prompt_builder
from app.services.ai_provider import AIProvider, AIProviderResult
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.safety_guardrail_service import SafetyAssessment


def _seed_profile(db: Session, user: User) -> None:
    onboarding_repository.upsert_profile(
        db,
        user.id,
        full_name="Test User",
        gender="female",
        birth_date=date(1990, 1, 1),
        height_cm=165,
        weight_kg=72,
        target_weight_kg=66,
        waist_cm=88,
    )
    nutrition_repository.upsert_nutrition_goal(db, user.id, "weight_loss")
    onboarding_repository.replace_medical_flags(db, user.id, {"none": False})
    onboarding_repository.create_risk_assessment(
        db,
        user.id,
        SafetyAssessment(risk_level="low", flags_triggered=[], clinical_review_required=False),
    )
    db.flush()


def _seed_lifestyle_and_behavior(db: Session, user: User) -> None:
    onboarding_repository.upsert_lifestyle(
        db,
        user.id,
        sleep_hours=6,
        stress_level=4,
        work_schedule="office",
        activity_level="light",
        exercise_days_per_week=2,
        cooking_ability=3,
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
        disliked_foods=["fish"],
        favorite_foods=["عدسی", "کباب"],
        breakfast_habit="irregular",
        rice_frequency="moderate",
        bread_frequency="daily",
        sweets_frequency="medium",
        tea_frequency="daily",
        restaurant_frequency="weekly",
    )
    onboarding_repository.upsert_behavior_profile(
        db,
        user.id,
        emotional_eating=True,
        night_eating=True,
        meal_skipping=True,
        cravings=["sweet after dinner", "chocolate"],
        binge_history=True,
        diet_history="tried strict low-carb diet",
        previous_failures="gave up when dinners were hard",
        hunger_pattern="late-night hunger",
        motivation_level=3,
    )
    db.flush()


def test_memory_includes_waist_when_available(db_session: Session, test_user: User):
    _seed_profile(db_session, test_user)

    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.waist_circumference == 88
    assert ctx.to_compact_dict()["waist_circumference"] == 88
    assert ctx.to_prompt_memory()["stable_user_profile"]["waist_circumference"] == 88


def test_memory_includes_onboarding_behavior_fields(db_session: Session, test_user: User):
    _seed_profile(db_session, test_user)
    _seed_lifestyle_and_behavior(db_session, test_user)

    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.cravings == ["sweet after dinner", "chocolate"]
    assert ctx.previous_failures == "gave up when dinners were hard"
    assert ctx.previous_failures_summary == "gave up when dinners were hard"
    assert ctx.craving_patterns == "sweet after dinner, chocolate"
    assert ctx.emotional_eating_pattern == "reported"
    assert ctx.stress_eating_pattern is not None
    assert ctx.sleep_craving_pattern is not None


def test_memory_includes_recent_checkin_and_progress_summaries(
    db_session: Session, test_user: User
):
    today = date.today()
    for idx in range(3):
        progress_repository.upsert_checkin(
            db_session,
            test_user.id,
            check_date=today - timedelta(days=idx),
            weight_kg=72 - idx * 0.2,
            hunger_level=3 + idx,
            sleep_hours=6 + idx * 0.5,
            stress_level=4 - idx,
            activity_minutes=20 + idx * 10,
            adherence_notes=f"note {idx}",
        )
    db_session.add(
        ProgressEntry(
            user_id=test_user.id,
            entry_type="waist",
            value_numeric=88,
            value_text=None,
            recorded_at=datetime.now() - timedelta(days=7),
        )
    )
    db_session.add(
        ProgressEntry(
            user_id=test_user.id,
            entry_type="waist",
            value_numeric=86,
            value_text=None,
            recorded_at=datetime.now(),
        )
    )
    progress_repository.save_weekly_report(
        db_session,
        test_user.id,
        week_start=today - timedelta(days=6),
        week_end=today,
        report_data={"avg_sleep": 6.5, "avg_stress": 3, "suggested_focus": "sleep"},
    )
    db_session.flush()

    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.recent_checkin_summary is not None
    assert "avg sleep" in ctx.recent_checkin_summary
    assert ctx.progress_history_summary is not None
    assert "waist" in ctx.progress_history_summary
    assert ctx.weekly_insights_summary is not None
    assert "suggested_focus=sleep" in ctx.weekly_insights_summary
    assert ctx.body_response_summary is not None


def test_memory_includes_meal_history_and_active_plan_summary(
    db_session: Session, test_user: User
):
    nutrition_repository.create_meal_entry(
        db_session,
        test_user.id,
        meal_time="lunch",
        description="rice with chicken",
        analysis_result={"quality_score": 7, "analysis_summary": "balanced lunch"},
        logged_at=datetime.now(),
    )
    nutrition_repository.create_plan(
        db_session,
        test_user.id,
        title="Full plan",
        description="balanced active plan",
        plan_metadata={
            "plan_type": "full_plan",
            "daily_guidelines": {"calories": 1900},
            "warnings": ["review if symptoms change"],
        },
        generated_by="mock",
    )
    db_session.flush()

    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.meal_history_summary is not None
    assert "rice with chicken" in ctx.meal_history_summary
    assert ctx.active_plan_summary is not None
    assert "plan_type=full_plan" in ctx.active_plan_summary


def test_memory_includes_active_calendar_summary(db_session: Session, test_user: User):
    cal = calendar_repository.get_or_create_calendar(db_session, test_user.id, "fa")
    day = calendar_repository.create_plan_day(
        db_session,
        calendar_id=cal.id,
        user_id=test_user.id,
        locale="fa",
        plan_date=date.today(),
        day_index=1,
        title="روز اول",
        summary="برنامه متعادل",
        hydration_goal="۸ لیوان آب",
        notes=None,
        warnings=["هشدار نمونه"],
    )
    calendar_repository.create_plan_day_meal(
        db_session,
        plan_day_id=day.id,
        locale="fa",
        meal_type="lunch",
        title="عدسی",
        description="عدسی با نان",
        portion_guidance="یک کاسه",
        alternatives=[],
        preparation_notes=None,
    )
    db_session.flush()

    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.active_calendar_summary is not None
    assert "planned days" in ctx.active_calendar_summary
    assert "روز اول" in ctx.active_calendar_summary


def test_empty_optional_history_does_not_crash_memory_build(
    db_session: Session, test_user: User
):
    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.meal_history_summary is None
    assert ctx.recent_checkin_summary is None
    assert "meal_history" in ctx.to_prompt_memory()["missing_or_unknown_data"]


def test_prompt_builder_includes_expanded_memory_sections():
    ctx = nutrition_memory_service.NutritionMemoryContext(
        user_id="u1",
        waist_circumference=90,
        meal_history_summary="3 recent meals",
        recent_checkin_summary="avg sleep 6.5h",
        active_plan_summary="plan_type=full_plan",
    )

    prompt = prompt_builder.for_chat_message(ctx, "what should I eat?", [])

    assert "Memory/context use" in prompt.system
    assert "stable_user_profile" in prompt.user
    assert "recent_progress_checkins" in prompt.user
    assert "active_plan_context" in prompt.user
    assert "waist_circumference" in prompt.user


class CapturingProvider(AIProvider):
    def __init__(self) -> None:
        self.messages = []

    def generate_text(self, messages, temperature=None, max_tokens=None) -> AIProviderResult:
        self.messages = messages
        return AIProviderResult(
            content=json.dumps({"reply": "ok"}),
            provider="capture",
            model="test",
            is_mock=False,
        )


def test_nutrition_agent_service_passes_memory_context_into_prompts():
    ctx = nutrition_memory_service.NutritionMemoryContext(
        user_id="u1",
        meal_history_summary="recent meal memory",
        active_plan_summary="active plan memory",
    )
    provider = CapturingProvider()
    service = NutritionAgentService()
    service._provider = provider

    service.chat_message(ctx, "hello", [])

    joined = "\n".join(m.get("content", "") for m in provider.messages)
    assert "recent meal memory" in joined
    assert "active plan memory" in joined
    assert "stable_user_profile" in joined
