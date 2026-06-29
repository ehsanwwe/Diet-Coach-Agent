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
from app.schemas.nutrition import (
    ContextGuidanceRequest,
    CravingSupportRequest,
    SlipRecoveryRequest,
)

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

# Structural signal: message ends with a question mark (Persian or ASCII).
_FOLLOWUP_QUESTION_RE = re.compile(r"[؟?]\s*$")

_ORCHESTRATOR_SYSTEM = """\
You are the Diet Coach Agent — a personal nutrition companion. You MUST use tools for nutrition tasks.

MANDATORY TOOL RULES:

1. CALORIE / NUTRITION QUESTION → analyze_meal(should_log=false)
   When: user asks about calories, macros, or nutritional value of ANY food.
   Rule: NEVER answer a calorie question from memory alone — always call analyze_meal.

2. USER REPORTS EATING SOMETHING → analyze_meal(should_log=true) + get_calendar
   When: user says they ate/drank something (past tense), or reports a food event today.
   After tools: NEVER shame the user. You may ask ONE concise supportive follow-up question.
   IMPORTANT: Do NOT call update_tomorrow_plan just because the user ate something.
   Only call update_tomorrow_plan if the user EXPLICITLY asks to adjust tomorrow's plan.

3. EXPLICIT PLAN UPDATE REQUEST → get_calendar + update_tomorrow_plan
   (also call analyze_meal first if food is mentioned in the same message)
   When: user explicitly asks to change, lighten, or adjust tomorrow's plan.
   Trigger phrases: "برنامه فردامو سبک‌تر کن", "فردامو تنظیم کن", "make tomorrow lighter".
   Rule: ONLY say plan was updated if update_tomorrow_plan returns success=true.
   If success=false → apologize, never claim success.

3b. MEAL SUBSTITUTION FOR TODAY → get_calendar + substitute_meal
    When: user asks to swap, replace, or change a SPECIFIC MEAL within today's (or another) plan.
    Trigger phrases: "به جای [X] [Y] می‌خوام", "ناهار/شام/صبحانه رو با [Y] عوض کن", "replace [meal] with [Y]".
    Steps:
    1. Call get_calendar (days=1) to see today's current meals.
    2. Identify: target_date (today unless user specifies a date), meal_slot (infer from context:
       ناهار/نهار=lunch, شام=dinner, صبحانه=breakfast, میان‌وعده=snack).
    3. Craft the replacement meal WITH EXPLICIT PERSIAN HOUSEHOLD QUANTITIES:
       - Pasta/ماکارانی: '۱.۵ لیوان ماکارانی پخته + ۱ کف دست گوشت چرخ‌کرده کم‌چرب + ۱ بشقاب سالاد'
       - Rice+stew: '۷ قاشق غذاخوری برنج پخته + ۴ قاشق خورش [name]'
       - Chicken: '۱ کف دست سینه مرغ (حدود ۱۲۰ گرم) + سبزیجات'
       - Legumes: '۱ کاسه متوسط [food] + نان یا برنج'
    4. Call substitute_meal with the crafted title, description, portion_guidance.
    5. After success=true: report the EXACT updated meal with quantities — do NOT just say 'باشه'.
       Say: 'برنامه امروزت به‌روزرسانی شد. [meal_slot] امروز: [exact description with quantities]'
    6. If user then asks for "برنامه جدید" or the full updated plan: call get_calendar and show
       the ACTUAL stored plan — never invent a plan from memory.
    If no plan exists for today: say 'برنامه‌ای برای امروز ثبت نشده' and offer to generate one.
    NEVER use vague amounts like 'مقدار مناسب', 'کمی', 'کنترل‌شده' in the substitution.

4. WEEK PLAN REQUEST → generate_week_plan
   When: user asks for a plan for next week or multiple future days.

5. WHAT TO EAT NOW → what_to_eat_now
   When: user asks for meal suggestions or what to eat right now.
   ALSO WHEN: user reports still being hungry, hunger pain, hunger burn, or weakness
              after a food event — call what_to_eat_now immediately, do NOT ask more questions.
   hunger_level mapping: "گرسنه‌ام" / "هنوز گرسنه" / "سوزش گرسنگی" / "شکم‌درد" → hunger_level="high"

6. PROGRESS / CHECK-IN → log_check_in or get_progress_summary
   When: user mentions weight, sleep, activity, stress, or asks about their progress.

7. STORED PERSONAL DATA QUESTION → query_user_nutrition_data
   When: user asks about their history, patterns, adherence, previous meals, logged data,
   current plan details, progress trends, or anything that requires facts from the database.
   Examples that MUST trigger this tool:
     "این هفته چقدر به برنامه پایبند بودم؟" → query recent check-ins and adherence data
     "بیشتر کجاها رژیمم خراب میشه؟" → query meal entries + check-ins for pattern analysis
     "تو وعده‌هام پروتئین کمه؟" → query recent meal entries and plan day meals for macros
     "تو چند روز اخیر بیشتر چی خوردم؟" → query recent meal entries ordered by date
     "از وقتی شروع کردم وزنم بهتر شده؟" → query progress entries or check-ins for weight trend
     "بر اساس برنامه و چیزایی که خوردم، شام چی بخورم?" → query plan + meal entries together

   SQL rules you MUST follow when constructing the sql argument:
     - Use :user_id as the ONLY user identifier — never hard-code any ID
     - Reference only whitelisted nutrition tables (meal_entries, daily_checkins,
       progress_entries, nutrition_plan_days, nutrition_plan_day_meals, nutrition_plan_calendars,
       nutrition_plans, nutrition_goals, user_profiles, lifestyle_profiles, behavior_profiles,
       food_preferences, allergies, medications, user_medical_flags, weekly_reports, etc.)
     - Always include ORDER BY and LIMIT (max 100)
     - No comments, no semicolons, no UNION/INSERT/UPDATE/DELETE/DROP/ALTER

   If the tool returns success=false:
     - Do NOT mention SQL, database, or the tool in your response
     - If no data: say the user hasn't logged enough yet; give useful next step advice
     - If query failed: answer from your nutrition knowledge and profile context

   INVISIBILITY RULE (strictly enforced): Never say "I checked the database", "I ran a query",
   "according to table X", "the tool returned", or any reference to internal mechanics.
   Instead use natural coaching language:
     ✓ "با توجه به اطلاعات ثبت‌شده‌ات..."
     ✓ "در گزارش‌های اخیرت دیده میشه..."
     ✓ "از الگوی چند روز اخیرت مشخصه..."
     ✓ "فعلاً داده کافی ثبت نشده، اما برای شروع..."
     ✗ "طبق جدول meal_entries..."
     ✗ "I queried your database..."
     ✗ "نتیجه ابزار نشون میده..."

8. OFF-DOMAIN QUESTION → NO TOOLS — one brief sentence, then redirect to nutrition.
   Rule: do NOT become a general assistant — keep answer brief and pivot back to nutrition.

9. MULTI-TASK → call all relevant tools in parallel, give ONE combined final response.

10. FOLLOW-UP ANSWER DETECTION — read CONVERSATION_STATE before deciding
    If CONVERSATION_STATE shows FOLLOW_UP_PENDING=true:
    • The user's current message is answering the question the assistant already asked.
    • MANDATORY: Take action. Do NOT ask another diagnostic question.
    • If user reports hunger or any hunger-related discomfort: call what_to_eat_now(hunger_level="high")
      and give a specific decisive food recommendation — name the food and portion.
    • If user message contains an explicit action command ('کن', 'بکن', 'تنظیم کن', 'سبک‌تر'):
      treat as a new instruction and call the appropriate tool.
    • NEVER repeat analysis of food events already covered in recent turns.
    If CONVERSATION_STATE shows MAX_FOLLOWUPS_REACHED=true:
    • ABSOLUTE RULE: Do NOT ask any question. Call tools. Give decisive answer only.
    • Call what_to_eat_now for any hunger/discomfort context.

11. AVOID DUPLICATE ACTIONS — check conversation HISTORY before calling any tool
    • If a recent assistant turn already updated tomorrow's plan: do NOT update again.
    • If a food event was already analyzed recently: refer to it briefly, do NOT re-analyze.

FOLLOW-UP LIMIT (critical):
- Per user issue/event, ask AT MOST 1 clarifying question before taking action.
- 'گرسنه‌ام', 'هنوز گرسنه‌ام', 'سوزش گرسنگی', 'شکم‌درد از گرسنگی', 'ضعف' are NOT reasons to ask.
  They are signals to call what_to_eat_now and give immediate food guidance.
- Safety exception ONLY for life-threatening symptoms: 'درد شدید قفسه سینه', 'استفراغ خون' etc.

CRITICAL RULES (non-negotiable):
- NEVER claim an action succeeded unless the tool returned success=true
- NEVER show raw JSON, SQL, tool names, table names, or system internals in your response text
- NEVER shame users for eating off-plan foods or sweets
- NEVER recommend starvation or under 1200 kcal/day
- NEVER prescribe medication or medical treatment
- Respond in the SAME LANGUAGE as the user
- Ask at most 1 follow-up question per turn; 0 questions when MAX_FOLLOWUPS_REACHED=true

RESPONSE FORMAT (strictly enforced):
- Your final response text must NOT contain action confirmations.
  Phrases like "برنامه فردا به‌روزرسانی شد" or "ثبت شد" belong in action chips, not in your text.
  Do not repeat tool result summaries in your conversational response.
- When plan update succeeds: briefly mention WHAT changed (e.g. more fiber/protein, lighter carbs).
- If plan update fails: say you could not save the update; still give the immediate food recommendation.
- If a food event was already discussed in recent history, refer to it briefly.
  Do not repeat the full nutritional analysis again.
- Write complete sentences. Never output truncated or cut-off text.
- Generate a fresh, clean coaching response. Do not continue from or repeat any
  partial text that appeared before tool calls in this same turn.
"""

