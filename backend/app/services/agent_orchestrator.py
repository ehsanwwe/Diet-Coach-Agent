"""
AgentOrchestrator: routes companion chat through OpenAI tool calling.

If provider supports tools (OpenAI), runs multi-step tool loop.
Falls back to text-based chat if provider is mock or tool calling fails.
"""
from __future__ import annotations
import json
import logging
import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories import chat_repository
from app.schemas.chat import ChatMessageResponse
from app.services import nutrition_memory_service
from app.services.ai_provider import AIProviderError, get_ai_provider
from app.services.agent_tools.base import AgentExecutionContext
from app.services.agent_tools.registry import build_tool_registry
from app.services.agent_tools.openai_tool_specs import build_openai_specs

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3
MAX_TOOL_CALLS_PER_MESSAGE = 5

_GREETING_RE = re.compile(
    r"^[\s]*(?:سلام|درود|خوبی[؟?]?|چطوری[؟?]?|چطورید[؟?]?|خوب هستی[؟?]?|"
    r"صبح بخیر|عصر بخیر|شب بخیر|وقت بخیر|"
    r"hi|hello|hey|good\s+morning|good\s+evening|good\s+night|howdy)"
    r"[\s!؟?🌿🌱✨🍃،.]*$",
    re.IGNORECASE | re.UNICODE,
)
_GREETING_REPLY = (
    "سلام، خوش اومدی 🌿\n"
    "امروز می‌تونم در کدوم موضوع کمکت کنم؟\n"
    "• برنامه غذایی یا تنظیم وعده‌ها\n"
    "• انتخاب غذا یا هوس خوردنی الان\n"
    "• پیشرفت هدف و وضعیت بدن\n"
    "• سوال درباره مواد مغذی یا ترکیب غذا"
)

_ORCHESTRATOR_SYSTEM = """\
You are the Diet Coach Agent — a trusted nutrition companion.
You have access to backend tools to help the user.

TOOL USAGE RULES — Always use tools when the user:
- Asks about food calories/nutrition → analyze_meal (should_log=false — NEVER log hypothetical questions)
- Reports eating something → analyze_meal (should_log=true)
- Wants plan updated/adjusted → update_tomorrow_plan and/or adapt_plan
- Asks what to eat → what_to_eat_now
- Wants to generate a plan → generate_week_plan
- Asks about their schedule/plan → get_calendar
- Asks about progress → get_progress_summary
- Logs daily check-in (weight, sleep, activity) → log_check_in

CRITICAL RULES FOR PLAN UPDATE TOOLS:
- update_tomorrow_plan → ONLY when user explicitly asks to change tomorrow's plan
  ("برنامه فردامو تغییر بده", "make tomorrow lighter", etc.)
  NEVER call update_tomorrow_plan just because a user asks a calorie question.
- generate_week_plan → ONLY when user explicitly asks to generate a new week plan.
- A question like "how many calories does X have?" or "X چقدر کالری داره؟" is a
  HYPOTHETICAL CALORIE QUESTION — call analyze_meal(should_log=false) ONLY.
  Do NOT call update_tomorrow_plan or generate_week_plan for calorie questions.

RESPONSE RULES:
- Summarize tool results naturally — never show raw JSON or internal details
- Do NOT claim success unless tool result shows success=true
- Do NOT shame users for eating off-plan foods or sweets
- Do NOT recommend starvation or extreme calorie restriction
- Do NOT mention tool names, provider, model, or system internals
- Be concise and practical
- If multiple tools ran, summarize each action in a short friendly list
- Never prescribe medication or medical treatment
- Respond in the same language as the user (Persian for Persian, etc.)
"""

_TOOL_REGISTRY = build_tool_registry()
_TOOL_SPECS = build_openai_specs(_TOOL_REGISTRY)


def _is_greeting(message: str) -> bool:
    return bool(_GREETING_RE.match(message.strip()))


def _get_locale(db: Session, user: User) -> str:
    from app.repositories.calendar_repository import resolve_locale, get_user_language
    return resolve_locale(None, get_user_language(db, user.id))


def _text_fallback(db, session, user_msg, ctx, message, history) -> ChatMessageResponse:
    from app.services.nutrition_agent_service import NutritionAgentService
    agent = NutritionAgentService()
    try:
        parsed, result = agent.chat_message(ctx, message, history)
        reply_text = parsed.get("reply") or "چطور می‌توانم کمک کنم؟"
        prov = getattr(result, "provider", "mock")
        is_mock = getattr(result, "is_mock", True)
    except Exception as exc:
        logger.warning("Text fallback failed: %s", exc)
        reply_text = "در حال حاضر پاسخ به پیام شما ممکن نیست. بعداً تلاش کنید."
        prov, is_mock = "mock_fallback", True
    assistant_msg = chat_repository.create_message(db, session.id, "assistant", reply_text)
    db.commit()
    return ChatMessageResponse(
        message_id=assistant_msg.id, role="assistant", content=reply_text,
        provider=prov, is_mock=is_mock, created_at=assistant_msg.created_at,
    )


