"""Agent tool implementations — all 10 nutrition agent tools."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.services.agent_tools.base import AgentExecutionContext, AgentTool, AgentToolResult

logger = logging.getLogger(__name__)


# ─── 1. AnalyzeMealTool ──────────────────────────────────────────────────────

class AnalyzeMealTool(AgentTool):
    name = "analyze_meal"
    description = (
        "Analyze a food or meal for nutrition info. CALL THIS for every calorie question and every food event.\n"
        "should_log=false: user is asking about a food hypothetically (calorie lookup, nutrition question)\n"
        "should_log=true: user actually ate/drank something and is reporting it (log the event)\n"
        "Examples: 'لوبیا پلو چقدر کالری داره' → should_log=false; "
        "'امشب نون خامه‌ای خوردم' → should_log=true"
    )
    input_schema = {
        "type": "object",
        "properties": {
            "meal_text": {"type": "string", "description": "The food or meal description"},
            "meal_time": {
                "type": "string",
                "enum": ["breakfast", "lunch", "dinner", "snack", "unknown"],
                "default": "unknown",
            },
            "context": {"type": "string", "description": "Additional context about the meal"},
            "should_log": {
                "type": "boolean",
                "default": True,
                "description": "Whether to log this meal entry to the database",
            },
        },
        "required": ["meal_text"],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services.nutrition_agent_service import NutritionAgentService
        from app.repositories import nutrition_repository

        meal_text: str = arguments.get("meal_text", "")
        meal_time: str = arguments.get("meal_time", "unknown")
        meal_context: str | None = arguments.get("context")
        should_log: bool = arguments.get("should_log", True)

        agent = NutritionAgentService()
        try:
            parsed, _ = agent.analyze_meal(context.nutrition_memory, meal_text, meal_time, meal_context)
        except Exception as exc:
            logger.warning("analyze_meal AI call failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="تحلیل وعده غذایی ناموفق بود.",
                error=str(exc),
            )

        if should_log:
            try:
                nutrition_repository.create_meal_entry(
                    context.db,
                    context.user.id,
                    meal_time=meal_time if meal_time != "unknown" else None,
                    description=meal_text,
                    analysis_result=parsed,
                    logged_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            except Exception as exc:
                logger.warning("Failed to log meal entry: %s", exc)

        summary = parsed.get("analysis_summary") or f"تحلیل {meal_text} انجام شد."
        return AgentToolResult(
            tool_name=self.name, success=True,
            user_visible_summary=summary,
            data=parsed,
        )


# ─── 2. WhatToEatNowTool ─────────────────────────────────────────────────────

class WhatToEatNowTool(AgentTool):
    name = "what_to_eat_now"
    description = (
        "Suggest food options based on available ingredients and hunger level. "
        "Use when user asks what to eat or needs meal suggestions."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "available_foods": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of available ingredients or foods",
            },
            "hunger_level": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "default": "medium",
            },
            "meal_context": {"type": "string", "description": "Additional context"},
            "time_available_minutes": {
                "type": "integer",
                "description": "Minutes available for preparation",
            },
        },
        "required": [],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services.nutrition_agent_service import NutritionAgentService

        available_foods: list[str] = arguments.get("available_foods") or []
        hunger_level: str = arguments.get("hunger_level", "medium")
        meal_context: str | None = arguments.get("meal_context")
        time_available: int | None = arguments.get("time_available_minutes")

        agent = NutritionAgentService()
        try:
            parsed, _ = agent.what_to_eat_now(
                context.nutrition_memory, available_foods, hunger_level, meal_context, time_available
            )
        except Exception as exc:
            logger.warning("what_to_eat_now AI call failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="پیشنهاد غذایی ناموفق بود.",
                error=str(exc),
            )

        summary = parsed.get("reasoning_summary") or "گزینه‌های غذایی پیشنهاد شد."
        return AgentToolResult(
            tool_name=self.name, success=True,
            user_visible_summary=summary,
            data=parsed,
        )


# ─── 3. GenerateWeekPlanTool ─────────────────────────────────────────────────

class GenerateWeekPlanTool(AgentTool):
    name = "generate_week_plan"
    description = (
        "Generate a 7-day meal plan. Call ONLY when user EXPLICITLY asks for a new week plan or future days.\n"
        "Explicit triggers: 'برنامه هفته بعد رو بساز', 'یه برنامه ۷ روزه بده', "
        "'build a week plan', 'create a meal plan'\n"
        "Skips days that already have a plan (safe append). "
        "force=true overwrites existing plan days — REQUIRES explicit user confirmation via the UI; "
        "do NOT call with force=true from chat."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "force": {
                "type": "boolean",
                "default": False,
                "description": (
                    "Overwrite existing plan days. REQUIRES user confirmation — "
                    "never set true unless user explicitly confirmed replacement."
                ),
            },
        },
        "required": [],
    }

    def needs_confirmation(self, arguments: dict[str, Any]) -> bool:
        return bool(arguments.get("force"))

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services import calendar_service

        force: bool = arguments.get("force", False)

        # Defense-in-depth: should never reach here with force=True because the orchestrator
        # intercepts needs_confirmation=True before calling execute(). Reject anyway.
        if force:
            return AgentToolResult(
                tool_name=self.name,
                success=False,
                user_visible_summary=(
                    "بازنویسی برنامه موجود نیاز به تأیید کاربر دارد. "
                    "از دکمه مربوطه در رابط کاربری استفاده کنید."
                ),
                error="confirmation_required",
            )

        try:
            result = calendar_service.generate_week(
                context.db, context.user, context.locale, start_date=None, force=False
            )
            summary = f"برنامه {result.generated_days} روز آینده ساخته شد."
            if result.skipped_days:
                summary += f" ({result.skipped_days} روز قبلاً برنامه داشت و نادیده گرفته شد.)"
            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary=summary,
                data={"generated_days": result.generated_days, "skipped_days": result.skipped_days},
            )
        except Exception as exc:
            logger.warning("generate_week_plan failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="ساخت برنامه هفتگی ناموفق بود.",
                error=str(exc),
            )


# ─── 4. GetCalendarTool ──────────────────────────────────────────────────────

class GetCalendarTool(AgentTool):
    name = "get_calendar"
    description = (
        "Get the user's meal plan calendar. Use when:\n"
        "  - User reports a food event (compare against today's planned meals)\n"
        "  - User asks about their plan for today/tomorrow/this week\n"
        "  - Before calling update_tomorrow_plan\n"
        "  - User asks what to eat according to their schedule"
    )
    input_schema = {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "default": 7,
                "description": "Number of days to retrieve",
            },
        },
        "required": [],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services import calendar_service

        days: int = arguments.get("days", 7)
        try:
            result = calendar_service.get_calendar(
                context.db, context.user, context.locale,
                start_date=date.today(), days=days,
            )
            planned = result.coverage.planned_days_count
            summary = f"برنامه {planned} روز از {days} روز آینده برنامه‌ریزی شده."

            # Build concise day list (limit to 7)
            day_list = []
            for d in result.days[:7]:
                meal_titles = [m.title for m in d.meals[:4]]
                day_list.append({
                    "date": d.plan_date,
                    "title": d.title,
                    "meals": meal_titles,
                })

            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary=summary,
                data={
                    "planned_days": planned,
                    "total_days": days,
                    "days": day_list,
                },
            )
        except Exception as exc:
            logger.warning("get_calendar failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="دریافت برنامه غذایی ناموفق بود.",
                error=str(exc),
            )


# ─── 5. UpdateTomorrowPlanTool ───────────────────────────────────────────────

class UpdateTomorrowPlanTool(AgentTool):
    name = "update_tomorrow_plan"
    description = (
        "Regenerate tomorrow's meal plan. Call ONLY when user EXPLICITLY asks to adjust, lighten, "
        "or compensate tomorrow's plan.\n"
        "Explicit triggers: 'برنامه فردامو سبک‌تر کن', 'make tomorrow lighter', "
        "'فردامو تنظیم کن', 'برنامه فردا رو عوض کن'\n"
        "NEVER call this just because user ate something — only when they explicitly request it.\n"
        "NEVER recommend starvation. Minimum 1500 kcal. "
        "intensity='light' = smaller portions + more vegetables/fiber, NOT starvation."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "Reason for updating tomorrow's plan"},
            "user_event": {"type": "string", "description": "What the user did (e.g. ate a lot, had a party)"},
            "intensity": {
                "type": "string",
                "enum": ["light", "normal", "conservative"],
                "default": "light",
            },
        },
        "required": ["reason"],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services import calendar_service

        reason: str = arguments.get("reason", "")
        user_event: str | None = arguments.get("user_event")
        intensity: str = arguments.get("intensity", "light")

        extra_parts = [reason]
        if user_event:
            extra_parts.append(f"رویداد کاربر: {user_event}")
        extra_parts.append(
            "Generate balanced, nourishing plan. If lighter, focus on fiber, vegetables, "
            "lean protein, hydration. NEVER restrict to starvation. Minimum 1500 kcal."
        )
        if intensity == "light":
            extra_parts.append("Make the plan lighter with smaller portions and more vegetables.")
        extra_context = " | ".join(extra_parts)

        try:
            tomorrow = date.today() + timedelta(days=1)
            calendar_service.regenerate_day(
                context.db, context.user, context.locale, tomorrow, reason=extra_context
            )
            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary="برنامه فردا به‌روزرسانی شد.",
                data={"plan_date": tomorrow.isoformat(), "intensity": intensity},
            )
        except Exception as exc:
            logger.warning("update_tomorrow_plan failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="به‌روزرسانی برنامه فردا ناموفق بود.",
                error=str(exc),
            )


# ─── 6. AdaptPlanTool ────────────────────────────────────────────────────────

class AdaptPlanTool(AgentTool):
    name = "adapt_plan"
    description = (
        "Get AI recommendations for adapting the nutrition plan based on user feedback. "
        "Returns recommendations but does not automatically change the stored plan."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "Why the plan needs adaptation"},
            "recent_hunger": {"type": "integer", "description": "Recent hunger level 1-5"},
            "recent_sleep": {"type": "number", "description": "Recent sleep hours"},
            "recent_stress": {"type": "integer", "description": "Recent stress level 1-5"},
            "notes": {"type": "string", "description": "Additional notes"},
        },
        "required": ["reason"],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services.nutrition_agent_service import NutritionAgentService

        reason: str = arguments.get("reason", "")
        recent_context: dict = {}
        if arguments.get("recent_hunger") is not None:
            recent_context["hunger"] = arguments["recent_hunger"]
        if arguments.get("recent_sleep") is not None:
            recent_context["sleep"] = arguments["recent_sleep"]
        if arguments.get("recent_stress") is not None:
            recent_context["stress"] = arguments["recent_stress"]
        if arguments.get("notes"):
            recent_context["notes"] = arguments["notes"]

        agent = NutritionAgentService()
        try:
            parsed, _ = agent.adapt_plan(context.nutrition_memory, reason, recent_context)
        except Exception as exc:
            logger.warning("adapt_plan AI call failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="تطبیق برنامه ناموفق بود.",
                error=str(exc),
            )

        changes: list[str] = parsed.get("changes") or []
        summary = " | ".join(changes[:2]) if changes else "توصیه‌های تطبیق برنامه آماده شد."
        return AgentToolResult(
            tool_name=self.name, success=True,
            user_visible_summary=summary,
            data=parsed,
        )


# ─── 7. LogCheckInTool ───────────────────────────────────────────────────────

class LogCheckInTool(AgentTool):
    name = "log_check_in"
    description = (
        "Log a daily progress check-in. Use when user mentions their weight, sleep, activity, or daily status."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "weight_kg": {"type": "number", "description": "User weight in kg"},
            "hunger_level": {"type": "integer", "description": "Hunger level 1-5"},
            "sleep_hours": {"type": "number", "description": "Hours of sleep"},
            "stress_level": {"type": "integer", "description": "Stress level 1-5"},
            "activity_minutes": {"type": "integer", "description": "Minutes of activity"},
            "notes": {"type": "string", "description": "Additional notes"},
        },
        "required": [],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services import progress_service
        from app.schemas.progress import CheckInRequest

        try:
            req = CheckInRequest(
                check_date=date.today(),
                weight_kg=arguments.get("weight_kg"),
                hunger_level=arguments.get("hunger_level"),
                sleep_hours=arguments.get("sleep_hours"),
                stress_level=arguments.get("stress_level"),
                activity_minutes=arguments.get("activity_minutes"),
                adherence_notes=arguments.get("notes"),
            )
            result = progress_service.submit_check_in(context.db, context.user, req)

            parts = ["گزارش امروز ثبت شد."]
            if result.weight_kg:
                parts.append(f"وزن: {result.weight_kg} کیلوگرم")
            if result.sleep_hours:
                parts.append(f"خواب: {result.sleep_hours} ساعت")
            if result.activity_minutes:
                parts.append(f"فعالیت: {result.activity_minutes} دقیقه")
            summary = " | ".join(parts)

            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary=summary,
                data={"check_date": result.check_date.isoformat()},
            )
        except Exception as exc:
            logger.warning("log_check_in failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="ثبت گزارش روزانه ناموفق بود.",
                error=str(exc),
            )


# ─── 8. GetProgressSummaryTool ───────────────────────────────────────────────

class GetProgressSummaryTool(AgentTool):
    name = "get_progress_summary"
    description = (
        "Get user's recent progress summary including weight trend and behavior wins. "
        "Use when user asks about their progress or how they've been doing."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "range_days": {
                "type": "integer",
                "default": 7,
                "description": "Number of days to summarize",
            },
        },
        "required": [],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        from app.services import progress_service

        try:
            result = progress_service.get_summary(context.db, context.user)
            if not result.has_data:
                return AgentToolResult(
                    tool_name=self.name, success=True,
                    user_visible_summary="هنوز هیچ گزارشی ثبت نشده است.",
                    data={"has_data": False},
                )

            parts = [f"رشته ثبت: {result.logging_streak} روز"]
            if result.weight_trend:
                delta = result.weight_trend.delta
                trend_text = "کاهش" if delta < 0 else ("افزایش" if delta > 0 else "ثابت")
                parts.append(f"وزن: {trend_text} {abs(delta):.1f} کیلوگرم")

            achieved_wins = [w.key for w in (result.behavior_wins or []) if w.achieved]
            if achieved_wins:
                parts.append(f"دستاوردها: {', '.join(achieved_wins[:3])}")

            summary = " | ".join(parts)
            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary=summary,
                data={
                    "has_data": True,
                    "logging_streak": result.logging_streak,
                    "latest_weight_kg": result.latest_weight_kg,
                    "weight_trend": {
                        "delta": result.weight_trend.delta,
                        "first": result.weight_trend.first,
                        "last": result.weight_trend.last,
                    } if result.weight_trend else None,
                },
            )
        except Exception as exc:
            logger.warning("get_progress_summary failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="دریافت خلاصه پیشرفت ناموفق بود.",
                error=str(exc),
            )


# ─── 9. ClearChatMemoryTool ──────────────────────────────────────────────────

class ClearChatMemoryTool(AgentTool):
    name = "clear_chat_memory"
    description = (
        "Clear the companion chat memory. Requires user confirmation. "
        "Use when user asks to clear/delete chat history."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "description": "Must be true to confirm clearing",
            },
        },
        "required": ["confirm"],
    }
    requires_confirmation = True

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        return AgentToolResult(
            tool_name=self.name,
            success=False,
            user_visible_summary=(
                "پاک کردن حافظه نیاز به تأیید دارد. "
                "از دکمه پاک کردن در رابط کاربری استفاده کنید."
            ),
            error="confirmation_required",
        )


# ─── 10. GetUserProfileSummaryTool ───────────────────────────────────────────

class GetUserProfileSummaryTool(AgentTool):
    name = "get_user_profile_summary"
    description = (
        "Internal: Get user nutrition profile summary. "
        "Use only when specific user details are needed that aren't available in context."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult:
        try:
            profile = context.nutrition_memory.to_compact_dict()
            return AgentToolResult(
                tool_name=self.name, success=True,
                user_visible_summary="پروفایل کاربر دریافت شد.",
                data=profile,
            )
        except Exception as exc:
            logger.warning("get_user_profile_summary failed: %s", exc)
            return AgentToolResult(
                tool_name=self.name, success=False,
                user_visible_summary="دریافت پروفایل ناموفق بود.",
                error=str(exc),
            )


# ─── Registry factory ─────────────────────────────────────────────────────────

def build_tool_registry() -> dict[str, AgentTool]:
    tools: list[AgentTool] = [
        AnalyzeMealTool(),
        WhatToEatNowTool(),
        GenerateWeekPlanTool(),
        GetCalendarTool(),
        UpdateTomorrowPlanTool(),
        AdaptPlanTool(),
        LogCheckInTool(),
        GetProgressSummaryTool(),
        ClearChatMemoryTool(),
        GetUserProfileSummaryTool(),
    ]
    return {tool.name: tool for tool in tools}