_TOOL_REGISTRY = build_tool_registry()
_TOOL_SPECS = build_openai_specs(_TOOL_REGISTRY)

_CRAVING_KEYWORDS = (
    "craving", "cravings", "sweet craving", "i want chocolate",
    "هوس", "ولع", "دلم شکلات", "دلم شیرینی", "ریزه‌خواری", "ریزه خواری",
)
_SLIP_KEYWORDS = (
    "overate", "ate too much", "broke my diet", "ruined my diet", "slip",
    "پرخوری", "زیاد خوردم", "رژیمم خراب", "همه چیز خراب", "لغزش", "خراب شد",
    # natural eating-event phrases that imply off-plan eating
    "شیرینی خوردم", "کیک خوردم", "چیپس خوردم", "بیسکویت خوردم", "زیادی خوردم",
)

_PLAN_CHANGE_KEYWORDS = (
    "change my plan", "modify my plan", "update my plan",
    "تغییرش بدی", "تغییرش بده", "تغییر بده", "برنامه رو تغییر",
    "برنامه‌ام رو عوض", "عوضش بده", "عوضش کن", "می‌تونی تغییرش",
    "میتونی تغییرش", "میشه تغییرش", "می‌شه تغییرش",
)

_PLAN_CHANGE_MOCK_REPLY = (
    "بله، می‌تونم کمکت کنم برنامه رو تنظیم کنیم 🌿\n\n"
    "چه بخشی رو می‌خوای تغییر بدی؟\n"
    "• یک وعده خاص (صبحانه، ناهار، شام، میان‌وعده)\n"
    "• سبک‌تر یا سنگین‌تر کردن کل برنامه\n"
    "• جایگزینی مواد غذایی (مثلاً حذف لبنیات یا گوشت)\n"
    "• تنظیم بر اساس برنامه ورزشی\n"
    "• تغییر بر اساس بودجه یا دسترسی به مواد\n\n"
    "بگو چه تغییری داری در نظر و من کمکت می‌کنم."
)
_CONTEXT_KEYWORDS = (
    "restaurant", "party", "travel", "travelling", "traveling", "fast food",
    "رستوران", "مهمونی", "مهمانی", "سفر", "فست فود", "مسافرت",
)


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _detect_behavior_intent(message: str) -> str | None:
    if _contains_keyword(message, _SLIP_KEYWORDS):
        return "slip_recovery"
    if _contains_keyword(message, _CRAVING_KEYWORDS):
        return "craving_support"
    if _contains_keyword(message, _CONTEXT_KEYWORDS):
        return "context_guidance"
    return None


