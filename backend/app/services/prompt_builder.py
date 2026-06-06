"""
PromptBuilder: constructs provider message lists for each nutrition task.

Each method returns a PromptData containing system + user messages and a
TASK:<type> marker the MockAIProvider reads to pick the right response.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.mock_ai_provider import (
    TASK_GENERATE_PLAN,
    TASK_ANALYZE_MEAL,
    TASK_WHAT_TO_EAT,
    TASK_ADAPT_PLAN,
    TASK_CHAT,
    TASK_GENERATE_WEEK_FA,
    TASK_GENERATE_WEEK_EN,
    TASK_GENERATE_WEEK_AR,
)

_SYSTEM_BASE = """\
شما DietCoach هستید، یک متخصص تغذیه حرفه‌ای و دلسوز که به زبان فارسی پاسخ می‌دهد.
محدودیت‌های ایمنی (اجباری):
- هرگز رژیم‌های بسیار کم‌کالری (کمتر از ۱۲۰۰ کالری برای زنان / ۱۵۰۰ برای مردان) توصیه نکنید.
- هرگز دارو تجویز نکنید یا درمان پزشکی توصیه نکنید.
- هرگز درباره وزن یا ظاهر بدن قضاوت نکنید.
- این اپلیکیشن جایگزین متخصص تغذیه یا پزشک نیست.
- برای کاربران با ریسک پزشکی بالا، فقط راهنمایی کلی ارائه دهید.

اولویت‌های فرهنگی:
- از غذاهای ایرانی استفاده کنید (برنج، نان، حبوبات، سبزیجات، لبنیات، گوشت حلال)
- غذاهای غیرواقع‌بینانه یا کاملاً غربی پیشنهاد ندهید
- در صورت نیاز به رعایت حلال، این الزام را جدی بگیرید

فرمت پاسخ:
فقط JSON معتبر برگردانید. هیچ متنی خارج از JSON ننویسید.
"""


# Extra instructions injected into the system prompt for companion chat only.
_SYSTEM_CHAT_RULES = """\

