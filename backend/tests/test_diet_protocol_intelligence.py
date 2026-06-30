"""
Diet protocol intelligence tests.

Covers:
1. GenerateWeekPlanTool.needs_confirmation — replace_confirmed bypasses the gate
2. check_protocol_safety — low-risk users never blocked
3. check_protocol_safety — keto blocked for diabetes
4. check_protocol_safety — fasting blocked for binge history
5. _build_protocol_extra_context("keto") — contains low-carb guidance, not just meat
6. _build_protocol_extra_context("intermittent_fasting") — contains timing/window language
7. AskDietProtocolTool.execute() — returns 2 chips when active plan exists
8. AskDietProtocolTool.execute() — returns 2 chips when no plan exists
"""
from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock


# ─── Minimal NutritionMemoryContext stub ─────────────────────────────────────

@dataclass
class _MemCtx:
    user_id: str = "test-user"
    clinical_review_required: bool = False
    active_medical_flags: list[str] = field(default_factory=list)
    binge_history: bool = False
    current_plan_id: str | None = None
    active_calendar_summary: str | None = None


# ─── 1. replace_confirmed bypasses needs_confirmation gate ───────────────────

class TestGenerateWeekPlanToolConfirmation:
    def _tool(self):
        from app.services.agent_tools.registry import GenerateWeekPlanTool
        return GenerateWeekPlanTool()

    def test_replace_confirmed_bypasses_force_gate(self):
        tool = self._tool()
        assert tool.needs_confirmation({"force": True, "replace_confirmed": True}) is False

    def test_force_without_replace_confirmed_requires_confirmation(self):
        tool = self._tool()
        assert tool.needs_confirmation({"force": True}) is True

    def test_no_force_no_confirmation_needed(self):
        tool = self._tool()
        assert tool.needs_confirmation({}) is False

    def test_replace_confirmed_false_with_force_still_needs_confirmation(self):
        tool = self._tool()
        assert tool.needs_confirmation({"force": True, "replace_confirmed": False}) is True


# ─── 2. Low-risk user — never blocked for any protocol ──────────────────────

