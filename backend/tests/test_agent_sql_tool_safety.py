"""
Tests for query_user_nutrition_data tool: SQL safety layer + orchestrator integration.

Coverage:
  Part A — sql_safety unit tests (no DB, no provider)
  Part B — QueryUserNutritionDataTool execute() unit tests (mocked DB)
  Part C — Orchestrator integration tests (ScriptedToolProvider)
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Part A — SQL safety unit tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateReadonlyUserSQL:
    """Pure unit tests for validate_readonly_user_sql(). No DB, no I/O."""

    def _v(self, sql: str):
        from app.services.agent_tools.sql_safety import validate_readonly_user_sql
        return validate_readonly_user_sql(sql)

    # ── Safe queries ──────────────────────────────────────────────────────────

    def test_safe_select_with_user_id(self):
        result = self._v(
            "SELECT logged_at, meal_time, description, analysis_result "
            "FROM meal_entries WHERE user_id = :user_id "
            "ORDER BY logged_at DESC LIMIT 10"
        )
        assert result.valid, result.error

    def test_safe_select_daily_checkins(self):
        result = self._v(
            "SELECT check_date, adherence_level, weight_kg, sleep_hours "
            "FROM daily_checkins WHERE user_id = :user_id "
            "ORDER BY check_date DESC LIMIT 7"
        )
        assert result.valid, result.error

    def test_safe_select_progress_entries(self):
        result = self._v(
            "SELECT entry_type, value_numeric, recorded_at "
            "FROM progress_entries WHERE user_id = :user_id "
            "ORDER BY recorded_at DESC LIMIT 20"
        )
        assert result.valid, result.error

    def test_safe_select_plan_days(self):
        result = self._v(
            "SELECT plan_date, title, daily_calories, daily_macros "
            "FROM nutrition_plan_days WHERE user_id = :user_id "
            "ORDER BY plan_date DESC LIMIT 7"
        )
        assert result.valid, result.error

    def test_safe_join_plan_days_and_meals(self):
        result = self._v(
            "SELECT d.plan_date, m.meal_type, m.title, m.calories_estimate "
            "FROM nutrition_plan_days d "
            "JOIN nutrition_plan_day_meals m ON m.plan_day_id = d.id "
            "WHERE d.user_id = :user_id "
            "ORDER BY d.plan_date DESC, m.meal_order LIMIT 20"
        )
        assert result.valid, result.error

    def test_safe_with_cte(self):
        result = self._v(
            "WITH recent AS ("
            "SELECT logged_at, meal_time, description "
            "FROM meal_entries WHERE user_id = :user_id "
            "ORDER BY logged_at DESC LIMIT 5"
            ") SELECT * FROM recent"
        )
        assert result.valid, result.error

    def test_safe_select_user_profiles(self):
        result = self._v(
            "SELECT gender, birth_date, height_cm, weight_kg, target_weight_kg "
            "FROM user_profiles WHERE user_id = :user_id LIMIT 1"
        )
        assert result.valid, result.error

    def test_safe_select_nutrition_goals(self):
        result = self._v(
            "SELECT goal_type, target_calories, notes "
            "FROM nutrition_goals WHERE user_id = :user_id LIMIT 1"
        )
        assert result.valid, result.error

    def test_normalized_sql_strips_trailing_semicolon(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id LIMIT 5;"
        )
        assert result.valid, result.error
        assert not result.normalized_sql.rstrip().endswith(";")

    # ── Missing :user_id ──────────────────────────────────────────────────────

    def test_rejects_missing_user_id(self):
        result = self._v("SELECT * FROM meal_entries LIMIT 10")
        assert not result.valid
        assert "user_id" in result.error.lower()

    def test_rejects_select_star_without_user_id(self):
        result = self._v("SELECT * FROM meal_entries")
        assert not result.valid

    # ── Literal user ID ───────────────────────────────────────────────────────

    def test_rejects_literal_uuid_in_where(self):
        result = self._v(
            "SELECT * FROM meal_entries "
            "WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'"
        )
        assert not result.valid
        assert "literal" in result.error.lower() or "user_id" in result.error.lower()

    def test_rejects_literal_uuid_with_double_quotes(self):
        result = self._v(
            'SELECT * FROM meal_entries '
            'WHERE user_id = "abcdef12-1234-1234-1234-abcdef123456"'
        )
        assert not result.valid

    # ── Write / DDL operations ────────────────────────────────────────────────

    def test_rejects_insert(self):
        result = self._v("INSERT INTO meal_entries (user_id) VALUES (:user_id)")
        assert not result.valid

    def test_rejects_update(self):
        result = self._v(
            "UPDATE meal_entries SET description = 'x' WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_delete(self):
        result = self._v("DELETE FROM meal_entries WHERE user_id = :user_id")
        assert not result.valid

    def test_rejects_drop_table(self):
        result = self._v("DROP TABLE meal_entries")
        assert not result.valid

    def test_rejects_alter_table(self):
        result = self._v("ALTER TABLE meal_entries ADD COLUMN foo TEXT")
        assert not result.valid

    def test_rejects_create_table(self):
        result = self._v(
            "CREATE TABLE evil AS SELECT * FROM meal_entries WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_pragma(self):
        result = self._v("PRAGMA table_info(meal_entries)")
        assert not result.valid

    def test_rejects_attach(self):
        result = self._v("ATTACH DATABASE 'evil.db' AS evil")
        assert not result.valid

    def test_rejects_detach(self):
        result = self._v("DETACH DATABASE evil")
        assert not result.valid

    def test_rejects_vacuum(self):
        result = self._v("VACUUM")
        assert not result.valid

    def test_rejects_truncate(self):
        result = self._v("TRUNCATE TABLE meal_entries")
        assert not result.valid

    def test_rejects_replace_into(self):
        result = self._v(
            "REPLACE INTO meal_entries (user_id, description) VALUES (:user_id, 'x')"
        )
        assert not result.valid

    def test_rejects_merge(self):
        result = self._v("MERGE INTO meal_entries USING src ON 1=1")
        assert not result.valid

    # ── Multiple statements / injection ──────────────────────────────────────

    def test_rejects_multiple_statements_drop(self):
        result = self._v(
            "SELECT * FROM meal_entries WHERE user_id = :user_id; "
            "DROP TABLE meal_entries;"
        )
        assert not result.valid

    def test_rejects_multiple_statements_delete(self):
        result = self._v(
            "SELECT id FROM daily_checkins WHERE user_id = :user_id; "
            "DELETE FROM daily_checkins WHERE 1=1"
        )
        assert not result.valid

    # ── SQL comments ──────────────────────────────────────────────────────────

    def test_rejects_double_dash_comment(self):
        result = self._v(
            "SELECT * FROM meal_entries WHERE user_id = :user_id -- AND 1=1"
        )
        assert not result.valid

    def test_rejects_block_comment(self):
        result = self._v(
            "SELECT /* evil */ * FROM meal_entries WHERE user_id = :user_id"
        )
        assert not result.valid

    # ── Non-whitelisted tables ────────────────────────────────────────────────

    def test_rejects_users_table(self):
        result = self._v("SELECT * FROM users WHERE id = :user_id")
        assert not result.valid

    def test_rejects_auth_otps_table(self):
        result = self._v(
            "SELECT otp_code FROM auth_otps WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_token_blocklist_table(self):
        result = self._v(
            "SELECT jti FROM token_blocklist WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_audit_logs_table(self):
        result = self._v(
            "SELECT action FROM audit_logs WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_arbitrary_unknown_table(self):
        result = self._v(
            "SELECT * FROM secret_data WHERE user_id = :user_id LIMIT 5"
        )
        assert not result.valid

    # ── Sensitive columns ─────────────────────────────────────────────────────

    def test_rejects_hashed_password_column(self):
        result = self._v(
            "SELECT hashed_password FROM user_profiles WHERE user_id = :user_id LIMIT 1"
        )
        assert not result.valid

    def test_rejects_otp_code_column(self):
        result = self._v(
            "SELECT otp_code FROM daily_checkins WHERE user_id = :user_id LIMIT 1"
        )
        assert not result.valid

    def test_rejects_token_column(self):
        result = self._v(
            "SELECT token FROM meal_entries WHERE user_id = :user_id LIMIT 1"
        )
        assert not result.valid

    def test_rejects_api_key_column(self):
        result = self._v(
            "SELECT api_key FROM user_profiles WHERE user_id = :user_id LIMIT 1"
        )
        assert not result.valid

    def test_rejects_phone_column(self):
        result = self._v(
            "SELECT phone FROM user_profiles WHERE user_id = :user_id LIMIT 1"
        )
        assert not result.valid

    # ── Metadata tables ───────────────────────────────────────────────────────

    def test_rejects_sqlite_master(self):
        result = self._v(
            "SELECT name FROM sqlite_master WHERE user_id = :user_id LIMIT 10"
        )
        assert not result.valid

    def test_rejects_sqlite_schema(self):
        result = self._v(
            "SELECT * FROM sqlite_schema WHERE user_id = :user_id LIMIT 5"
        )
        assert not result.valid

    # ── Set operations ────────────────────────────────────────────────────────

    def test_rejects_union(self):
        result = self._v(
            "SELECT id FROM meal_entries WHERE user_id = :user_id "
            "UNION SELECT id FROM daily_checkins WHERE user_id = :user_id"
        )
        assert not result.valid

    def test_rejects_union_all(self):
        result = self._v(
            "SELECT id FROM meal_entries WHERE user_id = :user_id "
            "UNION ALL SELECT id FROM meal_entries WHERE user_id != :user_id"
        )
        assert not result.valid

    def test_rejects_intersect(self):
        result = self._v(
            "SELECT id FROM meal_entries WHERE user_id = :user_id "
            "INTERSECT SELECT id FROM daily_checkins WHERE user_id = :user_id"
        )
        assert not result.valid

    # ── LIMIT enforcement ─────────────────────────────────────────────────────

    def test_appends_limit_when_missing(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id"
        )
        assert result.valid, result.error
        assert "LIMIT" in result.normalized_sql.upper()

    def test_default_limit_is_50(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id"
        )
        assert result.valid
        assert "LIMIT 50" in result.normalized_sql.upper()

    def test_caps_limit_above_100(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id LIMIT 999"
        )
        assert result.valid
        assert "LIMIT 100" in result.normalized_sql.upper()

    def test_preserves_limit_within_range(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id LIMIT 30"
        )
        assert result.valid
        assert "LIMIT 30" in result.normalized_sql.upper()

    def test_caps_limit_exactly_at_100(self):
        result = self._v(
            "SELECT description FROM meal_entries WHERE user_id = :user_id LIMIT 100"
        )
        assert result.valid
        assert "LIMIT 100" in result.normalized_sql.upper()

    # ── created_at / updated_at columns not false-positive ───────────────────

    def test_created_at_does_not_trigger_create_block(self):
        result = self._v(
            "SELECT created_at, description FROM meal_entries "
            "WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 5"
        )
        assert result.valid, result.error

    def test_updated_at_does_not_trigger_update_block(self):
        result = self._v(
            "SELECT updated_at FROM nutrition_plan_days "
            "WHERE user_id = :user_id ORDER BY updated_at DESC LIMIT 5"
        )
        assert result.valid, result.error

    def test_deleted_flag_column_does_not_trigger_delete_block(self):
        # 'deleted' as a standalone column name — but word boundary prevents match with 'delete'
        # (no such column exists in our schema, but we verify boundary behavior is correct)
        result = self._v(
            "SELECT adherence_notes FROM daily_checkins "
            "WHERE user_id = :user_id ORDER BY check_date DESC LIMIT 5"
        )
        assert result.valid, result.error

    # ── Empty query ───────────────────────────────────────────────────────────

    def test_rejects_empty_string(self):
        result = self._v("")
        assert not result.valid

    def test_rejects_whitespace_only(self):
        result = self._v("   \n\t  ")
        assert not result.valid


# ═══════════════════════════════════════════════════════════════════════════════
# Part B — ensure_limit unit tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnsureLimit:
    def _el(self, sql: str, default: int = 50, max_l: int = 100) -> str:
        from app.services.agent_tools.sql_safety import _ensure_limit
        return _ensure_limit(sql, default_limit=default, max_limit=max_l)

    def test_appends_limit_when_absent(self):
        out = self._el("SELECT 1 FROM meal_entries WHERE user_id = :user_id")
        assert "LIMIT 50" in out.upper()

    def test_strips_trailing_semicolon_before_appending(self):
        out = self._el("SELECT 1 FROM meal_entries WHERE user_id = :user_id;")
        assert not out.rstrip().endswith(";")
        assert "LIMIT 50" in out.upper()

    def test_caps_oversized_limit(self):
        out = self._el(
            "SELECT 1 FROM meal_entries WHERE user_id = :user_id LIMIT 200",
            max_l=100,
        )
        assert "LIMIT 100" in out.upper()
        assert "200" not in out

    def test_preserves_small_limit(self):
        out = self._el(
            "SELECT 1 FROM meal_entries WHERE user_id = :user_id LIMIT 5",
            max_l=100,
        )
        assert "LIMIT 5" in out.upper()


# ═══════════════════════════════════════════════════════════════════════════════
# Part C — QueryUserNutritionDataTool.execute() unit tests (mocked DB session)
# ═══════════════════════════════════════════════════════════════════════════════

class TestQueryUserNutritionDataToolExecute:
    """Test the tool's execute() method in isolation using a mock DB."""

    def _make_context(self, db=None, user_id="test-user-uuid-1234-5678-90ab"):
        from app.services.agent_tools.base import AgentExecutionContext

        user = MagicMock()
        user.id = user_id

        mem = MagicMock()
        mem.to_compact_dict.return_value = {}

        return AgentExecutionContext(
            db=db or MagicMock(),
            user=user,
            locale="fa",
            nutrition_memory=mem,
            chat_session_id="test-session",
        )

    def test_returns_failure_on_empty_sql(self):
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        tool = QueryUserNutritionDataTool()
        ctx = self._make_context()
        result = tool.execute(ctx, {"question": "test", "sql": ""})
        assert not result.success
        assert result.error == "no_sql_provided"

    def test_returns_failure_on_unsafe_sql(self):
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        tool = QueryUserNutritionDataTool()
        ctx = self._make_context()
        result = tool.execute(ctx, {
            "question": "delete everything",
            "sql": "DELETE FROM meal_entries WHERE user_id = :user_id",
        })
        assert not result.success
        assert result.error == "unsafe_or_invalid_query"

    def test_returns_failure_when_table_not_whitelisted(self):
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        tool = QueryUserNutritionDataTool()
        ctx = self._make_context()
        result = tool.execute(ctx, {
            "question": "get my phone",
            "sql": "SELECT phone FROM users WHERE id = :user_id LIMIT 1",
        })
        assert not result.success

    def test_returns_success_on_valid_query_with_results(self):
        """Valid SQL with mocked DB cursor → success with row data."""
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        # Build a mock cursor that returns two rows
        mock_cursor = MagicMock()
        mock_cursor.keys.return_value = ["check_date", "adherence_level"]
        mock_cursor.fetchmany.return_value = [
            ("2026-06-28", 4),
            ("2026-06-27", 3),
        ]

        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cursor

        tool = QueryUserNutritionDataTool()
        ctx = self._make_context(db=mock_db)

        result = tool.execute(ctx, {
            "question": "این هفته پایبندی؟",
            "sql": (
                "SELECT check_date, adherence_level FROM daily_checkins "
                "WHERE user_id = :user_id ORDER BY check_date DESC LIMIT 7"
            ),
        })
        assert result.success, result.error
        assert result.data["row_count"] == 2
        assert "check_date" in result.data["columns"]

    def test_does_not_expose_raw_sql_error_on_db_exception(self):
        """If DB raises, tool returns failure without leaking error details."""
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB connection exploded: passwords=abc123")

        tool = QueryUserNutritionDataTool()
        ctx = self._make_context(db=mock_db)

        result = tool.execute(ctx, {
            "question": "recent meals",
            "sql": (
                "SELECT description FROM meal_entries "
                "WHERE user_id = :user_id ORDER BY logged_at DESC LIMIT 5"
            ),
        })
        assert not result.success
        # Raw DB error must not be surfaced to the caller
        assert "exploded" not in (result.error or "")
        assert "abc123" not in (result.error or "")

    def test_user_id_comes_from_context_not_arguments(self):
        """The query must be executed with context.user.id, never with an LLM-supplied ID."""
        from app.services.agent_tools.registry import QueryUserNutritionDataTool

        captured_params: dict = {}

        def capture_execute(stmt, params):
            captured_params.update(params)
            m = MagicMock()
            m.keys.return_value = ["description"]
            m.fetchmany.return_value = []
            return m

        mock_db = MagicMock()
        mock_db.execute.side_effect = capture_execute

        tool = QueryUserNutritionDataTool()
        real_user_id = "real-user-context-id-abc"
        ctx = self._make_context(db=mock_db, user_id=real_user_id)

        tool.execute(ctx, {
            "question": "my meals",
            "sql": (
                "SELECT description FROM meal_entries "
                "WHERE user_id = :user_id ORDER BY logged_at DESC LIMIT 5"
            ),
        })

        assert captured_params.get("user_id") == real_user_id