دستورالعمل‌های گفتگو (اجباری — فقط برای این task):
- به زبانی که کاربر نوشته پاسخ بده. اگر فارسی نوشت، فارسی پاسخ بده.
- پاسخ کوتاه و طبیعی باشد؛ از جملات پرکننده خودداری کن.
- حداکثر یک سوال دنباله‌ای بپرس.
- اگر کاربر فقط سلام یا احوال‌پرسی کرده: یک جمله خوش‌آمد کوتاه بنویس و ۲ تا ۴ موضوع تغذیه‌ای پیشنهاد بده.
- هرگز این عبارات را ننویس: «دسترسی به اطلاعات مربی»، «مربی تغذیه‌ات»، «اینقدر از اپ استفاده»، «خوشحالیم که اومدی/برگشتی».
- اطلاعات داخلی سیستم (مدل AI، provider، حافظه سیستم) را هرگز ذکر نکن.
- از جملات انگیزشی کلیشه‌ای خودداری کن.
- درباره وزن یا ظاهر قضاوت نکن.
- دارو تجویز نکن.\
"""


@dataclass
class PromptData:
    task_type: str
    system: str
    user: str
    history_messages: list[dict[str, str]] = field(default_factory=list)

    def to_messages(self) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = [{"role": "system", "content": self.system}]
        msgs.extend(self.history_messages)
        msgs.append({"role": "user", "content": self.user})
        return msgs


def _safety_note(ctx: NutritionMemoryContext) -> str:
    if ctx.clinical_review_required:
        return (
            "\n⚠️ این کاربر نیاز به بررسی پزشکی دارد. "
            "فقط راهنمایی کلی سلامت ارائه دهید، برنامه غذایی تخصصی ندهید."
        )
    if ctx.risk_level == "high":
        return (
            "\n⚠️ این کاربر ریسک بالا دارد. "
            "برنامه محافظه‌کارانه و عمومی ارائه دهید."
        )
    return ""


def for_generate_plan(ctx: NutritionMemoryContext) -> PromptData:
    system = f"{_SYSTEM_BASE}\n{TASK_GENERATE_PLAN}{_safety_note(ctx)}"
    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False, indent=2)
    user = (
        f"مشخصات کاربر:\n{user_ctx}\n\n"
        "یک برنامه تغذیه اولیه برای این کاربر طراحی کن.\n"
        "پاسخ را دقیقاً به این فرمت JSON برگردان:\n"
        "{\n"
        '  "title": "...",\n'
        '  "summary": "...",\n'
        '  "daily_guidelines": {"calories": int, "protein_g": float, "carbs_g": float, "fat_g": float, "fiber_g": float, "water_liters": float, "notes": "..."},\n'
        '  "meals": [{"meal_time": "breakfast|lunch|dinner|snack", "name": "...", "description": "...", "calories_estimate": int, "protein_g": float, "carbs_g": float, "fat_g": float, "notes": null}],\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="generate_plan", system=system, user=user)


def for_analyze_meal(
    ctx: NutritionMemoryContext,
    meal_text: str,
    meal_time: str,
    meal_context: str | None,
) -> PromptData:
    system = f"{_SYSTEM_BASE}\n{TASK_ANALYZE_MEAL}{_safety_note(ctx)}"
    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)
    extra = f"\nاطلاعات بیشتر: {meal_context}" if meal_context else ""
    user = (
        f"مشخصات کاربر: {user_ctx}\n\n"
        f"وعده غذایی: {meal_text}\n"
        f"نوع وعده: {meal_time}{extra}\n\n"
        "این وعده را تحلیل کن و نتیجه را دقیقاً به این فرمت JSON برگردان:\n"
        "{\n"
        '  "quality_score": int (1-10),\n'
        '  "analysis_summary": "...",\n'
        '  "protein": "...",\n'
        '  "fiber": "...",\n'
        '  "sugar": "...",\n'
        '  "balance": "...",\n'
        '  "portion": "...",\n'
        '  "suggestions": ["..."],\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="analyze_meal", system=system, user=user)


def for_what_to_eat_now(
    ctx: NutritionMemoryContext,
    available_foods: list[str],
    hunger_level: str,
    meal_context: str | None,
    time_available_minutes: int | None,
) -> PromptData:
    system = f"{_SYSTEM_BASE}\n{TASK_WHAT_TO_EAT}{_safety_note(ctx)}"
    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)
    foods_str = "، ".join(available_foods) if available_foods else "مواد معمول آشپزخانه ایرانی"
    time_str = f"{time_available_minutes} دقیقه" if time_available_minutes else "نامشخص"
    extra = f"\nاطلاعات بیشتر: {meal_context}" if meal_context else ""
    user = (
        f"مشخصات کاربر: {user_ctx}\n\n"
        f"مواد موجود: {foods_str}\n"
        f"سطح گرسنگی: {hunger_level}\n"
        f"زمان آماده‌سازی: {time_str}{extra}\n\n"
        "۲ تا ۳ گزینه غذایی پیشنهاد بده. دقیقاً به این فرمت JSON:\n"
        "{\n"
        '  "options": [{"name": "...", "description": "...", "calories_estimate": int, "prep_time_minutes": int, "tags": ["..."]}],\n'
        '  "reasoning_summary": "...",\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="what_to_eat_now", system=system, user=user)


def for_chat_message(
    ctx: NutritionMemoryContext,
    user_message: str,
    history: list[dict[str, str]],
) -> PromptData:
    user_ctx_json = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)
    system = (
        f"{_SYSTEM_BASE}\n"
        f"{TASK_CHAT}"
        f"{_SYSTEM_CHAT_RULES}\n"
        f"پروفایل کاربر (پس‌زمینه — نیازی به ذکر صریح آن نیست): {user_ctx_json}"
        f"{_safety_note(ctx)}"
    )

    # Recent history as proper role-separated turns (clean, no embedded text)
    clean_history: list[dict[str, str]] = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-6:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    user = (
        f"{user_message}\n\n"
        "پاسخ مختصر و طبیعی بده. دقیقاً به این فرمت JSON:\n"
        '{"reply": "..."}'
    )
    return PromptData(
        task_type="chat_message",
        system=system,
        user=user,
        history_messages=clean_history,
    )


_LOCALE_TASK_MAP = {
    "fa": TASK_GENERATE_WEEK_FA,
    "en": TASK_GENERATE_WEEK_EN,
    "ar": TASK_GENERATE_WEEK_AR,
}

_LOCALE_LANG_MAP = {
    "fa": "Persian (فارسی). All user-facing text MUST be in Persian.",
    "en": "English. All user-facing text MUST be in English. Food names may use transliterations (e.g. ghormeh sabzi, kabob, doogh).",
    "ar": "Arabic (العربية). All user-facing text MUST be in Arabic. Food names may use transliterations.",
}

_LOCALE_SAFETY_MAP = {
    "fa": "در صورت بررسی پزشکی لازم، برنامه کلی و ایمن ارائه دهید و هشدار مشاوره متخصص اضافه کنید.",
    "en": "If clinical_review_required, generate a general wellness-safe plan only and include a warning recommending specialist review.",
    "ar": "إذا كان المستخدم يحتاج مراجعة طبية، قدم خطة عامة وآمنة فقط وأضف تحذيراً بضرورة استشارة متخصص.",
}


def for_generate_week_plan(ctx: NutritionMemoryContext, locale: str, extra_context: str | None = None) -> PromptData:
    task_tag = _LOCALE_TASK_MAP.get(locale, TASK_GENERATE_WEEK_FA)
    lang_instruction = _LOCALE_LANG_MAP.get(locale, _LOCALE_LANG_MAP["fa"])
    safety = _LOCALE_SAFETY_MAP.get(locale, _LOCALE_SAFETY_MAP["fa"])
    safety_note = _safety_note(ctx)

    system = (
        f"You are DietCoach, a professional nutrition expert.\n"
        f"Output language: {lang_instruction}\n"
        f"Safety rules:\n"
        f"- Never recommend extremely low-calorie diets (<1200 kcal for women / <1500 for men).\n"
        f"- Never prescribe medication or medical treatment.\n"
        f"- Never body-shame.\n"
        f"- {safety}\n"
        f"Cultural priority: Use Iranian/Persian food culture. Include kebab, rice, stew, yogurt, bread, legumes.\n"
        f"Output: Return JSON ONLY. No markdown. No explanations outside JSON.\n"
        f"{task_tag}{safety_note}"
    )

    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False, indent=2)
    user = (
        f"User profile:\n{user_ctx}\n\n"
        f"Generate exactly 7 days of meal plan in {locale} language.\n"
        f"Repetition of meals between days is allowed.\n"
        f"Each day must have exactly 4 meals: breakfast, lunch, dinner, snack.\n"
        f"Return JSON only, matching this exact structure:\n"
        "{\n"
        f'  "locale": "{locale}",\n'
        '  "days": [\n'
        '    {\n'
        '      "day_index": 1,\n'
        '      "title": "...",\n'
        '      "summary": "...",\n'
        '      "hydration_goal": "...",\n'
        '      "notes": "...",\n'
        '      "warnings": [],\n'
        '      "meals": [\n'
        '        {\n'
        '          "meal_type": "breakfast",\n'
        '          "title": "...",\n'
        '          "description": "...",\n'
        '          "portion_guidance": "...",\n'
        '          "alternatives": ["..."],\n'
        '          "preparation_notes": null\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        "}\n"
        f"All string values must be written in {locale} language only."
    )
    if extra_context:
        user = f"Special instruction for this request: {extra_context}\n\n" + user
    return PromptData(task_type=f"generate_week_{locale}", system=system, user=user)


def for_adapt_plan(
    ctx: NutritionMemoryContext,
    current_plan_title: str | None,
    reason: str,
    recent_context: dict,
) -> PromptData:
    system = f"{_SYSTEM_BASE}\n{TASK_ADAPT_PLAN}{_safety_note(ctx)}"
    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)
    plan_info = f"برنامه فعلی: {current_plan_title}" if current_plan_title else "بدون برنامه فعال"
    ctx_str = json.dumps(recent_context, ensure_ascii=False) if recent_context else "{}"
    user = (
        f"مشخصات کاربر: {user_ctx}\n\n"
        f"{plan_info}\n"
        f"دلیل تطبیق: {reason}\n"
        f"وضعیت اخیر: {ctx_str}\n\n"
        "برنامه را با توجه به بازخورد کاربر تطبیق بده. دقیقاً به این فرمت JSON:\n"
        "{\n"
        '  "changes": ["..."],\n'
        '  "updated_guidelines": {"calories": int, "protein_g": float, "carbs_g": float, "fat_g": float, "fiber_g": float, "water_liters": float, "notes": "..."},\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="adapt_plan", system=system, user=user)
