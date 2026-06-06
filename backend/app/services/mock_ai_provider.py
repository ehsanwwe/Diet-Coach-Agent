"""
MockAIProvider: deterministic Persian-friendly structured responses.

No external API calls. App works fully end-to-end with this provider.
PromptBuilder embeds TASK:<type> markers that this provider reads to pick the right mock.
"""
from __future__ import annotations

import json

from app.services.ai_provider import AIProvider, AIProviderResult

# Task markers injected by PromptBuilder into the system message
TASK_GENERATE_PLAN = "TASK:generate_plan"
TASK_ANALYZE_MEAL = "TASK:analyze_meal"
TASK_WHAT_TO_EAT = "TASK:what_to_eat_now"
TASK_ADAPT_PLAN = "TASK:adapt_plan"
TASK_CHAT = "TASK:chat_message"

_MOCK_PLAN = {
    "title": "برنامه تغذیه اولیه",
    "summary": (
        "یک برنامه غذایی متعادل برای شروع سفر سلامت شما. "
        "این برنامه بر اساس اطلاعات شخصی شما طراحی شده است."
    ),
    "daily_guidelines": {
        "calories": 2000,
        "protein_g": 75,
        "carbs_g": 250,
        "fat_g": 65,
        "fiber_g": 25,
        "water_liters": 2.0,
        "notes": "این مقادیر تقریبی هستند. بر اساس احساس انرژی و سیری خود تنظیم کنید.",
    },
    "meals": [
        {
            "meal_time": "breakfast",
            "name": "صبحانه پروتئینی",
            "description": "نان سبوس‌دار با پنیر کم‌چرب و گردو + یک لیوان چای کمرنگ",
            "calories_estimate": 380,
            "protein_g": 18.0,
            "carbs_g": 42.0,
            "fat_g": 16.0,
            "notes": None,
        },
        {
            "meal_time": "snack",
            "name": "میان‌وعده صبح",
            "description": "میوه فصلی تازه + مشتی بادام",
            "calories_estimate": 200,
            "protein_g": 5.0,
            "carbs_g": 28.0,
            "fat_g": 9.0,
            "notes": None,
        },
        {
            "meal_time": "lunch",
            "name": "ناهار متعادل",
            "description": "برنج با مرغ یا خوراک حبوبات + سالاد سبزیجات",
            "calories_estimate": 650,
            "protein_g": 30.0,
            "carbs_g": 85.0,
            "fat_g": 20.0,
            "notes": "می‌توانید به جای برنج از نان سبوس‌دار استفاده کنید.",
        },
        {
            "meal_time": "snack",
            "name": "میان‌وعده بعدازظهر",
            "description": "ماست کم‌چرب یا دوغ",
            "calories_estimate": 150,
            "protein_g": 8.0,
            "carbs_g": 15.0,
            "fat_g": 4.0,
            "notes": None,
        },
        {
            "meal_time": "dinner",
            "name": "شام سبک",
            "description": "سوپ سبزیجات یا خوراک حبوبات با نان سبوس‌دار",
            "calories_estimate": 420,
            "protein_g": 18.0,
            "carbs_g": 55.0,
            "fat_g": 14.0,
            "notes": None,
        },
    ],
    "warnings": [],
}

_MOCK_MEAL_ANALYSIS = {
    "quality_score": 7,
    "analysis_summary": (
        "این وعده غذایی از نظر تغذیه‌ای نسبتاً متعادل است. "
        "با چند تغییر کوچک می‌توانید کیفیت آن را بهبود دهید."
    ),
    "protein": "میزان پروتئین در این وعده مناسب است و به حس سیری طولانی‌تر کمک می‌کند.",
    "fiber": "افزودن سبزیجات تازه یا پخته می‌تواند مقدار فیبر را بهتر کند.",
    "sugar": "میزان قند در حد قابل قبول است. از نوشیدنی‌های شیرین در کنار این وعده اجتناب کنید.",
    "balance": "تعادل درشت‌مغذی‌ها خوب است. ترکیب کربوهیدرات، پروتئین و چربی مناسب است.",
    "portion": "حجم وعده مناسب به نظر می‌رسد. به احساس سیری خود توجه کنید.",
    "suggestions": [
        "افزودن سبزیجات تازه یا پخته به این وعده توصیه می‌شود.",
        "نوشیدن یک لیوان آب قبل از غذا به هضم بهتر کمک می‌کند.",
        "آرام غذا خوردن و جویدن کامل به احساس سیری بهتر کمک می‌کند.",
    ],
    "warnings": [],
}

