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

# Structural signal: last assistant turn ended with a question.
_FOLLOWUP_QUESTION_RE = re.compile(r"[؟?]\s*$")

_ORCHESTRATOR_SYSTEM = """\
You are the Diet Coach Agent — a personal nutrition companion. You MUST use tools for nutrition tasks.

MANDATORY TOOL RULES:

1. CALORIE / NUTRITION QUESTION → analyze_meal(should_log=false)
   When: user asks about calories, macros, or nutritional value of ANY food.
   Rule: NEVER answer a calorie question from memory alone — always call analyze_meal.

2. USER REPORTS EATING SOMETHING → analyze_meal(should_log=true) + get_calendar
   When: user says they ate/drank something (past tense), or reports a food event today.
   After tools: NEVER shame the user. Ask ONE supportive follow-up question.
   IMPORTANT: Do NOT call update_tomorrow_plan just because the user ate something.
   Only call update_tomorrow_plan if the user EXPLICITLY asks to adjust tomorrow's plan.

3. EXPLICIT PLAN UPDATE REQUEST → get_calendar + update_tomorrow_plan
   (also call analyze_meal first if food is mentioned in the same message)
   When: user explicitly asks to change, lighten, or adjust tomorrow's plan.
   Trigger phrases: "برنامه فردامو سبک‌تر کن", "فردامو تنظیم کن", "make tomorrow lighter".
   Rule: ONLY say plan was updated if update_tomorrow_plan returns success=true.
   If success=false → apologize, never claim success.

4. WEEK PLAN REQUEST → generate_week_plan
   When: user asks for a plan for next week or multiple future days.

5. WHAT TO EAT NOW → what_to_eat_now
   When: user asks for meal suggestions or what to eat right now.

6. PROGRESS / CHECK-IN → log_check_in or get_progress_summary
   When: user mentions weight, sleep, activity, stress, or asks about their progress.

7. OFF-DOMAIN QUESTION → NO TOOLS — one brief sentence, then redirect to nutrition.
   Rule: do NOT become a general assistant — keep answer brief and pivot back to nutrition.

8. MULTI-TASK → call all relevant tools in parallel, give ONE combined final response.

9. FOLLOW-UP ANSWER DETECTION — read CONVERSATION_STATE before deciding
   If CONVERSATION_STATE reports FOLLOW_UP_PENDING=true:
   • The user's current message is answering the question the assistant just asked.
   • If the message is ONLY providing information (food, time, quantity, context):
     treat it as context. Provide guidance. Do NOT call update_tomorrow_plan.
   • If the message contains an explicit action command ("کن", "بکن", "تنظیم کن",
     "update", "change", "سبک‌تر"): treat it as a new instruction and use tools.
   • Either way: never repeat analysis of events already covered in recent turns.

10. AVOID DUPLICATE ACTIONS — check conversation HISTORY before calling any tool
    • Scan recent assistant messages in history.
    • If a recent assistant turn already indicated tomorrow's plan was updated:
      do NOT call update_tomorrow_plan again unless user says to update it AGAIN.
    • If a food event was already analyzed recently:
      refer to it briefly — do NOT re-run the full analysis on the same event.
    • Repeating the same action without a new explicit user request is always wrong.

CRITICAL RULES (non-negotiable):
- NEVER claim an action succeeded unless the tool returned success=true
- NEVER show raw JSON, tool names, or system internals in your response text
- NEVER shame users for eating off-plan foods or sweets
- NEVER recommend starvation or under 1200 kcal/day
- NEVER prescribe medication or medical treatment
- Respond in the SAME LANGUAGE as the user
- Ask at most 1 follow-up question per turn

RESPONSE FORMAT (strictly enforced):
- Your final response text must NOT contain action confirmations.
  Phrases like "برنامه فردا به‌روزرسانی شد" or "ثبت شد" belong in action chips, not in your text.
  Do not repeat tool result summaries in your conversational response.
- If a food event was already discussed in recent history, refer to it briefly.
  Do not repeat the full nutritional analysis again.
- Write complete sentences. Never output truncated or cut-off text.
- Generate a fresh, clean coaching response. Do not continue from or repeat any
  partial text that appeared before tool calls in this same turn.
"""

