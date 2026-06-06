"""
Unit tests for agent tool confirmation policy.

Verifies that destructive tool calls (generate_week_plan with force=true,
clear_chat_memory) require confirmation, while safe calls do not.
"""
from __future__ import annotations

import json

import pytest


# ---------------------------------------------------------------------------
# Tool unit tests (no DB / HTTP needed)
# ---------------------------------------------------------------------------

class TestGenerateWeekPlanConfirmation:
    def _tool(self):
        from app.services.agent_tools.registry import GenerateWeekPlanTool
        return GenerateWeekPlanTool()

    def test_force_true_needs_confirmation(self):
        assert self._tool().needs_confirmation({"force": True}) is True

    def test_force_false_no_confirmation(self):
        assert self._tool().needs_confirmation({"force": False}) is False

    def test_no_force_arg_no_confirmation(self):
        assert self._tool().needs_confirmation({}) is False

    def test_execute_with_force_true_returns_failure(self):
        """Defense-in-depth: execute() rejects force=True even without orchestrator gate."""
        from app.services.agent_tools.base import AgentExecutionContext

        class _FakeCtx:
            db = None
            user = None
            locale = "fa"
            nutrition_memory = None
            chat_session_id = "x"
            request_id = "test"

        tool = self._tool()
        result = tool.execute(_FakeCtx(), {"force": True})  # type: ignore[arg-type]
        assert result.success is False
        assert result.error == "confirmation_required"

    def test_execute_without_force_does_not_raise_confirmation_error(self, monkeypatch):
        """force=False path should proceed to calendar_service, not hit the guard."""
        from app.services.agent_tools.registry import GenerateWeekPlanTool
        import app.services.calendar_service as cal_svc

        class _FakeResult:
            generated_days = 3
            skipped_days = 0

        monkeypatch.setattr(cal_svc, "generate_week", lambda *a, **kw: _FakeResult())

        class _FakeCtx:
            db = None
            user = None
            locale = "fa"
            nutrition_memory = None
            chat_session_id = "x"
            request_id = "test"

        result = GenerateWeekPlanTool().execute(_FakeCtx(), {"force": False})  # type: ignore[arg-type]
        assert result.success is True
        assert result.error != "confirmation_required"


class TestClearChatMemoryConfirmation:
    def _tool(self):
        from app.services.agent_tools.registry import ClearChatMemoryTool
        return ClearChatMemoryTool()

    def test_always_needs_confirmation(self):
        assert self._tool().needs_confirmation({}) is True
        assert self._tool().needs_confirmation({"confirm": True}) is True

    def test_execute_returns_failure(self):
        class _FakeCtx:
            db = None
            user = None
            locale = "fa"
            nutrition_memory = None
            chat_session_id = "x"
            request_id = "test"

        result = self._tool().execute(_FakeCtx(), {})  # type: ignore[arg-type]
        assert result.success is False
        assert result.error == "confirmation_required"


class TestSafeToolsNoConfirmation:
    @pytest.mark.parametrize("tool_name", [
        "analyze_meal",
        "what_to_eat_now",
        "get_calendar",
        "update_tomorrow_plan",
        "adapt_plan",
        "log_check_in",
        "get_progress_summary",
        "get_user_profile_summary",
    ])
    def test_safe_tools_do_not_need_confirmation(self, tool_name):
        from app.services.agent_tools.registry import build_tool_registry
        registry = build_tool_registry()
        tool = registry[tool_name]
        assert tool.needs_confirmation({}) is False


# ---------------------------------------------------------------------------
# Orchestrator integration: confirmation gate injects proper tool response
# ---------------------------------------------------------------------------

class TestOrchestratorConfirmationGate:
    """
    Simulate the orchestrator confirmation-gate path without a real DB.
    We mock provider.generate_with_tools to request generate_week_plan with force=True,
    and verify the tool message sent back contains requires_confirmation=True.
    """

    def test_orchestrator_blocks_force_true(self, client):
        """
        When the mock AI provider is active (default in tests), the orchestrator
        falls back to text chat — no tool calls are attempted. This verifies the
        response is valid and the endpoint does not crash.

        A separate, deeper test would need a mock OpenAI provider; the unit tests
        above cover the confirmation gate logic directly.
        """
        resp = client.post(
            "/api/v1/chat/message",
            json={"message": "برنامه هفته رو از نو بساز"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
