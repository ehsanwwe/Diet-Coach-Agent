from __future__ import annotations

import json

from app.services.ai_provider import AIProvider, AIProviderResult
from app.services.nutrition_agent_service import NutritionAgentService
from app.services.nutrition_memory_service import NutritionMemoryContext


class StaticProvider(AIProvider):
    def __init__(self, content: str) -> None:
        self.content = content

    def generate_text(self, messages, temperature=None, max_tokens=None) -> AIProviderResult:
        return AIProviderResult(
            content=self.content,
            provider="static",
            model="test",
            is_mock=False,
        )


def _service_with_provider(content: str) -> NutritionAgentService:
    service = NutritionAgentService()
    service._provider = StaticProvider(content)
    return service


def _ctx() -> NutritionMemoryContext:
    return NutritionMemoryContext(user_id="test-user")


def test_valid_json_provider_output_is_validated_and_returned():
    payload = {
        "reply": "Use a balanced snack and drink water.",
        "extra_field": "ignored",
    }
    parsed, result = _service_with_provider(json.dumps(payload)).chat_message(_ctx(), "hi", [])

    assert parsed == {"reply": "Use a balanced snack and drink water."}
    assert result.provider == "static"
    assert result.is_mock is False


def test_invalid_json_provider_output_falls_back_to_mock():
    parsed, result = _service_with_provider("not-json").chat_message(_ctx(), "hi", [])

    assert "reply" in parsed
    assert result.provider == "mock_fallback"
    assert result.is_mock is True
    assert result.raw_metadata["fallback_reason"] == "invalid_json"


def test_wrong_schema_provider_output_falls_back_to_mock():
    parsed, result = _service_with_provider(json.dumps({"not_reply": "bad"})).chat_message(
        _ctx(), "hi", []
    )

    assert "reply" in parsed
    assert result.provider == "mock_fallback"
    assert result.raw_metadata["fallback_reason"] == "schema_validation_failed"


def test_mock_provider_output_still_validates():
    parsed, result = NutritionAgentService().what_to_eat_now(
        _ctx(),
        available_foods=[],
        hunger_level="medium",
        meal_context=None,
        time_available_minutes=None,
    )

    assert parsed["options"]
    assert result.provider == "mock"
    assert result.is_mock is True
