"""
NutritionAgentService: orchestrates AI calls for all nutrition tasks.

Builds prompts → prepares messages → calls provider → parses JSON.
Falls back to mock response on parse failure rather than crashing.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.services.ai_provider import AIProvider, AIProviderError, AIProviderResult, get_ai_provider
from app.services.conversation_context_manager import ConversationContextManager
from app.services.mock_ai_provider import MockAIProvider
from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.prompt_builder import (
    for_adapt_plan,
    for_analyze_meal,
    for_chat_message,
    for_generate_plan,
    for_generate_week_plan,
    for_what_to_eat_now,
)

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict | None:
    """Best-effort JSON extraction from provider response text."""
    text = text.strip()
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract from ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # First { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _fallback_mock(task_type: str) -> dict:
    """Return mock data for the given task when real provider JSON is unparseable."""
    mock = MockAIProvider()
    from app.services.mock_ai_provider import (
        TASK_ADAPT_PLAN, TASK_ANALYZE_MEAL, TASK_GENERATE_PLAN, TASK_WHAT_TO_EAT,
    )
    task_tag_map = {
        "generate_plan": TASK_GENERATE_PLAN,
        "analyze_meal": TASK_ANALYZE_MEAL,
        "what_to_eat_now": TASK_WHAT_TO_EAT,
        "adapt_plan": TASK_ADAPT_PLAN,
    }
    tag = task_tag_map.get(task_type, TASK_GENERATE_PLAN)
    result = mock.generate_text([{"role": "system", "content": tag}])
    data = json.loads(result.content)
    return data


class NutritionAgentService:
    def __init__(self) -> None:
        self._provider: AIProvider = get_ai_provider()
        self._ctx_manager = ConversationContextManager(
            max_messages=settings.OPENAI_CONTEXT_MAX_MESSAGES
        )

    def _call(
        self, prompt_data: Any
    ) -> tuple[dict, AIProviderResult]:
        """Call the provider and parse JSON. Falls back to mock on failure."""
        messages = self._ctx_manager.prepare(prompt_data)
        task_type = prompt_data.task_type

        try:
            result = self._provider.generate_text(
                messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
            )
        except AIProviderError as exc:
            logger.warning("AI provider failed (%s), using mock fallback: %s", task_type, exc)
            mock_provider = MockAIProvider()
            result = mock_provider.generate_text(messages)

        parsed = _extract_json(result.content)
        if parsed is None:
            logger.warning("Failed to parse provider JSON for task %s, using mock fallback", task_type)
            parsed = _fallback_mock(task_type)
            result = AIProviderResult(
                content=json.dumps(parsed, ensure_ascii=False),
                provider="mock_fallback",
                model="mock",
                is_mock=True,
            )

        return parsed, result

    def generate_plan(self, ctx: NutritionMemoryContext) -> tuple[dict, AIProviderResult]:
        prompt = for_generate_plan(ctx)
        return self._call(prompt)

    def analyze_meal(
        self,
        ctx: NutritionMemoryContext,
        meal_text: str,
        meal_time: str,
        meal_context: str | None,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_analyze_meal(ctx, meal_text, meal_time, meal_context)
        return self._call(prompt)

    def what_to_eat_now(
        self,
        ctx: NutritionMemoryContext,
        available_foods: list[str],
        hunger_level: str,
        meal_context: str | None,
        time_available_minutes: int | None,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_what_to_eat_now(
            ctx, available_foods, hunger_level, meal_context, time_available_minutes
        )
        return self._call(prompt)

    def chat_message(
        self,
        ctx: NutritionMemoryContext,
        user_message: str,
        history: list[dict[str, str]],
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_chat_message(ctx, user_message, history)
        return self._call(prompt)

    def generate_week_plan(
        self,
        ctx: NutritionMemoryContext,
        locale: str,
    ) -> tuple[dict, AIProviderResult]:
        """Generate a 7-day meal plan in the given locale."""
        prompt = for_generate_week_plan(ctx, locale)
        parsed, result = self._call(prompt)
        # Validate structure: must have 'days' list with at least 7 entries
        if not isinstance(parsed.get("days"), list) or len(parsed["days"]) < 7:
            logger.warning(
                "Week plan response invalid (locale=%s, days=%s), falling back to mock",
                locale,
                len(parsed.get("days") or []),
            )
            from app.services.mock_ai_provider import (
                _MOCK_WEEK_FA, _MOCK_WEEK_EN, _MOCK_WEEK_AR,
            )
            mock_map = {"fa": _MOCK_WEEK_FA, "en": _MOCK_WEEK_EN, "ar": _MOCK_WEEK_AR}
            parsed = mock_map.get(locale, _MOCK_WEEK_FA)
            result = AIProviderResult(
                content=json.dumps(parsed, ensure_ascii=False),
                provider="mock_fallback",
                model="mock",
                is_mock=True,
            )
        return parsed, result

    def adapt_plan(
        self,
        ctx: NutritionMemoryContext,
        reason: str,
        recent_context: dict,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_adapt_plan(ctx, ctx.current_plan_title, reason, recent_context)
        return self._call(prompt)
