"""
NutritionAgentService: orchestrates AI calls for all nutrition tasks.

Builds prompts → prepares messages → calls provider → parses JSON.
Falls back to mock response on parse failure rather than crashing.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai import AI_TASK_SCHEMAS
from app.services.ai_provider import AIProvider, AIProviderError, AIProviderResult, get_ai_provider
from app.services.conversation_context_manager import ConversationContextManager
from app.services.mock_ai_provider import MockAIProvider
from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.prompt_builder import (
    for_adapt_plan,
    for_analyze_meal,
    for_chat_message,
    for_context_guidance,
    for_craving_support,
    for_generate_plan,
    for_generate_week_plan,
    for_repair_week_plan,
    for_weekly_report,
    for_slip_recovery,
    for_what_to_eat_now,
)

logger = logging.getLogger(__name__)
_WEEK_TASK_PREFIXES = ("generate_week_", "repair_week_")


def _dump_week_plan_debug(
    *, prompt_data: Any, messages: list[dict[str, str]], result: AIProviderResult,
    parse_error: str, extracted_json: Any = None, repair_attempt: int | None = None,
    issue_codes: list[str] | None = None,
) -> str | None:
    if not settings.DEBUG_WEEK_PLAN_AI_DUMP:
        return None
    dump_dir = Path(settings.WEEK_PLAN_AI_DUMP_PATH)
    dump_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = dump_dir / f"{stamp}-{prompt_data.task_type}.json"
    payload = {
        "task_type": prompt_data.task_type,
        "provider": result.provider,
        "model": result.model,
        "finish_reason": result.finish_reason,
        "content_length": len(result.content or ""),
        "raw_provider_content": result.content,
        "extracted_json": extracted_json,
        "parse_error": parse_error,
        "system_prompt": prompt_data.system,
        "user_prompt": prompt_data.user,
        "messages": messages,
        "repair_attempt": repair_attempt,
        "issue_codes": issue_codes or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.warning("Week-plan AI debug dump written to %s", path)
    return str(path)


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


def _fallback_mock(
    task_type: str,
    reason: str,
    messages: list[dict[str, str]] | None = None,
) -> tuple[dict, AIProviderResult]:
    """Return mock data for the given task when real provider JSON is unparseable."""
    mock = MockAIProvider()
    from app.services.mock_ai_provider import (
        TASK_ADAPT_PLAN, TASK_ANALYZE_MEAL, TASK_GENERATE_PLAN, TASK_WHAT_TO_EAT,
        TASK_CHAT, TASK_CONTEXT_GUIDANCE, TASK_CRAVING_SUPPORT, TASK_GENERATE_WEEK_AR,
        TASK_GENERATE_WEEK_EN, TASK_GENERATE_WEEK_FA, TASK_SLIP_RECOVERY, TASK_WEEKLY_REPORT,
        TASK_REPAIR_WEEK_AR, TASK_REPAIR_WEEK_EN, TASK_REPAIR_WEEK_FA,
    )
    task_tag_map = {
        "generate_plan": TASK_GENERATE_PLAN,
        "analyze_meal": TASK_ANALYZE_MEAL,
        "what_to_eat_now": TASK_WHAT_TO_EAT,
        "craving_support": TASK_CRAVING_SUPPORT,
        "slip_recovery": TASK_SLIP_RECOVERY,
        "context_guidance": TASK_CONTEXT_GUIDANCE,
        "adapt_plan": TASK_ADAPT_PLAN,
        "chat_message": TASK_CHAT,
        "generate_week_fa": TASK_GENERATE_WEEK_FA,
        "generate_week_en": TASK_GENERATE_WEEK_EN,
        "generate_week_ar": TASK_GENERATE_WEEK_AR,
        "repair_week_fa": TASK_REPAIR_WEEK_FA,
        "repair_week_en": TASK_REPAIR_WEEK_EN,
        "repair_week_ar": TASK_REPAIR_WEEK_AR,
        "weekly_report": TASK_WEEKLY_REPORT,
    }
    tag = task_tag_map.get(task_type, TASK_GENERATE_PLAN)
    fallback_messages = list(messages or [])
    fallback_messages.insert(0, {"role": "system", "content": tag})
    result = mock.generate_text(fallback_messages)
    data = json.loads(result.content)
    return data, AIProviderResult(
        content=json.dumps(data, ensure_ascii=False),
        provider="mock_fallback",
        model="mock",
        finish_reason=result.finish_reason,
        raw_metadata={"fallback_reason": reason, "fallback_task": task_type},
        is_mock=True,
    )


def _validate_task_output(task_type: str, data: dict) -> dict:
    """Validate and normalize provider output for a known AI task."""
    schema = AI_TASK_SCHEMAS.get(task_type)
    if schema is None:
        return data
    validated = schema.model_validate(data)
    return validated.model_dump(mode="json", exclude_none=True)


class NutritionAgentService:
    def __init__(self) -> None:
        self._provider: AIProvider = get_ai_provider()
        self._ctx_manager = ConversationContextManager(
            max_messages=settings.OPENAI_CONTEXT_MAX_MESSAGES
        )

    def _call(
        self, prompt_data: Any, *, repair_attempt: int | None = None,
        issue_codes: list[str] | None = None,
    ) -> tuple[dict, AIProviderResult]:
        """Call the provider and parse JSON. Falls back to mock on failure."""
        messages = self._ctx_manager.prepare(prompt_data)
        task_type = prompt_data.task_type

        fallback_reason: str | None = None
        try:
            max_tokens = (
                settings.OPENAI_WEEK_PLAN_MAX_TOKENS
                if task_type.startswith(_WEEK_TASK_PREFIXES)
                else settings.OPENAI_MAX_TOKENS
            )
            result = self._provider.generate_text(
                messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=max_tokens,
            )
        except AIProviderError as exc:
            logger.warning("AI provider failed (%s), using mock fallback: %s", task_type, exc)
            parsed, result = _fallback_mock(task_type, "provider_error", messages)
            return _validate_task_output(task_type, parsed), result

        if task_type.startswith(_WEEK_TASK_PREFIXES):
            logger.info(
                "Week-plan provider call task_type=%s provider=%s model=%s finish_reason=%s content_length=%d",
                task_type, result.provider, result.model, result.finish_reason, len(result.content or ""),
            )
        parsed = _extract_json(result.content)
        if parsed is None:
            _dump_week_plan_debug(
                prompt_data=prompt_data, messages=messages, result=result,
                parse_error="invalid_json", repair_attempt=repair_attempt, issue_codes=issue_codes,
            )
            logger.warning("Failed to parse provider JSON for task %s, using mock fallback", task_type)
            fallback_reason = "invalid_json"
        elif not isinstance(parsed, dict):
            logger.warning("Provider JSON for task %s was not an object, using mock fallback", task_type)
            fallback_reason = "non_object_json"

        if fallback_reason is not None:
            parsed, result = _fallback_mock(task_type, fallback_reason, messages)

        try:
            parsed = _validate_task_output(task_type, parsed)
        except ValidationError as exc:
            if task_type.startswith(_WEEK_TASK_PREFIXES):
                _dump_week_plan_debug(
                    prompt_data=prompt_data, messages=messages, result=result,
                    parse_error=f"schema_validation_failed: {exc}", extracted_json=parsed,
                    repair_attempt=repair_attempt, issue_codes=issue_codes,
                )
            logger.warning(
                "Provider JSON schema validation failed for task %s, using mock fallback: %s",
                task_type,
                exc,
            )
            parsed, result = _fallback_mock(task_type, "schema_validation_failed", messages)
            parsed = _validate_task_output(task_type, parsed)

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
        extra_context: dict | None = None,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_analyze_meal(ctx, meal_text, meal_time, meal_context, extra_context)
        return self._call(prompt)

    def what_to_eat_now(
        self,
        ctx: NutritionMemoryContext,
        available_foods: list[str],
        hunger_level: str,
        meal_context: str | None,
        time_available_minutes: int | None,
        current_context: dict | None = None,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_what_to_eat_now(
            ctx, available_foods, hunger_level, meal_context, time_available_minutes, current_context
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

    def craving_support(
        self,
        ctx: NutritionMemoryContext,
        request_context: dict,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_craving_support(ctx, request_context)
        return self._call(prompt)

    def slip_recovery(
        self,
        ctx: NutritionMemoryContext,
        request_context: dict,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_slip_recovery(ctx, request_context)
        return self._call(prompt)

    def context_guidance(
        self,
        ctx: NutritionMemoryContext,
        request_context: dict,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_context_guidance(ctx, request_context)
        return self._call(prompt)

    def generate_week_plan(
        self,
        ctx: NutritionMemoryContext,
        locale: str,
        extra_context: str | None = None,
        progress: Callable[[str, str], None] | None = None,
    ) -> tuple[dict, AIProviderResult]:
        """Generate, review, and ask the provider to repair a 7-day plan."""
        from app.services.week_plan_quality_evaluator import (
            evaluate_week_plan_quality,
            has_blocking_quality_issues,
        )
        from app.services.weekly_plan_personalization_validator import validate_and_sanitize

        prompt = for_generate_week_plan(ctx, locale, extra_context=extra_context)
        if progress:
            progress("generating_plan", "requesting_week_plan")
        parsed, result = self._call(prompt)
        best_plan: dict | None = None
        best_result: AIProviderResult | None = None
        best_issues: list[Any] = []
        best_score: tuple[int, int] | None = None
        for repair_attempt in range(3):
            if progress:
                progress("reviewing_plan", "reviewing_plan")
            normalized = validate_and_sanitize(parsed, ctx, locale=locale)
            issues = evaluate_week_plan_quality(normalized, ctx, locale)
            score = (
                sum(issue.severity == "safety_blocker" for issue in issues),
                sum(issue.severity == "repairable_quality" for issue in issues),
            )
            if best_score is None or score < best_score:
                best_plan, best_result, best_issues, best_score = normalized, result, issues, score
            if not issues:
                return normalized, result
            if repair_attempt == 2:
                assert best_plan is not None and best_result is not None
                if has_blocking_quality_issues(best_issues):
                    codes = sorted({issue.code for issue in best_issues if issue.severity == "safety_blocker"})
                    logger.error("Week plan rejected after two repairs; safety blockers: %s", codes)
                    raise AIProviderError(
                        "Generated week plan still violates required safety constraints after two repairs: "
                        + ", ".join(codes)
                    )
                logger.warning(
                    "Accepting safe week plan with remaining repairable quality warnings: %s",
                    [issue.code for issue in best_issues],
                )
                return best_plan, best_result
            logger.warning(
                "Week plan failed review; requesting LLM repair attempt %d: %s",
                repair_attempt + 1,
                [issue.code for issue in issues],
            )
            repair_prompt = for_repair_week_plan(ctx, locale, normalized, issues)
            if progress:
                progress("repairing_plan", f"repairing_plan_{repair_attempt + 1}")
            parsed, result = self._call(
                repair_prompt, repair_attempt=repair_attempt + 1,
                issue_codes=[issue.code for issue in issues],
            )

        raise AIProviderError("Week plan quality review failed")

    def weekly_report(
        self,
        ctx: NutritionMemoryContext,
        weekly_metrics: dict,
        locale: str,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_weekly_report(ctx, weekly_metrics, locale)
        return self._call(prompt)

    def adapt_plan(
        self,
        ctx: NutritionMemoryContext,
        reason: str,
        recent_context: dict,
    ) -> tuple[dict, AIProviderResult]:
        prompt = for_adapt_plan(ctx, ctx.current_plan_title, reason, recent_context)
        return self._call(prompt)