def _context_type_from_message(message: str) -> str:
    lowered = message.lower()
    if "restaurant" in lowered or "رستوران" in lowered or "fast food" in lowered or "فست فود" in lowered:
        return "restaurant"
    if "party" in lowered or "مهمونی" in lowered or "مهمانی" in lowered:
        return "party"
    if "travel" in lowered or "traveling" in lowered or "travelling" in lowered or "سفر" in lowered or "مسافرت" in lowered:
        return "travel"
    return "mixed"


def _behavior_reply(intent: str, data: dict) -> str:
    if intent == "craving_support":
        parts = [
            data.get("calming_message"),
            data.get("hunger_vs_craving_assessment"),
            (data.get("better_choice") or {}).get("description"),
            data.get("prevention_tip"),
        ]
    elif intent == "slip_recovery":
        parts = [
            data.get("calming_message"),
            data.get("data_not_failure_message"),
            data.get("one_small_adjustment"),
            data.get("next_meal_plan"),
            data.get("no_extreme_compensation_note"),
        ]
    else:
        parts = [
            data.get("best_available_choice"),
            data.get("flexible_choice"),
            data.get("portion_strategy"),
            data.get("next_meal_adjustment"),
        ]
    return "\n".join(str(p) for p in parts if p) or "راهنمایی آماده شد."