class TestProtocolSafetyLowRiskUser:
    PROTOCOLS = [
        "keto", "intermittent_fasting", "low_carb", "high_protein",
        "mediterranean", "vegetarian", "vegan", "calorie_deficit",
        "muscle_gain", "iranian_traditional",
    ]

    def test_low_risk_user_never_blocked(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx()
        for protocol in self.PROTOCOLS:
            result = check_protocol_safety(protocol, ctx)
            assert result.blocked is False, f"Protocol {protocol} should not be blocked for a low-risk user"


# ─── 3. Keto blocked for diabetes ────────────────────────────────────────────

class TestProtocolSafetyKetoDiabetes:
    def test_keto_blocked_for_diabetes(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(active_medical_flags=["diabetes"])
        result = check_protocol_safety("keto", ctx)
        assert result.blocked is True
        assert result.safer_protocol == "low_carb"

    def test_keto_blocked_for_kidney_disease(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(active_medical_flags=["kidney_disease"])
        result = check_protocol_safety("keto", ctx)
        assert result.blocked is True

    def test_keto_blocked_for_pregnancy(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(active_medical_flags=["pregnancy"])
        result = check_protocol_safety("keto", ctx)
        assert result.blocked is True

    def test_keto_not_blocked_for_unrelated_flag(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(active_medical_flags=["hypertension"])
        result = check_protocol_safety("keto", ctx)
        assert result.blocked is False


# ─── 4. Fasting blocked for binge history ────────────────────────────────────

class TestProtocolSafetyFastingBinge:
    def test_fasting_blocked_for_binge_history(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(binge_history=True)
        result = check_protocol_safety("intermittent_fasting", ctx)
        assert result.blocked is True
        assert result.safer_protocol == "calorie_deficit"

    def test_fasting_blocked_for_eating_disorder_flag(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(active_medical_flags=["eating_disorder_history"])
        result = check_protocol_safety("intermittent_fasting", ctx)
        assert result.blocked is True

    def test_fasting_blocked_for_clinical_review(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(clinical_review_required=True)
        result = check_protocol_safety("intermittent_fasting", ctx)
        assert result.blocked is True

    def test_calorie_deficit_blocked_for_binge_history(self):
        from app.services.agent_tools._diet_protocol_safety import check_protocol_safety
        ctx = _MemCtx(binge_history=True)
        result = check_protocol_safety("calorie_deficit", ctx)
        assert result.blocked is True


# ─── 5. Keto instructions: low-carb guidance, not just meat ─────────────────

class TestProtocolExtraContextKeto:
    def test_keto_mentions_net_carbs_limit(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("keto")
        assert text is not None
        lowered = text.lower()
        assert "50g" in text or "50 g" in text or "net carb" in lowered or "carb" in lowered

    def test_keto_mentions_vegetables(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("keto")
        assert text is not None
        assert "vegetable" in text.lower() or "vegetables" in text.lower()

    def test_keto_does_not_say_only_meat(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("keto")
        assert text is not None
        assert "only meat" not in text.lower()
        assert "فقط گوشت" not in text

    def test_keto_mentions_fat_percentage(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("keto")
        assert text is not None
        assert "fat" in text.lower() or "65" in text or "75" in text


# ─── 6. Fasting instructions: timing/window language ────────────────────────

class TestProtocolExtraContextFasting:
    def test_fasting_mentions_eating_window(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("intermittent_fasting")
        assert text is not None
        lowered = text.lower()
        assert "window" in lowered or "timing" in lowered or "16:8" in text

    def test_fasting_is_timing_change_only(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("intermittent_fasting")
        assert text is not None
        lowered = text.lower()
        assert "timing" in lowered or "schedule" in lowered or "only" in lowered

    def test_fasting_does_not_restrict_food_types(self):
        from app.services.agent_tools.registry import _build_protocol_extra_context
        text = _build_protocol_extra_context("intermittent_fasting")
        assert text is not None
        # The instructions should say food types do NOT change
        assert "food type" in text.lower() or "do not" in text.lower() or "not change" in text.lower()


# ─── 7. AskDietProtocolTool: 2 chips when active plan exists ─────────────────

class TestAskDietProtocolToolActivePlan:
    def _run(self, protocol: str, ctx: _MemCtx, locale: str = "fa") -> dict:
        from app.services.agent_tools.registry import AskDietProtocolTool
        from app.services.agent_tools.base import AgentExecutionContext

        exec_ctx = MagicMock(spec=AgentExecutionContext)
        exec_ctx.nutrition_memory = ctx
        exec_ctx.locale = locale

        tool = AskDietProtocolTool()
        result = tool.execute(exec_ctx, {"protocol": protocol, "protocol_label": protocol})
        return result.data or {}

    def test_returns_two_chips_when_active_plan(self):
        ctx = _MemCtx(current_plan_id="plan-abc", active_calendar_summary="Week plan summary...")
        data = self._run("keto", ctx)
        chips = data.get("suggestion_chips", [])
        assert len(chips) == 2, f"Expected 2 chips, got {len(chips)}: {chips}"

    def test_chips_contain_replace_and_continue(self):
        ctx = _MemCtx(current_plan_id="plan-abc", active_calendar_summary="Week plan summary...")
        data = self._run("keto", ctx, locale="fa")
        chips = data.get("suggestion_chips", [])
        # The chips should include Persian replace and continue text
        chips_joined = " ".join(chips)
        assert "جایگزین" in chips_joined or "replace" in chips_joined.lower()
        assert "ادامه" in chips_joined or "continue" in chips_joined.lower()

    def test_has_active_plan_true_in_data(self):
        ctx = _MemCtx(current_plan_id="plan-abc", active_calendar_summary="summary")
        data = self._run("keto", ctx)
        assert data.get("has_active_plan") is True

    def test_safety_not_blocked_for_low_risk(self):
        ctx = _MemCtx(current_plan_id="plan-abc", active_calendar_summary="summary")
        data = self._run("keto", ctx)
        assert data.get("safety_blocked") is False


# ─── 8. AskDietProtocolTool: 2 chips when no plan exists ────────────────────

class TestAskDietProtocolToolNoPlan:
    def _run(self, protocol: str, ctx: _MemCtx, locale: str = "fa") -> dict:
        from app.services.agent_tools.registry import AskDietProtocolTool
        from app.services.agent_tools.base import AgentExecutionContext

        exec_ctx = MagicMock(spec=AgentExecutionContext)
        exec_ctx.nutrition_memory = ctx
        exec_ctx.locale = locale

        tool = AskDietProtocolTool()
        result = tool.execute(exec_ctx, {"protocol": protocol, "protocol_label": "رژیم کتو"})
        return result.data or {}

    def test_returns_two_chips_when_no_plan(self):
        ctx = _MemCtx(current_plan_id=None)
        data = self._run("keto", ctx)
        chips = data.get("suggestion_chips", [])
        assert len(chips) == 2, f"Expected 2 chips, got {len(chips)}: {chips}"

    def test_chips_contain_create_and_later(self):
        ctx = _MemCtx(current_plan_id=None)
        data = self._run("keto", ctx, locale="fa")
        chips = data.get("suggestion_chips", [])
        chips_joined = " ".join(chips)
        assert "بله" in chips_joined or "yes" in chips_joined.lower() or "بساز" in chips_joined
        assert "بعداً" in chips_joined or "later" in chips_joined.lower()

    def test_has_active_plan_false_in_data(self):
        ctx = _MemCtx(current_plan_id=None)
        data = self._run("keto", ctx)
        assert data.get("has_active_plan") is False

    def test_no_chips_when_safety_blocked(self):
        ctx = _MemCtx(current_plan_id=None, active_medical_flags=["diabetes"])
        data = self._run("keto", ctx)
        chips = data.get("suggestion_chips", [])
        assert chips == [], f"Expected no chips for blocked user, got: {chips}"
        assert data.get("safety_blocked") is True