def process_user_message(db: Session, user: User, message: str) -> ChatMessageResponse:
    session = chat_repository.get_or_create_companion_session(db, user.id)
    user_msg = chat_repository.create_message(db, session.id, "user", message)
    # Commit user message + session before running tools so a tool-level DB rollback
    # cannot erase the user's message from chat history.
    db.commit()

    if _is_greeting(message):
        am = chat_repository.create_message(db, session.id, "assistant", _GREETING_REPLY)
        db.commit()
        return ChatMessageResponse(
            message_id=am.id, role="assistant", content=_GREETING_REPLY,
            provider="local", is_mock=True, created_at=am.created_at,
        )

    locale = _get_locale(db, user)
    ctx = nutrition_memory_service.build(db, user)
    ctx_json = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)

    recent = chat_repository.get_recent_messages(db, session.id, limit=11)
    history = [{"role": m.role, "content": m.content} for m in recent if m.id != user_msg.id]

    provider = get_ai_provider()
    if not provider.supports_tools:
        return _text_fallback(db, session, user_msg, ctx, message, history)

    exec_ctx = AgentExecutionContext(
        db=db, user=user, locale=locale, nutrition_memory=ctx, chat_session_id=session.id,
    )
    system_with_ctx = _ORCHESTRATOR_SYSTEM + f"\nUser profile context: {ctx_json}"
    messages: list[dict] = [{"role": "system", "content": system_with_ctx}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": message})

    actions_summary: list[str] = []
    tool_calls_total = 0
    reply_text = ""
    provider_name = "openai"

    try:
        for round_idx in range(MAX_TOOL_ROUNDS):
            tool_result = provider.generate_with_tools(messages, _TOOL_SPECS)
            provider_name = tool_result.provider

            if not tool_result.tool_calls:
                reply_text = tool_result.assistant_message or ""
                break

            # Append assistant turn with tool_calls
            asst_turn: dict = {"role": "assistant", "content": tool_result.assistant_message or None}
            if tool_result.raw_tool_calls:
                asst_turn["tool_calls"] = tool_result.raw_tool_calls
            messages.append(asst_turn)

            for tc in tool_result.tool_calls[:MAX_TOOL_CALLS_PER_MESSAGE]:
                tool_calls_total += 1
                tool = _TOOL_REGISTRY.get(tc.name)
                if tool is None:
                    tool_content = json.dumps({"error": f"Unknown tool: {tc.name}"})
                elif tool.needs_confirmation(tc.arguments):
                    tool_content = json.dumps({
                        "success": False, "requires_confirmation": True,
                        "message": "این عمل نیاز به تأیید کاربر دارد. از دکمه مربوطه در رابط کاربری استفاده کنید."
                    })
                else:
                    try:
                        tr = tool.execute(exec_ctx, tc.arguments)
                        if tr.success and tr.user_visible_summary:
                            actions_summary.append(tr.user_visible_summary)
                        if not tr.success:
                            # Tool caught a DB error internally; rollback so the session
                            # is usable for saving the assistant reply afterward.
                            try:
                                db.rollback()
                                session = chat_repository.get_or_create_companion_session(db, user.id)
                            except Exception as rb_exc:
                                logger.warning("Post-tool rollback failed: %s", rb_exc)
                        tool_content = json.dumps({
                            "success": tr.success, "summary": tr.user_visible_summary,
                            "data": tr.data, "error": tr.error,
                        }, ensure_ascii=False)
                    except Exception as exc:
                        logger.warning("Tool %s raised: %s", tc.name, exc)
                        try:
                            db.rollback()
                            session = chat_repository.get_or_create_companion_session(db, user.id)
                        except Exception as rb_exc:
                            logger.warning("Post-tool rollback failed: %s", rb_exc)
                        tool_content = json.dumps({"success": False, "error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_content})

            if round_idx == MAX_TOOL_ROUNDS - 1 or not tool_result.tool_calls:
                try:
                    final = provider.generate_with_tools(messages, _TOOL_SPECS)
                    reply_text = final.assistant_message or ""
                except Exception:
                    pass
                break

        if not reply_text:
            if actions_summary:
                reply_text = "کارهای درخواستی انجام شد:\n" + "\n".join(f"• {a}" for a in actions_summary)
            else:
                reply_text = "پیام شما پردازش شد. چطور می‌توانم بیشتر کمک کنم؟"

    except (AIProviderError, Exception) as exc:
        logger.warning("Agent orchestrator error, falling back: %s", exc)
        return _text_fallback(db, session, user_msg, ctx, message, history)

    am = chat_repository.create_message(db, session.id, "assistant", reply_text)
    db.commit()
    return ChatMessageResponse(
        message_id=am.id, role="assistant", content=reply_text,
        provider=provider_name, is_mock=False, created_at=am.created_at,
        actions_summary=actions_summary if actions_summary else None,
        tool_calls_executed=tool_calls_total,
    )