_MOCK_WHAT_TO_EAT = {
    "options": [
        {
            "name": "نان و پنیر با سبزی خوردن",
            "description": "یک میان‌وعده سنتی ایرانی سریع و مقوی. پنیر منبع خوب پروتئین است.",
            "calories_estimate": 300,
            "prep_time_minutes": 5,
            "tags": ["سریع", "ایرانی", "پروتئین‌دار"],
        },
        {
            "name": "تخم‌مرغ آب‌پز با نان",
            "description": "منبع کامل پروتئین. آماده‌سازی ساده و سریع است.",
            "calories_estimate": 250,
            "prep_time_minutes": 10,
            "tags": ["پروتئین‌دار", "ساده", "مقوی"],
        },
        {
            "name": "میوه فصلی با ماست",
            "description": "سبک و مغذی. پروبیوتیک ماست برای سلامت گوارش مفید است.",
            "calories_estimate": 180,
            "prep_time_minutes": 3,
            "tags": ["سبک", "سریع", "طبیعی"],
        },
    ],
    "reasoning_summary": (
        "با توجه به وضعیت شما، این گزینه‌های ساده، سریع و متناسب با "
        "فرهنگ ایرانی پیشنهاد می‌شود. هر سه گزینه مواد مغذی لازم را دارند."
    ),
    "warnings": [],
}

_MOCK_CHAT = {
    "reply": (
        "بر اساس وضعیتت می‌تونم کمک کنم. "
        "درباره کدوم موضوع می‌خوای بیشتر بدونی — "
        "ترکیب وعده‌ها، انتخاب مواد غذایی، یا چیز دیگه‌ای؟"
    )
}

_MOCK_ADAPT_PLAN = {
    "changes": [
        "برنامه بر اساس بازخورد شما بررسی و تنظیم شد.",
        "توزیع کالری بین وعده‌ها بهینه‌سازی شد.",
        "میان‌وعده‌ها برای کاهش گرسنگی تقویت شد.",
    ],
    "updated_guidelines": {
        "calories": 2000,
        "protein_g": 75,
        "carbs_g": 250,
        "fat_g": 65,
        "fiber_g": 25,
        "water_liters": 2.0,
        "notes": "برنامه با توجه به بازخورد شما تنظیم شده است. به آرامی به تغییرات عادت کنید.",
    },
    "warnings": [],
}


class MockAIProvider(AIProvider):
    """Deterministic mock — no external calls, always returns valid structured JSON."""

    def generate_text(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        task_type = self._detect_task(messages)

        if task_type == "generate_plan":
            content = json.dumps(_MOCK_PLAN, ensure_ascii=False)
        elif task_type == "analyze_meal":
            content = json.dumps(_MOCK_MEAL_ANALYSIS, ensure_ascii=False)
        elif task_type == "what_to_eat_now":
            content = json.dumps(_MOCK_WHAT_TO_EAT, ensure_ascii=False)
        elif task_type == "adapt_plan":
            content = json.dumps(_MOCK_ADAPT_PLAN, ensure_ascii=False)
        elif task_type == "chat_message":
            content = json.dumps(_MOCK_CHAT, ensure_ascii=False)
        else:
            content = json.dumps(_MOCK_PLAN, ensure_ascii=False)

        return AIProviderResult(
            content=content,
            provider="mock",
            model="mock",
            finish_reason="stop",
            is_mock=True,
        )

    @staticmethod
    def _detect_task(messages: list[dict[str, str]]) -> str:
        for msg in messages:
            content = msg.get("content", "")
            if TASK_GENERATE_PLAN in content:
                return "generate_plan"
            if TASK_ANALYZE_MEAL in content:
                return "analyze_meal"
            if TASK_WHAT_TO_EAT in content:
                return "what_to_eat_now"
            if TASK_ADAPT_PLAN in content:
                return "adapt_plan"
            if TASK_CHAT in content:
                return "chat_message"
        return "generate_plan"
