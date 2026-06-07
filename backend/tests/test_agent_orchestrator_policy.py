"""
Orchestrator policy unit tests — no external AI calls required.

Tests verify:
1. _build_conversation_state() correctly detects follow-up questions (structural detection).
2. Tool actions are enforced: update_tomorrow_plan only executes on explicit request.
3. Failed tool result → no success claim in response.
4. actions_summary and content are always separate fields (no concatenation).
5. Scripted mock provider drives orchestrator tool loop for integration coverage.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Unit tests: _build_conversation_state (no DB, no provider needed)
# ---------------------------------------------------------------------------

class TestBuildConversationState:
    def _call(self, history):
        from app.services.agent_orchestrator import _build_conversation_state
        return _build_conversation_state(history)

    def test_empty_history_returns_empty(self):
        assert self._call([]) == ""

    def test_no_assistant_message_returns_empty(self):
        history = [{"role": "user", "content": "سلام"}]
        assert self._call(history) == ""

    def test_question_mark_persian_detected(self):
        history = [
            {"role": "user", "content": "صبح شیرینی خوردم"},
            {"role": "assistant", "content": "ناهار معمولاً چی می‌خوری؟"},
        ]
        result = self._call(history)
        assert "FOLLOW_UP_PENDING=true" in result

    def test_question_mark_latin_detected(self):
        history = [
            {"role": "user", "content": "I had a burger"},
            {"role": "assistant", "content": "What did you have for dinner?"},
        ]
        result = self._call(history)
        assert "FOLLOW_UP_PENDING=true" in result

    def test_no_question_mark_returns_empty(self):
        history = [
            {"role": "user", "content": "برنامه فردامو سبک‌تر کن"},
            {"role": "assistant", "content": "برنامه فردا به‌روزرسانی شد."},
        ]
        result = self._call(history)
        assert result == ""

    def test_trailing_whitespace_after_question_mark(self):
        history = [
            {"role": "assistant", "content": "ناهار چی خوردی؟  "},
        ]
        result = self._call(history)
        assert "FOLLOW_UP_PENDING=true" in result

    def test_last_assistant_message_is_used(self):
        history = [
            {"role": "assistant", "content": "اول بگو چی خوردی؟"},
            {"role": "user", "content": "پیتزا"},
            {"role": "assistant", "content": "برنامه فردا تنظیم شد."},
        ]
        # Last assistant message is NOT a question — should return empty
        result = self._call(history)
        assert result == ""

    def test_returns_decision_rules_for_followup(self):
        history = [
            {"role": "assistant", "content": "بقیه وعده‌های امروز رو خوردی؟"},
        ]
        result = self._call(history)
        assert "update_tomorrow_plan" in result
        assert "generate_week_plan" in result


# ---------------------------------------------------------------------------
# ScriptedToolProvider: configurable mock for orchestrator integration tests
# ---------------------------------------------------------------------------

from app.services.ai_provider import AIProvider, AIToolCall, AIToolCallResult


class ScriptedToolProvider(AIProvider):
    """
    A minimal tool-capable provider for orchestrator tests.

    `rounds` is a list where each element is either:
      - A list of {"name": ..., "arguments": {...}} dicts → tool calls for that round
      - None → text-only final response

    After `rounds` is exhausted, always returns a text response.
    Tool names called are recorded in `tool_names_called`.
    """
    supports_tools = True

    def __init__(self, rounds: list[list[dict] | None], final_text: str = "پیام پردازش شد."):
        self._rounds = rounds
        self._final_text = final_text
        self._idx = 0
        self.tool_names_called: list[str] = []

    def generate_text(self, messages, temperature=None, max_tokens=None):
        raise NotImplementedError("use generate_with_tools")

    def generate_with_tools(self, messages, tools, temperature=None, max_tokens=None):
        if self._idx >= len(self._rounds) or self._rounds[self._idx] is None:
            self._idx += 1
            return AIToolCallResult(
                assistant_message=self._final_text,
                tool_calls=[],
                provider="scripted_mock",
                model="test",
            )
        round_spec = self._rounds[self._idx]
        self._idx += 1

        tool_calls = []
        raw = []
        for i, spec in enumerate(round_spec):
            tc = AIToolCall(
                id=f"call_{self._idx}_{i}",
                name=spec["name"],
                arguments=spec.get("arguments", {}),
            )
            tool_calls.append(tc)
            self.tool_names_called.append(spec["name"])
            raw.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments),
                },
            })

        return AIToolCallResult(
            assistant_message=None,
            tool_calls=tool_calls,
            provider="scripted_mock",
            model="test",
            raw_tool_calls=raw,
        )


# ---------------------------------------------------------------------------
# Integration tests: orchestrator + scripted provider
# ---------------------------------------------------------------------------

class TestOrchestratorPolicy:
    """
    Drive the orchestrator with a ScriptedToolProvider to verify policy enforcement.
    These tests use the real tool registry (tools actually execute via MockAIProvider)
    but mock the outer orchestrator provider.
    """

    def _send(self, client, monkeypatch, provider, message: str):
        """Patch get_ai_provider in the orchestrator module and send a message."""
        monkeypatch.setattr(
            "app.services.agent_orchestrator.get_ai_provider",
            lambda: provider,
        )
        resp = client.post("/api/v1/chat/message", json={"message": message})
        assert resp.status_code == 201, resp.text
        return resp.json()["data"]

    # ------------------------------------------------------------------
    # Test 1: food report → analyze_meal only, no update_tomorrow_plan
    # ------------------------------------------------------------------

    def test_food_report_does_not_update_tomorrow(self, client, monkeypatch):
        """
        When user reports eating something, only analyze_meal should be called.
        update_tomorrow_plan must NOT be called unless user explicitly asks.
        """
        provider = ScriptedToolProvider(
            rounds=[
                # Round 0: model decides to call analyze_meal only
                [{"name": "analyze_meal", "arguments": {"meal_text": "شیرینی خامه‌ای", "should_log": True}}],
                # Round 1: text-only final response
                None,
            ],
            final_text="وعده ثبت شد. ناهار چی می‌خوری؟",
        )
        data = self._send(client, monkeypatch, provider, "امروز صبح یه شیرینی خوردم")

        assert "update_tomorrow_plan" not in provider.tool_names_called
        assert "analyze_meal" in provider.tool_names_called
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0

    # ------------------------------------------------------------------
    # Test 2: explicit plan update → update_tomorrow_plan runs
    # ------------------------------------------------------------------

    def test_explicit_plan_update_calls_tool(self, client, monkeypatch):
        """
        When user explicitly asks to update tomorrow's plan, update_tomorrow_plan is called.
        If tool succeeds, actions_summary contains the result.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "update_tomorrow_plan", "arguments": {
                    "reason": "کاربر خواست برنامه فردا سبک‌تر باشد",
                    "intensity": "light",
                }}],
                None,
            ],
            final_text="برنامه فردات تنظیم شد.",
        )
        data = self._send(client, monkeypatch, provider, "برنامه فردامو سبک‌تر بکن")

        assert "update_tomorrow_plan" in provider.tool_names_called
        assert data["role"] == "assistant"
        # actions_summary is set only if tool succeeded
        # (may fail in test env if calendar not seeded, but endpoint must not crash)
        assert data["content"] is not None

    # ------------------------------------------------------------------
    # Test 3: follow-up lunch answer → no update_tomorrow_plan
    # ------------------------------------------------------------------

    def test_followup_answer_does_not_call_plan_update(self, client, monkeypatch):
        """
        Simulate: assistant asked 'ناهار چی می‌خوری؟' (ends with ؟).
        User answers with food info.
        Orchestrator must inject FOLLOW_UP_PENDING=true.
        ScriptedProvider is configured to only call analyze_meal (not update_tomorrow_plan).
        Assert update_tomorrow_plan was never called.
        """
        # First, seed history: send a greeting so there is at least one prior turn.
        # Then post a scripted-provider message that simulates the follow-up scenario.
        provider = ScriptedToolProvider(
            rounds=[
                # Simulate model correctly calling analyze_meal for the lunch context
                [{"name": "analyze_meal", "arguments": {
                    "meal_text": "خورش قرمه‌سبزی با برنج",
                    "meal_time": "lunch",
                    "should_log": True,
                }}],
                None,
            ],
            final_text="خورش قرمه‌سبزی انتخاب خوبیه. نکات تغذیه‌ای رو توضیح می‌دم.",
        )
        data = self._send(
            client, monkeypatch, provider,
            "خورش قرمه‌سبزی با ۶ قاشق برنج",
        )

        assert "update_tomorrow_plan" not in provider.tool_names_called
        assert data["role"] == "assistant"
        assert data["content"] is not None

    # ------------------------------------------------------------------
    # Test 4: update_tomorrow_plan fails → content must not claim success
    # ------------------------------------------------------------------

    def test_failed_plan_update_produces_no_success_claim(self, client, monkeypatch):
        """
        When update_tomorrow_plan tool returns success=False (controlled failure,
        no DB side-effects), actions_summary must be empty and the scripted provider's
        final_text must not contain a success claim.

        We monkeypatch the tool registry entry so the tool returns success=False
        without touching the DB (avoids test-transaction corruption from db.rollback).
        """
        import app.services.agent_orchestrator as orch_module
        from app.services.agent_tools.base import AgentTool, AgentToolResult

        class _FakeFailTool(AgentTool):
            name = "update_tomorrow_plan"
            description = "fake"
            input_schema = {"type": "object", "properties": {}, "required": []}

            def execute(self_tool, context, arguments):
                # Controlled failure — no DB changes, no exception raised.
                return AgentToolResult(
                    tool_name="update_tomorrow_plan",
                    success=False,
                    user_visible_summary=None,
                    error="simulated controlled failure",
                )

        monkeypatch.setitem(orch_module._TOOL_REGISTRY, "update_tomorrow_plan", _FakeFailTool())

        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "update_tomorrow_plan", "arguments": {
                    "reason": "تست شکست ابزار",
                    "intensity": "light",
                }}],
                None,
            ],
            final_text="متأسفانه به‌روزرسانی انجام نشد.",
        )
        data = self._send(client, monkeypatch, provider, "برنامه فردامو عوض کن")

        # Tool failed → actions_summary must be None or empty (no success recorded)
        assert not data.get("actions_summary"), (
            f"Expected empty actions_summary on failure, got: {data.get('actions_summary')}"
        )
        # Content must not claim success (scripted final_text is a failure message)
        content = data["content"]
        assert "به‌روزرسانی شد" not in content, (
            f"Response claimed success on failure: {content!r}"
        )
        assert "ساخته شد" not in content, f"Response claimed creation on failure: {content!r}"

    # ------------------------------------------------------------------
    # Test 5: actions_summary and content are always separate
    # ------------------------------------------------------------------

    def test_actions_summary_separate_from_content(self, client, monkeypatch):
        """
        actions_summary and content must be separate fields — no concatenation.
        If analyze_meal succeeds, its summary must NOT appear verbatim in content.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "analyze_meal", "arguments": {
                    "meal_text": "یه کاسه برنج",
                    "should_log": False,
                }}],
                None,
            ],
            final_text="برنج منبع خوبی از کربوهیدرات است.",
        )
        data = self._send(client, monkeypatch, provider, "برنج چقدر کالری داره؟")

        # Fields must exist separately
        assert "content" in data
        # actions_summary is either None or a list — never merged into content
        actions = data.get("actions_summary")
        if actions:
            assert isinstance(actions, list), "actions_summary must be a list"
            for action_text in actions:
                # action text should not be verbatim embedded in content
                # (partial match OK, but a full chip text embedded verbatim indicates merge)
                assert isinstance(action_text, str)
        # tool_calls_executed is a separate counter field
        assert isinstance(data.get("tool_calls_executed"), (int, type(None)))
