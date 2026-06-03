"""
PromptBuilder: constructs provider message lists for each nutrition task.

Each method returns a PromptData containing system + user messages and a
TASK:<type> marker the MockAIProvider reads to pick the right response.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from app.services.nutrition_memory_service import NutritionMemoryContext
from app.services.mock_ai_provider import (
    TASK_GENERATE_PLAN,
    TASK_ANALYZE_MEAL,
    TASK_WHAT_TO_EAT,
    TASK_ADAPT_PLAN,
    TASK_CHAT,
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


@dataclass
class PromptData:
    task_type: str
    system: str
    user: str

    def to_messages(self) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user},
        ]


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
    system = f"{_SYSTEM_BASE}\n{TASK_CHAT}{_safety_note(ctx)}"
    user_ctx = json.dumps(ctx.to_compact_dict(), ensure_ascii=False)
    history_str = ""
    if history:
        lines = [f"  [{m['role']}]: {m['content']}" for m in history[-6:]]
        history_str = "\nتاریخچه اخیر گفتگو:\n" + "\n".join(lines) + "\n"
    user = (
        f"مشخصات کاربر: {user_ctx}\n"
        f"{history_str}\n"
        f"پیام کاربر: {user_message}\n\n"
        "به این پیام به عنوان مربی تغذیه پاسخ بده. "
        "پاسخت باید صمیمی، حرفه‌ای و کوتاه باشد (۱ تا ۳ پاراگراف). "
        "دقیقاً به این فرمت JSON پاسخ بده:\n"
        '{"reply": "..."}'
    )
    return PromptData(task_type="chat_message", system=system, user=user)


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