def _save_assistant_response(
    db: Session,
    session_id: str,
    content: str,
    pending_id: str | None,
    status: str = "completed",
) -> "ChatMessage":
    """Update the pending placeholder if given, otherwise create a new assistant message."""
    from app.models.chat import ChatMessage  # local import avoids circular
    if pending_id:
        return chat_repository.update_message_status(
            db, pending_id, status=status, content=content
        )
    return chat_repository.create_message(db, session_id, "assistant", content, status=status)


def _run_behavior_workflow(
    db: Session,
    session,
    user: User,
    message: str,
    intent: str,
    pending_id: str | None = None,
) -> ChatMessageResponse:
    from app.services import nutrition_service

    if intent == "craving_support":
        result = nutrition_service.get_craving_support(
            db,
            user,
            CravingSupportRequest(user_note=message),
        )
    elif intent == "slip_recovery":
        result = nutrition_service.recover_from_slip(
            db,
            user,
            SlipRecoveryRequest(what_happened=message, user_note=message),
        )
    else:
        result = nutrition_service.get_restaurant_party_travel_guidance(
            db,
            user,
            ContextGuidanceRequest(
                context_type=_context_type_from_message(message),
                user_note=message,
            ),
        )

    payload = result.model_dump(mode="json")
    reply_text = _behavior_reply(intent, payload)
    assistant_msg = _save_assistant_response(db, session.id, reply_text, pending_id)
    db.commit()
    return ChatMessageResponse(
        message_id=assistant_msg.id,
        role="assistant",
        content=reply_text,
        provider=result.provider,
        is_mock=result.is_mock,
        created_at=assistant_msg.created_at,
        actions_summary=[intent],
        tool_calls_executed=1,
    )


def _clean_response_reminder(conversation_state: str = "") -> str:
    """Build the pre-final-response system reminder, stricter when follow-up limit is reached."""
    base = (
        "Now write your final coaching response. "
        "Start fresh — do not continue from or repeat any text from before the tool calls. "
        "Do not include action confirmations (e.g. 'برنامه فردا به‌روزرسانی شد') in your main text — "
        "those are shown separately as action chips. "
        "Be concise. Complete every sentence."
    )
    if "MAX_FOLLOWUPS_REACHED" in conversation_state:
        return (
            base
            + " DO NOT ask a follow-up question — provide decisive food guidance only. "
            "Name specific food options and portions."
        )
    return base + " Ask at most one follow-up question only if genuinely needed."


def _is_greeting(message: str) -> bool:
    return bool(_GREETING_RE.match(message.strip()))


def _get_locale(db: Session, user: User) -> str:
    from app.repositories.calendar_repository import resolve_locale, get_user_language
    return resolve_locale(None, get_user_language(db, user.id))


