from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories import onboarding_repository, progress_repository
from app.schemas.ai import AIMealAnalysisResponse, AIWhatToEatNowResponse
from app.services import nutrition_memory_service, prompt_builder
from app.services.safety_guardrail_service import SafetyAssessment


def test_daily_check_in_accepts_new_fields_and_returns_flags(
    client, auth_headers, test_user, db_session: Session
):
    today = date.today().isoformat()

    res = client.post(
        "/api/v1/progress/check-in",
        json={
            "check_date": today,
            "weight_kg": 72.5,
            "waist_cm": 88,
            "hunger_level": 4,
            "hunger_level_1_10": 8,
            "sleep_hours": 5.5,
            "sleep_quality": 2,
            "energy_level": 2,
            "stress_level": 4,
            "activity_minutes": 20,
            "cravings": "sweet cravings after dinner",
            "craving_type": "sweet",
            "eating_location": "work",
            "planned_eating_out": True,
            "adherence_level": 2,
            "symptoms": "mild headache",
            "adherence_notes": "hard day",
        },
        headers=auth_headers,
    )

    assert res.status_code == 201, res.text
    data = res.json()
    assert data["waist_cm"] == 88
    assert data["hunger_level_1_10"] == 8
    assert data["energy_level"] == 2
    assert data["cravings"] == "sweet cravings after dinner"
    assert data["eating_location"] == "work"
    assert data["planned_eating_out"] is True
    assert data["adaptation_hint"] is True
    assert data["human_review_recommended"] is False

    ctx = nutrition_memory_service.build(db_session, test_user)
    assert ctx.recent_checkin_summary is not None
    assert "avg hunger 8.0/10" in ctx.recent_checkin_summary
    assert ctx.energy_trend_summary == "avg energy 2.0/5"
    assert ctx.daily_craving_summary == "sweet cravings after dinner"
    assert ctx.eating_location_summary == "work=1"
    assert ctx.planned_eating_out_summary is not None


def test_daily_check_in_accepts_old_payload(client, auth_headers):
    res = client.post(
        "/api/v1/progress/check-in",
        json={
            "check_date": date.today().isoformat(),
            "weight_kg": 72.5,
            "hunger_level": 2,
            "sleep_hours": 7.5,
        },
        headers=auth_headers,
    )

    assert res.status_code == 201, res.text
    data = res.json()
    assert data["weight_kg"] == 72.5
    assert data["hunger_level"] == 2
    assert data["hunger_level_1_10"] is None


def test_check_in_red_flag_symptoms_set_human_review_flag(client, auth_headers):
    res = client.post(
        "/api/v1/progress/check-in",
        json={
            "check_date": date.today().isoformat(),
            "symptoms": "chest pain and severe dizziness",
        },
        headers=auth_headers,
    )

    assert res.status_code == 201, res.text
    data = res.json()
    assert data["human_review_recommended"] is True
    assert "red_flag_symptoms_reported" in data["safety_notes"]