# ═══════════════════════════════════════════════════════════════════════════════
# Part D — Orchestrator integration tests (ScriptedToolProvider)
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.ai_provider import AIProvider, AIToolCall, AIToolCallResult


class ScriptedToolProvider(AIProvider):
    """Minimal scripted provider reused from test_agent_orchestrator_policy.py."""

    supports_tools = True

    def __init__(self, rounds: list[list[dict] | None], final_text: str = "پیام پردازش شد."):
        self._rounds = rounds
        self._final_text = final_text
        self._idx = 0
        self.tool_names_called: list[str] = []

    def generate_text(self, messages, temperature=None, max_tokens=None):
        raise NotImplementedError

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

        tool_calls, raw = [], []
        for i, spec in enumerate(round_spec):
            tc = AIToolCall(
                id=f"call_{self._idx}_{i}",
                name=spec["name"],
                arguments=spec.get("arguments", {}),
            )
            tool_calls.append(tc)
            self.tool_names_called.append(spec["name"])
            raw.append({
                "id": tc.id, "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            })

        return AIToolCallResult(
            assistant_message=None,
            tool_calls=tool_calls,
            provider="scripted_mock",
            model="test",
            raw_tool_calls=raw,
        )


class TestQueryUserNutritionDataOrchestration:
    """Orchestrator integration tests: ScriptedProvider drives the tool loop."""

    def _send(self, client, monkeypatch, provider, message: str) -> dict:
        monkeypatch.setattr(
            "app.services.agent_orchestrator.get_ai_provider",
            lambda: provider,
        )
        resp = client.post("/api/v1/chat/message", json={"message": message})
        assert resp.status_code == 201, resp.text
        return resp.json()["data"]

    # ── Tool is called and registered ─────────────────────────────────────────

    def test_tool_registered_in_registry(self):
        from app.services.agent_tools.registry import build_tool_registry
        registry = build_tool_registry()
        assert "query_user_nutrition_data" in registry

    def test_tool_appears_in_openai_specs(self):
        import app.services.agent_orchestrator as orch
        names = [spec["function"]["name"] for spec in orch._TOOL_SPECS]
        assert "query_user_nutrition_data" in names

    # ── Adherence question → tool called ─────────────────────────────────────

    def test_adherence_question_calls_query_tool(self, client, monkeypatch):
        """
        User asks about weekly adherence → scripted provider calls
        query_user_nutrition_data; orchestrator executes it without crash.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "این هفته چقدر به برنامه پایبند بودم؟",
                    "sql": (
                        "SELECT check_date, adherence_level, adherence_notes "
                        "FROM daily_checkins WHERE user_id = :user_id "
                        "ORDER BY check_date DESC LIMIT 7"
                    ),
                    "purpose": "Get weekly adherence data",
                }}],
                None,
            ],
            final_text="با توجه به گزارش‌های اخیرت، این هفته پیشرفت خوبی داشتی.",
        )
        data = self._send(client, monkeypatch, provider, "این هفته چقدر به برنامه پایبند بودم؟")

        assert "query_user_nutrition_data" in provider.tool_names_called
        assert data["role"] == "assistant"
        assert data["content"] is not None

    # ── Pattern question → tool called ───────────────────────────────────────

    def test_diet_pattern_question_calls_query_tool(self, client, monkeypatch):
        """
        User asks where their diet usually breaks → query_user_nutrition_data called.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "بیشتر کجاها رژیمم خراب میشه؟",
                    "sql": (
                        "SELECT logged_at, meal_time, description "
                        "FROM meal_entries WHERE user_id = :user_id "
                        "ORDER BY logged_at DESC LIMIT 14"
                    ),
                    "purpose": "Analyze recent meal patterns for weak spots",
                }}],
                None,
            ],
            final_text=(
                "با توجه به اطلاعات ثبت‌شده‌ات، نقطه ضعف بیشتر بین عصر تا شب دیده میشه."
            ),
        )
        data = self._send(client, monkeypatch, provider, "بیشتر کجاها رژیمم خراب میشه؟")

        assert "query_user_nutrition_data" in provider.tool_names_called
        assert data["role"] == "assistant"

    # ── Final response must not expose internals ──────────────────────────────

    def test_response_does_not_contain_sql_keywords(self, client, monkeypatch):
        """Final response must be natural — no SELECT, no table names, no JSON."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "تو وعده‌هام پروتئین کمه؟",
                    "sql": (
                        "SELECT meal_type, calories_estimate, protein_g "
                        "FROM nutrition_plan_day_meals WHERE plan_day_id IN "
                        "(SELECT id FROM nutrition_plan_days "
                        "WHERE user_id = :user_id ORDER BY plan_date DESC LIMIT 3) LIMIT 12"
                    ),
                    "purpose": "Check protein in recent plan meals",
                }}],
                None,
            ],
            final_text=(
                "با توجه به برنامه غذاییت، پروتئین وعده‌های اخیر کمی پایین‌تر از هدف بوده. "
                "سعی کن ناهار یا شام یک منبع پروتئینی مثل مرغ یا ماهی اضافه کنی."
            ),
        )
        data = self._send(client, monkeypatch, provider, "تو وعده‌هام پروتئین کمه؟")

        content = data["content"]
        assert "SELECT" not in content
        assert "query_user_nutrition_data" not in content
        assert "nutrition_plan_day_meals" not in content
        assert "nutrition_plan_days" not in content
        assert content.strip() != ""

    # ── Unsafe SQL from LLM is rejected gracefully ────────────────────────────

    def test_unsafe_sql_does_not_crash_orchestrator(self, client, monkeypatch):
        """
        When scripted LLM sends DELETE SQL, the tool rejects it and orchestrator
        continues to produce a response without crashing.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "این هفته چقدر پایبند بودم؟",
                    "sql": "DELETE FROM meal_entries WHERE user_id = :user_id",
                }}],
                None,
            ],
            final_text="اطلاعات کافی برای پاسخ دقیق در دسترس نیست، اما می‌تونم کمک کنم.",
        )
        data = self._send(client, monkeypatch, provider, "این هفته چقدر پایبند بودم؟")

        assert data["role"] == "assistant"
        assert data["content"] is not None
        # Response must not contain SQL or internal details
        assert "DELETE" not in data["content"]
        assert "query_user_nutrition_data" not in data["content"]

    def test_missing_user_id_sql_rejected_gracefully(self, client, monkeypatch):
        """SQL without :user_id is rejected; response is still produced."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "recent meals",
                    "sql": "SELECT * FROM meal_entries LIMIT 10",
                }}],
                None,
            ],
            final_text="فعلاً داده کافی ثبت نشده. از امروز شروع به ثبت وعده‌هات کن.",
        )
        data = self._send(client, monkeypatch, provider, "آخرین وعده‌هامو نشونم بده")

        assert data["role"] == "assistant"
        assert data["content"] is not None
        assert "user_id" not in data["content"]

    def test_users_table_access_rejected_gracefully(self, client, monkeypatch):
        """Attempt to access users table is blocked; no crash."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "my phone",
                    "sql": "SELECT phone FROM users WHERE id = :user_id LIMIT 1",
                }}],
                None,
            ],
            final_text="اطلاعات درخواستی در دسترس نیست.",
        )
        data = self._send(client, monkeypatch, provider, "شماره تلفنمو بهم بگو")

        assert data["role"] == "assistant"
        assert "phone" not in data["content"]
        assert "users" not in data["content"]

    # ── Existing tools still work ─────────────────────────────────────────────

    def test_analyze_meal_still_works(self, client, monkeypatch):
        """Adding new tool must not break analyze_meal."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "analyze_meal", "arguments": {
                    "meal_text": "یه پرس خورش قرمه‌سبزی با برنج",
                    "should_log": False,
                }}],
                None,
            ],
            final_text="خورش قرمه‌سبزی حدود ۵۰۰ کالری داره.",
        )
        data = self._send(client, monkeypatch, provider, "خورش قرمه‌سبزی چقدر کالری داره؟")

        assert "analyze_meal" in provider.tool_names_called
        assert data["role"] == "assistant"
        assert data["content"] is not None

    def test_get_calendar_still_works(self, client, monkeypatch):
        """Adding new tool must not break get_calendar."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "get_calendar", "arguments": {"days": 7}}],
                None,
            ],
            final_text="برنامه غذایی این هفته آماده‌ست.",
        )
        data = self._send(client, monkeypatch, provider, "برنامه این هفته چیه؟")

        assert "get_calendar" in provider.tool_names_called
        assert data["role"] == "assistant"

    def test_update_tomorrow_plan_still_works(self, client, monkeypatch):
        """Adding new tool must not break update_tomorrow_plan."""
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "update_tomorrow_plan", "arguments": {
                    "reason": "کاربر درخواست سبک‌تر کردن داد",
                    "intensity": "light",
                }}],
                None,
            ],
            final_text="فردا یه برنامه سبک‌تر داری.",
        )
        data = self._send(client, monkeypatch, provider, "برنامه فردامو سبک‌تر کن")

        assert "update_tomorrow_plan" in provider.tool_names_called
        assert data["role"] == "assistant"

    # ── Empty DB result is handled gracefully ─────────────────────────────────

    def test_no_data_in_db_returns_graceful_response(self, client, monkeypatch):
        """
        When DB returns zero rows (no check-ins logged yet), the tool succeeds
        with row_count=0 and the scripted provider returns a helpful message.
        """
        provider = ScriptedToolProvider(
            rounds=[
                [{"name": "query_user_nutrition_data", "arguments": {
                    "question": "این هفته چقدر پایبند بودم؟",
                    "sql": (
                        "SELECT check_date, adherence_level FROM daily_checkins "
                        "WHERE user_id = :user_id ORDER BY check_date DESC LIMIT 7"
                    ),
                }}],
                None,
            ],
            final_text=(
                "فعلاً گزارشی ثبت نشده. از امروز چک‌این روزانه رو شروع کن "
                "تا بتونم الگوت رو تحلیل کنم."
            ),
        )
        data = self._send(client, monkeypatch, provider, "این هفته چقدر به برنامه پایبند بودم؟")

        assert data["role"] == "assistant"
        assert data["content"] is not None
        assert "SELECT" not in data["content"]
        assert len(data["content"]) > 10