def _count_recent_followup_questions(history: list[dict]) -> int:
    """
    Count how many consecutive recent assistant messages ended with a question mark.

    Iterates history in reverse, skipping user messages, counting assistant messages
    that end with '؟' or '?'. Stops at the first assistant message that does NOT end
    with a question mark, or after examining 6 assistant messages.
    """
    count = 0
    for msg in reversed(history):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content") or ""
        if _FOLLOWUP_QUESTION_RE.search(content.strip()):
            count += 1
        else:
            break
        if count >= 6:
            break
    return count


def _build_conversation_state(history: list[dict]) -> str:
    """
    Derive conversation state from message history using structural signals only.

    No food-name or content-phrase matching — only message structure (role + punctuation).
    Returns a compact state block injected into the system prompt so the LLM knows
    whether the user is answering a follow-up question and whether the follow-up budget
    is exhausted (mandating action instead of another question).
    """
    if not history:
        return ""

    followup_count = _count_recent_followup_questions(history)

    if followup_count == 0:
        return ""

    if followup_count >= 2:
        return (
            f"FOLLOW_UP_COUNT={followup_count}\n"
            "FOLLOW_UP_PENDING=true\n"
            "MAX_FOLLOWUPS_REACHED=true\n"
            "⚠️ MANDATORY ACTION REQUIRED: The assistant has already asked MULTIPLE follow-up questions.\n"
            "The user is answering them. You MUST call tools and provide decisive guidance NOW.\n"
            "ABSOLUTELY FORBIDDEN: Asking any further diagnostic question.\n"
            "REQUIRED for hunger/discomfort after food:\n"
            "  → call what_to_eat_now(hunger_level='high', meal_context='<brief summary>')\n"
            "  → give SPECIFIC food recommendation — name the food, portion, and when to eat it\n"
            "  → call update_tomorrow_plan ONLY if user EXPLICITLY asked for plan update\n"
            "ORDINARY SYMPTOMS DO NOT NEED MORE QUESTIONS:\n"
            "  'گرسنه‌ام' / 'هنوز گرسنه‌ام' / 'سوزش گرسنگی' / 'شکم‌درد از گرسنگی' / 'ضعف'\n"
            "  → these all mean the user needs food NOW — call what_to_eat_now\n"
            "Safety exception ONLY for life-threatening symptoms like 'درد شدید قفسه سینه' or 'استفراغ خون'.\n"
        )

    # followup_count == 1: one follow-up already asked — enforce action on next response
    return (
        "FOLLOW_UP_COUNT=1\n"
        "FOLLOW_UP_PENDING=true\n"
        "The assistant already asked one follow-up question. The user is now answering it.\n"
        "MANDATORY RULES:\n"
        "  • If user reports hunger, hunger pain, hunger burn, or stomach discomfort:\n"
        "    → call what_to_eat_now(hunger_level='high') immediately — do NOT ask another question.\n"
        "  • If user message is purely informational: provide concrete guidance, no more questions.\n"
        "  • If user message contains explicit action command ('کن', 'تنظیم کن', 'سبک‌تر'):\n"
        "    → call the appropriate tool.\n"
        "  • NEVER repeat analysis already completed in recent turns.\n"
    )


def _text_fallback(db, session, user_msg, ctx, message, history, pending_id=None) -> ChatMessageResponse:
    # In mock/no-tool mode, detect plan-change intent and give a contextual reply
    # instead of the generic canned response from the mock chat task.
    if _contains_keyword(message, _PLAN_CHANGE_KEYWORDS):
        reply_text = _PLAN_CHANGE_MOCK_REPLY
        am = _save_assistant_response(db, session.id, reply_text, pending_id)
        db.commit()
        return ChatMessageResponse(
            message_id=am.id, role="assistant", content=reply_text,
            provider="local", is_mock=True, created_at=am.created_at,
        )
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
    assistant_msg = _save_assistant_response(db, session.id, reply_text, pending_id)
    db.commit()
    return ChatMessageResponse(
        message_id=assistant_msg.id, role="assistant", content=reply_text,
        provider=prov, is_mock=is_mock, created_at=assistant_msg.created_at,
    )