def test_what_to_eat_now_accepts_old_payload(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/what-to-eat-now",
        json={"available_foods": ["eggs", "bread"], "hunger_level": "medium"},
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["options"]
    assert "reasoning_summary" in data


def test_what_to_eat_now_accepts_structured_context(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/what-to-eat-now",
        json={
            "available_foods": ["yogurt", "bread", "walnuts"],
            "hunger_level": "high",
            "current_place": "work",
            "last_meal_time": "08:00",
            "last_meal_summary": "bread and cheese",
            "current_goal": "weight_loss",
            "hunger_level_1_10": 8,
            "time_available_minutes": 10,
            "cooking_access": "microwave only",
            "budget_context": "low",
            "user_preference_note": "Iranian foods preferred",
        },
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["best_goal_aligned_option"]["option_type"] == "best_goal_aligned"
    assert data["fastest_option"]["option_type"] == "fastest"
    assert data["flexible_option"]["option_type"] == "flexible"
    assert data["options"][0]["household_portions"]


def test_what_to_eat_now_ai_schema_validates_named_options():
    payload = {
        "options": [
            {
                "name": "yogurt with walnuts",
                "option_type": "best_goal_aligned",
                "household_portions": "1 bowl yogurt + 2 walnuts",
                "why_it_fits_goal": "balanced protein and fat",
                "substitutions": ["cheese and bread"],
            }
        ],
        "best_goal_aligned_option": {"name": "yogurt", "option_type": "best_goal_aligned"},
        "fastest_option": {"name": "fruit", "option_type": "fastest"},
        "flexible_option": {"name": "eggs", "option_type": "flexible"},
    }

    parsed = AIWhatToEatNowResponse.model_validate(payload)

    assert parsed.options[0].household_portions == "1 bowl yogurt + 2 walnuts"
    assert parsed.best_goal_aligned_option is not None


def test_meal_analysis_schema_validates_expanded_fields():
    payload = {
        "quality_score": 7,
        "analysis_summary": "Mostly balanced.",
        "likely_meal": "lunch",
        "uncertainties": ["portion unknown"],
        "protein_quality": "moderate",
        "fiber_vegetable_quality": "low",
        "carbohydrate_quality": "refined",
        "fat_quality": "moderate",
        "simple_sugar_quality": "low",
        "portion_volume_assessment": "large plate",
        "satiety_assessment": "medium",
        "likely_goal_effect": "fits if portion is moderate",
        "one_small_correction": "add salad",
        "next_meal_suggestion": "choose a lighter protein meal",
        "no_extreme_compensation_note": "do not skip meals",
    }

    parsed = AIMealAnalysisResponse.model_validate(payload)

    assert parsed.uncertainties == ["portion unknown"]
    assert parsed.satiety_assessment == "medium"
    assert parsed.one_small_correction == "add salad"


def test_meal_analysis_endpoint_returns_expanded_fields(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/meal/analyze",
        json={
            "meal_text": "rice with chicken and salad",
            "meal_time": "lunch",
            "current_goal": "healthy_eating",
            "hunger_level_1_10": 6,
        },
        headers=auth_headers,
    )

    assert res.status_code == 201, res.text
    data = res.json()
    assert data["likely_meal"]
    assert data["uncertainties"]
    assert data["satiety_assessment"]
    assert data["likely_goal_effect"]
    assert data["one_small_correction"]
    assert data["next_meal_suggestion"]
    assert "حذف وعده" in data["no_extreme_compensation_note"]


def test_prompt_sections_include_phase5_workflow_contracts():
    ctx = nutrition_memory_service.NutritionMemoryContext(
        user_id="u1",
        recent_checkin_summary="avg hunger 8/10; cravings: sweet",
    )

    meal_prompt = prompt_builder.for_analyze_meal(
        ctx,
        meal_text="pizza",
        meal_time="dinner",
        meal_context=None,
        extra_context={"current_goal": "weight_loss", "hunger_level_1_10": 8},
    )
    what_prompt = prompt_builder.for_what_to_eat_now(
        ctx,
        available_foods=["egg"],
        hunger_level="high",
        meal_context=None,
        time_available_minutes=5,
        current_context={"current_place": "work", "last_meal_time": "08:00"},
    )

    assert "simple sugar quality" in meal_prompt.user
    assert "satiety assessment" in meal_prompt.user
    assert "Never suggest fasting, detox, purging" in meal_prompt.user
    assert "Structured daily context" in meal_prompt.user
    assert "Structured current context" in what_prompt.user
    assert "household portions" in what_prompt.user
    assert "best_goal_aligned_option" in what_prompt.user


def test_high_risk_what_to_eat_now_keeps_warning(client, auth_headers, test_user, db_session):
    onboarding_repository.create_risk_assessment(
        db_session,
        test_user.id,
        SafetyAssessment(
            risk_level="high",
            flags_triggered=["kidney_disease"],
            clinical_review_required=False,
        ),
    )
    db_session.flush()

    res = client.post(
        "/api/v1/nutrition/what-to-eat-now",
        json={"available_foods": ["bread", "cheese"], "hunger_level": "medium"},
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    assert res.json()["warnings"]


def test_new_checkin_fields_appear_in_progress_summary(client, auth_headers):
    res = client.post(
        "/api/v1/progress/check-in",
        json={
            "check_date": date.today().isoformat(),
            "energy_level": 3,
            "hunger_level_1_10": 7,
            "cravings": "salty snacks",
            "eating_location": "restaurant",
            "planned_eating_out": True,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201

    summary = client.get("/api/v1/progress/summary", headers=auth_headers)

    assert summary.status_code == 200
    data = summary.json()
    assert data["avg_energy_level"] == 3.0
    assert data["avg_hunger_level_1_10"] == 7.0
    assert data["craving_summary"] == "salty snacks"
    assert data["eating_location_summary"] == "restaurant=1"
    assert data["adaptation_hint"] is True


def test_memory_empty_optional_phase5_fields_do_not_crash(db_session: Session, test_user):
    ctx = nutrition_memory_service.build(db_session, test_user)

    assert ctx.energy_trend_summary is None
    assert ctx.daily_craving_summary is None