_TOOL_REGISTRY = build_tool_registry()
_TOOL_SPECS = build_openai_specs(_TOOL_REGISTRY)

# System message injected immediately before the final text-generation call.
# Prevents the LLM from repeating pre-tool thinking text or tool summaries.
_CLEAN_RESPONSE_REMINDER = (
    "Now write your final coaching response. "
    "Start fresh — do not continue from or repeat any text from before the tool calls. "
    "Do not include action confirmations (e.g. 'برنامه فردا به‌روزرسانی شد') — "
    "those are shown separately. "
    "Be concise. Complete every sentence. Ask at most one follow-up question."
)


def _is_greeting(message: str) -> bool:
    return bool(_GREETING_RE.match(message.strip()))


def _get_locale(db: Session, user: User) -> str:
    from app.repositories.calendar_repository import resolve_locale, get_user_language
    return resolve_locale(None, get_user_language(db, user.id))


def _build_conversation_state(history: list[dict]) -> str:
    """
    Derive conversation state from message history using structural signals only.

    No food-name or content-phrase matching — only message structure (role + punctuation).
    Returns a compact state block to inject into the system prompt so the LLM can make
    a better-informed decision about whether the current message is a follow-up answer
    or a new independent instruction.
    """
    if not history:
        return ""

    last_assistant = next(
        (m for m in reversed(history) if m.get("role") == "assistant"),
        None,
    )
    if last_assistant is None:
        return ""

    content = last_assistant.get("content", "").strip()
    if _FOLLOWUP_QUESTION_RE.search(content):
        return (
            "FOLLOW_UP_PENDING=true\n"
            "The immediately preceding assistant message ended with a question. "
            "The user's current message is likely ANSWERING that question, not issuing a new command.\n"
            "Decision rules:\n"
            "  • If user message is ONLY information/context (food description, quantity, time, name): "
            "treat as a follow-up answer. Provide guidance. "
            "Do NOT call update_tomorrow_plan or generate_week_plan based solely on this.\n"
            "  • If user message contains an explicit action command "
            "('کن', 'بکن', 'تنظیم کن', 'سبک‌تر', 'update', 'change', 'adjust'): "
            "treat as a new instruction and call the appropriate tool.\n"
            "  • Do NOT repeat analysis or actions already completed in recent turns."
        )
    return ""


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

    # Build conversation state annotation from recent history (structural detection only).
    conversation_state = _build_conversation_state(history[-10:])

    system_with_ctx = _ORCHESTRATOR_SYSTEM + f"\nUser profile context: {ctx_json}"
    if conversation_state:
        system_with_ctx += f"\n\nCONVERSATION_STATE:\n{conversation_state}"

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

            # Append assistant turn with tool_calls.
            # Use None for content when the model is calling tools — this prevents partial
            # pre-tool "thinking" text from leaking into the final response context.
            asst_content = tool_result.assistant_message or None
            asst_turn: dict = {"role": "assistant", "content": asst_content}
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
                        # Keep tool result compact: success flag + data only.
                        # Omit user_visible_summary from the LLM context to prevent it
                        # from being copied verbatim into the final response text.
                        tool_content = json.dumps({
                            "success": tr.success,
                            "data": tr.data,
                            "error": tr.error,
                        }, ensure_ascii=False)
                    except Exception as exc:
                        # tool.execute() raised unexpectedly — DB may be dirty, rollback.
                        # Controlled tool failures (success=False return) do not need rollback
                        # because the tool already handled its own error internally.
                        logger.warning("Tool %s raised: %s", tc.name, exc)
                        try:
                            db.rollback()
                            session = chat_repository.get_or_create_companion_session(db, user.id)
                        except Exception as rb_exc:
                            logger.warning("Post-tool rollback failed: %s", rb_exc)
                        tool_content = json.dumps({"success": False, "error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_content})

            if round_idx == MAX_TOOL_ROUNDS - 1 or not tool_result.tool_calls:
                # Inject a clean-response reminder so the model generates a fresh reply
                # instead of continuing from partial pre-tool text or repeating tool summaries.
                messages.append({"role": "system", "content": _CLEAN_RESPONSE_REMINDER})
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