def process_user_message(
    db: Session,
    user: User,
    message: str,
    client_message_id: str | None = None,
) -> ChatMessageResponse:
    session = chat_repository.get_or_create_companion_session(db, user.id)

    # Idempotency: if client already sent this message, return the existing response.
    if client_message_id:
        existing = chat_repository.get_message_by_client_id(db, session.id, client_message_id)
        if existing:
            last_assistant = chat_repository.get_last_assistant_message(db, session.id)
            if last_assistant:
                return ChatMessageResponse(
                    message_id=last_assistant.id,
                    role="assistant",
                    content=last_assistant.content,
                    provider="idempotent",
                    is_mock=False,
                    created_at=last_assistant.created_at,
                )

    # Save user message immediately.
    user_msg = chat_repository.create_message(
        db, session.id, "user", message,
        status="completed",
        client_message_id=client_message_id,
    )
    # Create pending assistant placeholder so GET /history immediately shows a
    # thinking state even if the user navigates away while AI is generating.
    pending_msg = chat_repository.create_message(
        db, session.id, "assistant", "",
        status="pending",
    )
    db.commit()
    pending_id = pending_msg.id

    if _is_greeting(message):
        am = _save_assistant_response(db, session.id, _GREETING_REPLY, pending_id)
        db.commit()
        return ChatMessageResponse(
            message_id=am.id, role="assistant", content=_GREETING_REPLY,
            provider="local", is_mock=True, created_at=am.created_at,
        )

    locale = _get_locale(db, user)
    ctx = nutrition_memory_service.build(db, user)
    ctx_json = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)

    # Exclude the current user message and the pending placeholder from context history.
    recent = chat_repository.get_recent_messages(db, session.id, limit=12)
    history = [
        {"role": m.role, "content": m.content}
        for m in recent
        if m.id != user_msg.id
        and m.id != pending_id
        and m.status not in ("pending",)
        and m.content
    ]

    provider = get_ai_provider()
    if not provider.supports_tools:
        # Mock/no-tool mode: use behavior intent routing for structured responses,
        # then fall back to text_fallback. The LLM orchestrator is unavailable here.
        behavior_intent = _detect_behavior_intent(message)
        if behavior_intent is not None:
            return _run_behavior_workflow(db, session, user, message, behavior_intent, pending_id)
        return _text_fallback(db, session, user_msg, ctx, message, history, pending_id)

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
                if tool_calls_total > 0:
                    # Tools were already called in a prior round.
                    # Inject the clean-response reminder before accepting the model's text
                    # to prevent partial pre-tool "thinking" text from bleeding through.
                    messages.append({"role": "system", "content": _clean_response_reminder(conversation_state)})
                    try:
                        clean = provider.generate_with_tools(messages, _TOOL_SPECS)
                        reply_text = clean.assistant_message or ""
                    except Exception as exc:
                        logger.warning("Clean response generation failed: %s", exc)
                        reply_text = tool_result.assistant_message or ""
                else:
                    # No tools called at all — pure text response, use as-is.
                    reply_text = tool_result.assistant_message or ""
                break

            # Append assistant turn with tool_calls.
            # Always set content=None to discard any partial pre-tool "thinking" text
            # the model may have generated before deciding to call tools.
            asst_turn: dict = {"role": "assistant", "content": None}
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
                        logger.warning("Tool %s raised: %s", tc.name, exc)
                        try:
                            db.rollback()
                            session = chat_repository.get_or_create_companion_session(db, user.id)
                        except Exception as rb_exc:
                            logger.warning("Post-tool rollback failed: %s", rb_exc)
                        tool_content = json.dumps({"success": False, "error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_content})

            if round_idx == MAX_TOOL_ROUNDS - 1:
                # Exhausted all rounds — force final generation with clean reminder.
                messages.append({"role": "system", "content": _clean_response_reminder(conversation_state)})
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
        return _text_fallback(db, session, user_msg, ctx, message, history, pending_id)

    am = _save_assistant_response(db, session.id, reply_text, pending_id)
    db.commit()
    return ChatMessageResponse(
        message_id=am.id, role="assistant", content=reply_text,
        provider=provider_name, is_mock=False, created_at=am.created_at,
        actions_summary=actions_summary if actions_summary else None,
        tool_calls_executed=tool_calls_total,
    )
