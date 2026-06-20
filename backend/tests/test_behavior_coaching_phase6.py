from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.repositories import onboarding_repository
from app.schemas.ai import (
    AIContextGuidanceResponse,
    AICravingSupportResponse,
    AISlipRecoveryResponse,
)
from app.services import nutrition_memory_service, prompt_builder
from app.services.mock_ai_provider import (
    _MOCK_CONTEXT_GUIDANCE,
    _MOCK_CRAVING_SUPPORT,
    _MOCK_SLIP_RECOVERY,
)
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.safety_guardrail_service import SafetyAssessment


def _ctx() -> nutrition_memory_service.NutritionMemoryContext:
    return nutrition_memory_service.NutritionMemoryContext(
        user_id="u1",
        risk_level="low",
        craving_patterns="sweet after dinner",
        previous_failures_summary="strict plans were hard at dinner",
        recent_checkin_summary="avg hunger 8/10; cravings: sweets",
        active_plan_summary="plan_type=full_plan",
    )


def test_craving_support_endpoint_returns_schema_safe_response(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/craving-support",
        json={
            "craving_food": "chocolate",
            "craving_intensity_1_10": 8,
            "hunger_level_1_10": 6,
            "stress_level": 4,
            "current_place": "home",
            "available_foods": ["yogurt", "walnuts"],
        },
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["calming_message"]
    assert data["likely_triggers"]
    assert data["immediate_options"]
    assert data["better_choice"]["title"]
    assert data["requires_human_review"] is False


def test_slip_recovery_endpoint_follows_protocol_fields(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/slip-recovery",
        json={
            "what_happened": "I overate sweets and feel guilty",
            "foods_eaten": ["cake", "cookies"],
            "emotion_after": "guilt",
            "restriction_before_slip": True,
        },
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["calming_message"]
    assert data["data_not_failure_message"]
    assert data["likely_trigger_questions"]
    assert data["pattern_hypothesis"]
    assert data["one_small_adjustment"]
    assert data["next_meal_plan"]
    assert data["tomorrow_reset_note"]
    assert "توصیه نمی‌شود" in data["no_extreme_compensation_note"]


def test_context_guidance_endpoint_returns_choice_portion_and_next_meal(client, auth_headers):
    res = client.post(
        "/api/v1/nutrition/context-guidance",
        json={
            "context_type": "restaurant",
            "available_options": ["pizza", "chicken kebab", "salad"],
            "preferred_option": "pizza",
            "current_goal": "weight_loss",
            "hunger_level_1_10": 7,
        },
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["best_available_choice"]
    assert data["flexible_choice"]
    assert data["portion_strategy"]
    assert data["plate_balance_tip"]
    assert data["next_meal_adjustment"]


def test_prompt_builder_includes_behavior_workflow_instructions():
    craving = prompt_builder.for_craving_support(_ctx(), {"craving_food": "sweets"})
    slip = prompt_builder.for_slip_recovery(_ctx(), {"what_happened": "overate"})
    context = prompt_builder.for_context_guidance(_ctx(), {"context_type": "restaurant"})

    assert "Normalize the experience without shame" in craving.user
    assert "Distinguish physical hunger from craving" in craving.user
    assert "severe restriction" in craving.user
    assert "Follow this 6-step slip recovery protocol" in slip.user
    assert "useful data, not a failure" in slip.user
    assert "Never suggest fasting, detox, purging" in slip.user
    assert "no absolute bans" in context.user
    assert "dessert/sweets strategy" in context.user
    assert "Iranian/Persian foods" in context.user


def test_mock_provider_outputs_validate_for_behavior_workflows():
    assert AICravingSupportResponse.model_validate(_MOCK_CRAVING_SUPPORT).calming_message
    assert AISlipRecoveryResponse.model_validate(_MOCK_SLIP_RECOVERY).data_not_failure_message
    assert AIContextGuidanceResponse.model_validate(_MOCK_CONTEXT_GUIDANCE).portion_strategy


def test_nutrition_agent_service_behavior_methods_validate_mock_outputs():
    service = NutritionAgentService()

    craving, craving_result = service.craving_support(_ctx(), {"craving_food": "sweets"})
    slip, slip_result = service.slip_recovery(_ctx(), {"what_happened": "overate"})
    context, context_result = service.context_guidance(_ctx(), {"context_type": "travel"})

    assert craving["calming_message"]
    assert slip["data_not_failure_message"]
    assert context["best_available_choice"]
    assert craving_result.provider == "mock"
    assert slip_result.provider == "mock"
    assert context_result.provider == "mock"


def test_chat_routes_obvious_persian_and_english_craving_messages(client, auth_headers):
    for message in ["هوس شیرینی کردم", "I am craving sweets"]:
        res = client.post("/api/v1/chat/message", json={"message": message}, headers=auth_headers)
        assert res.status_code == 201, res.text
        data = res.json()["data"]
        assert data["actions_summary"] == ["craving_support"]
        assert data["tool_calls_executed"] == 1
        assert "هوس" in data["content"] or "اطلاعات" in data["content"]


def test_chat_routes_obvious_persian_and_english_slip_messages(client, auth_headers):
    for message in ["پرخوری کردم و رژیمم خراب شد", "I overate and broke my diet"]:
        res = client.post("/api/v1/chat/message", json={"message": message}, headers=auth_headers)
        assert res.status_code == 201, res.text
        data = res.json()["data"]
        assert data["actions_summary"] == ["slip_recovery"]
        assert "شکست" in data["content"] or "خراب" in data["content"] or "داده" in data["content"]


def test_chat_routes_obvious_restaurant_party_travel_messages(client, auth_headers):
    for message in ["رستورانم چی بخورم", "I am traveling, what should I eat?"]:
        res = client.post("/api/v1/chat/message", json={"message": message}, headers=auth_headers)
        assert res.status_code == 201, res.text
        data = res.json()["data"]
        assert data["actions_summary"] == ["context_guidance"]
        assert data["content"]


def test_high_risk_and_clinical_users_receive_safety_notes(
    client, auth_headers, test_user, db_session: Session
):
    onboarding_repository.create_risk_assessment(
        db_session,
        test_user.id,
        SafetyAssessment(risk_level="high", flags_triggered=["heart_disease"]),
    )
    db_session.flush()

    high = client.post(
        "/api/v1/nutrition/craving-support",
        json={"craving_food": "sweets"},
        headers=auth_headers,
    )
    assert high.status_code == 200
    assert high.json()["safety_notes"]

    onboarding_repository.create_risk_assessment(
        db_session,
        test_user.id,
        SafetyAssessment(
            risk_level="clinical_review_required",
            flags_triggered=["eating_disorder_history"],
            clinical_review_required=True,
        ),
    )
    db_session.flush()

    clinical = client.post(
        "/api/v1/nutrition/context-guidance",
        json={"context_type": "party", "available_options": ["cake"]},
        headers=auth_headers,
    )
    assert clinical.status_code == 200
    assert clinical.json()["requires_human_review"] is True


def test_eating_disorder_history_does_not_produce_restrictive_coaching(
    client, auth_headers, test_user, db_session: Session
):
    onboarding_repository.replace_medical_flags(
        db_session,
        test_user.id,
        {"eating_disorder_history": True},
    )
    db_session.flush()

    res = client.post(
        "/api/v1/nutrition/slip-recovery",
        json={"what_happened": "I ate sweets and want to stop eating tomorrow"},
        headers=auth_headers,
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["requires_human_review"] is True
    assert any("eating_disorder_history" in note for note in data["safety_notes"])
    assert "توصیه نمی‌شود" in data["no_extreme_compensation_note"]


def test_slip_recovery_mock_does_not_recommend_extreme_compensation():
    parsed = AISlipRecoveryResponse.model_validate(_MOCK_SLIP_RECOVERY)
    combined = json.dumps(parsed.model_dump(mode="json"), ensure_ascii=False)

    assert "شکست" in parsed.data_not_failure_message
    assert "توصیه نمی‌شود" in (parsed.no_extreme_compensation_note or "")
    assert "روزه سخت" in combined
    assert "حذف وعده" in combined
