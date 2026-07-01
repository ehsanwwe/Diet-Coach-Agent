"""
PromptBuilder: constructs provider message lists for each nutrition task.

Each method returns a PromptData containing system + user messages and a
TASK:<type> marker the MockAIProvider reads to pick the right response.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.services.mock_ai_provider import (
    TASK_ADAPT_PLAN,
    TASK_ANALYZE_MEAL,
    TASK_CHAT,
    TASK_CONTEXT_GUIDANCE,
    TASK_CRAVING_SUPPORT,
    TASK_GENERATE_PLAN,
    TASK_GENERATE_WEEK_AR,
    TASK_GENERATE_WEEK_EN,
    TASK_GENERATE_WEEK_FA,
    TASK_REPAIR_WEEK_AR,
    TASK_REPAIR_WEEK_EN,
    TASK_REPAIR_WEEK_FA,
    TASK_SLIP_RECOVERY,
    TASK_WEEKLY_REPORT,
    TASK_WHAT_TO_EAT,
)
from app.services.nutrition_memory_service import NutritionMemoryContext


_LANGUAGE_INSTRUCTIONS = {
    "fa": "Use Persian for all user-facing values. Persian is the fallback when locale is missing.",
    "en": "Use English for all user-facing values.",
    "ar": "Use Arabic for all user-facing values.",
}

# Eating-out frequency rank (higher = eats out more often)
_EATING_OUT_FREQ_RANK: dict[str, int] = {
    "never": 0, "هرگز": 0,
    "rarely": 1, "به‌ندرت": 1, "به ندرت": 1,
    "monthly": 2, "ماهانه": 2,
    "few_monthly": 3, "چند ماهی": 3,
    "sometimes": 3, "گاهی": 3,
    "weekly": 4, "هفتگی": 4,
    "few_weekly": 5, "چند_هفتگی": 5, "several_weekly": 5,
    "daily": 6, "روزانه": 6,
}


def _resolve_eating_out_freq(ctx: "NutritionMemoryContext") -> str:
    """Return the higher-priority eating-out frequency from both profile fields.

    eating_out_frequency (lifestyle profile) and restaurant_frequency (food prefs)
    both carry signal. Use whichever implies more eating out so neither is silently ignored.
    """
    rf = (ctx.restaurant_frequency or "").strip().lower()
    ef = (ctx.eating_out_frequency or "").strip().lower()
    rf_rank = _EATING_OUT_FREQ_RANK.get(rf, 0)
    ef_rank = _EATING_OUT_FREQ_RANK.get(ef, 0)
    if ef_rank > rf_rank:
        return ctx.eating_out_frequency or ""
    if rf:
        return ctx.restaurant_frequency or ""
    return ""

_CULTURE_FOOD_INSTRUCTIONS = {
    "fa": (
        "Iranian/Persian food culture rules (MANDATORY for locale=fa):\n"
        "- Breakfast must follow typical Iranian patterns: نان (سنگک/بربری/لواش) + پنیر + سبزی خوردن/خیار/گوجه; "
        "OR تخم‌مرغ (نیمرو/آب‌پز/کوکو سبزی/اشکنه); OR عدسی/حلیم/فرنی (controlled portion); "
        "OR ماست + میوه فصلی + نان.\n"
        "- «ماست چکیده با گردو» is NOT a main Iranian breakfast — use it only as a side or snack, NOT as a standalone breakfast.\n"
        "- Main meals: Use خورشت‌های ایرانی (قرمه‌سبزی، قیمه، فسنجان، مرغ ترش) with controlled برنج; "
        "کباب (کوبیده/جوجه/بختیاری) with controlled برنج یا نان; آش‌های ایرانی; "
        "خوراک حبوبات (لوبیا، عدس با پروتئین); ماهی با برنج/سبزیجات.\n"
        "- Rice and bread are ALLOWED in controlled portions — do not ban them.\n"
        "- ماست/دوغ used as side accompaniment, not main protein source.\n"
        "- DAY TITLE/SUMMARY PHRASING: Use natural Persian sentence order. "
        "NEVER write «یک روز شروع آرام» or similar noun-first constructions. "
        "Instead write: «شروع یک روز آرام»، «روزی سبک برای شروع»، «شروع آرام هفته»، or «آغاز آرام برنامه».\n"
    ),
    "ar": (
        "Arabic/Middle Eastern food culture rules (MANDATORY for locale=ar):\n"
        "- Breakfast: فول مدمس، حمص، لبنة، بيض (مسلوق/مقلي/بيض بالطماطم)، خبز عربي، "
        "جبنة بيضاء، زيتون، خضروات طازجة، شاي.\n"
        "- Main meals: دجاج مشوي، كباب، أرز بالدجاج (controlled)، شاورما (controlled)، "
        "شوربة العدس، ملوخية، مسخن، سلطة فتوش، تبولة، مجدرة.\n"
        "- Accompaniments: لبن/زبادي as side, خبز عربي in controlled portions.\n"
    ),
    "en": (
        "International food culture rules (for locale=en):\n"
        "- Use globally common healthy meals: oatmeal, eggs, lean proteins, salads, "
        "grilled meats/fish, whole grain options, vegetables, fruits.\n"
        "- Still respect all user explicit food preferences.\n"
    ),
}

_LOCALE_TASK_MAP = {
    "fa": TASK_GENERATE_WEEK_FA,
    "en": TASK_GENERATE_WEEK_EN,
    "ar": TASK_GENERATE_WEEK_AR,
}

_LOCALE_REPAIR_TASK_MAP = {
    "fa": TASK_REPAIR_WEEK_FA,
    "en": TASK_REPAIR_WEEK_EN,
    "ar": TASK_REPAIR_WEEK_AR,
}


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


def _normalize_locale(locale: str | None = None) -> str:
    if locale in {"fa", "en", "ar"}:
        return locale
    return "fa"


def _language_section(locale: str | None = None) -> str:
    effective = _normalize_locale(locale)
    return (
        "Language and locale:\n"
        f"- locale={effective}.\n"
        f"- {_LANGUAGE_INSTRUCTIONS[effective]}\n"
        "- Keep JSON keys in English exactly as requested.\n"
        "- Do not mix languages unless the user does.\n"
    )


def _professional_identity_section() -> str:
    return (
        "Role and tone:\n"
        "- You are a professional AI diet, nutrition, and healthy lifestyle companion.\n"
        "- Be scientific, calm, supportive, practical, and non-judgmental.\n"
        "- Never use body-shaming, blame, fear, shame, comparison, or moral judgment.\n"
        "- Explain in simple language; avoid unrealistic promises such as guaranteed rapid weight loss.\n"
    )


def _safety_section() -> str:
    return (
        "Safety rules:\n"
        "- Never recommend extreme diets, very-low-calorie plans, hard fasting, or total food-group elimination unless human-supervised.\n"
        "- Never recommend under 1200 kcal/day for women or under 1500 kcal/day for men.\n"
        "- Never change medication, insulin, thyroid medication, diabetes medication, hormones, or medical treatment.\n"
        "- Never act as a replacement for a physician or registered dietitian.\n"
        "- For high-risk or clinical-review users, provide conservative general guidance and advise human review.\n"
    )


def _real_life_section() -> str:
    return (
        "Cultural and real-life fit:\n"
        "- Respect the user's food culture (Iranian/Persian, Arabic, or international) based on the locale and explicit preferences.\n"
        "- Use realistic foods and household units where useful, such as plate, bowl, cup, spoon, palm, handful, slice.\n"
        "- Consider budget, time, cooking ability, work schedule, family meals, restaurant meals, and food access.\n"
        "- Treat the diet as a living plan that can be monitored and adjusted, not a static file.\n"
    )


def _nutrition_care_process_section() -> str:
    return (
        "Nutrition-care process to follow internally:\n"
        "1. Assessment: use body data, medical data, lifestyle, diet history, preferences, behavior, sleep, stress, activity, budget, and access.\n"
        "2. Diagnosis/problem identification: identify likely root patterns such as low protein, low fiber, high simple sugar, irregular meals, skipped breakfast, night eating, emotional eating, restaurant dependency, low hydration, low activity, sleep-related cravings, stress overeating, excessive restriction, unrealistic goals, or medical red flags.\n"
        "3. Intervention: suggest practical meals, substitutions, behavior changes, small goals, and safe nutrition guidance.\n"
        "4. Monitoring and adjustment: use weight, waist, hunger, energy, sleep, stress, adherence, symptoms, labs if available, and progress history to adjust.\n"
        "When the JSON contract includes assessment_summary, nutrition_diagnosis, intervention_summary, or monitoring_notes, fill them briefly.\n"
    )


def _json_output_section() -> str:
    return (
        "Output format:\n"
        "- Return valid JSON only. No markdown and no text outside JSON.\n"
        "- Preserve the requested JSON keys exactly.\n"
        "- User-facing string values must follow the locale instruction.\n"
    )


def _memory_json(ctx: NutritionMemoryContext) -> str:
    return json.dumps(ctx.to_prompt_memory(), ensure_ascii=False, indent=2)


def _dislike_constraint(ctx: NutritionMemoryContext) -> str:
    if not ctx.disliked_foods:
        return ""
    disliked_str = ", ".join(ctx.disliked_foods[:10])
    return (
        f"\nDISLIKED FOODS — HARD CONSTRAINT: Never suggest or mention these foods: {disliked_str}. "
        "Replace any disliked food with a culturally similar alternative the user has not disliked."
    )


def _memory_instruction() -> str:
    return (
        "Memory/context use:\n"
        "- Use grouped memory sections as compact context, not as text to repeat to the user.\n"
        "- Stable user profile, medical/safety context, lifestyle, preferences, behavior patterns, recent progress/check-ins, and active plan context should guide decisions.\n"
        "- Missing/unknown data should trigger cautious assumptions or one concise clarifying question when needed.\n"
    )


def _base_system(task_tag: str, ctx: NutritionMemoryContext, locale: str | None = None) -> str:
    return "\n".join(
        [
            _professional_identity_section(),
            _safety_section(),
            _real_life_section(),
            _nutrition_care_process_section(),
            _language_section(locale),
            _memory_instruction(),
            _json_output_section(),
            task_tag,
            _safety_note(ctx),
        ]
    )


def _safety_note(ctx: NutritionMemoryContext) -> str:
    if ctx.clinical_review_required:
        return (
            "User risk note: clinical_review_required. Provide general wellness guidance only; "
            "do not produce disease-specific prescriptions or strict diet plans."
        )
    if ctx.risk_level == "high":
        return (
            "User risk note: high risk. Keep guidance conservative, avoid aggressive targets, "
            "and recommend human review."
        )
    return "User risk note: low or medium risk. Stay within normal safety rules."


def for_generate_plan(ctx: NutritionMemoryContext) -> PromptData:
    system = _base_system(TASK_GENERATE_PLAN, ctx)
    user_ctx = _memory_json(ctx)
    user = (
        f"User profile:\n{user_ctx}\n\n"
        + _dislike_constraint(ctx)
        + "\nGenerate a practical initial nutrition plan only if the profile is sufficiently complete.\n"
        "Do not create a complete strict diet based only on height, weight, and goal.\n"
        "The plan must include realistic meals/snacks with household portions and EXPLICIT QUANTITIES in both description and notes (e.g. '۲ کف دست نان + ۳۰ گرم پنیر', '۷ قاشق برنج + ۴ قاشق خورش'), alternatives, a quick busy-day option, outside-home/restaurant flexibility where possible, a simple scientific reason.\n"
        "NEVER produce a meal with only a food name — every meal must state measurable household amounts.\n"
        "Do NOT include a 'consult your doctor before starting' warning — the system injects that automatically.\n"
        "Prefer Iranian/Persian foods when culturally appropriate and allow substitutions if the user dislikes or lacks a food.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "title": "...",\n'
        '  "summary": "...",\n'
        '  "assessment_summary": "...",\n'
        '  "nutrition_diagnosis": "...",\n'
        '  "intervention_summary": "...",\n'
        '  "monitoring_notes": "...",\n'
        '  "daily_guidelines": {"calories": int, "protein_g": float, "carbs_g": float, "fat_g": float, "fiber_g": float, "water_liters": float, "notes": "..."},\n'
        '  "meals": [{"meal_time": "breakfast|lunch|dinner|snack", "name": "...", "description": "...", "calories_estimate": int, "protein_g": float, "carbs_g": float, "fat_g": float, "notes": "..."}],\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="generate_plan", system=system, user=user)


def for_analyze_meal(
    ctx: NutritionMemoryContext,
    meal_text: str,
    meal_time: str,
    meal_context: str | None,
    extra_context: dict | None = None,
) -> PromptData:
    system = _base_system(TASK_ANALYZE_MEAL, ctx)
    user_ctx = _memory_json(ctx)
    extra = f"\nAdditional context: {meal_context}" if meal_context else ""
    structured_extra = (
        "\nStructured daily context: " + json.dumps(extra_context, ensure_ascii=False)
        if extra_context
        else ""
    )
    user = (
        f"User profile: {user_ctx}\n\n"
        f"Meal text: {meal_text}\n"
        f"Meal time: {meal_time}{extra}{structured_extra}\n\n"
        "Analyze the meal without punishment or extreme compensation advice.\n"
        "Cover likely meal identification, uncertainties, protein quality, fiber/vegetable quality, carbohydrate quality, fat quality, simple sugar quality, portion/volume assessment, satiety assessment, likely effect on the user's goal, one small correction, and a next-meal suggestion.\n"
        "Never suggest fasting, detox, purging, extreme exercise, skipping the next meal, or harsh compensation after overeating.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "quality_score": int,\n'
        '  "analysis_summary": "...",\n'
        '  "likely_meal": "...",\n'
        '  "uncertainties": ["..."],\n'
        '  "assessment_summary": "...",\n'
        '  "nutrition_diagnosis": "...",\n'
        '  "intervention_summary": "...",\n'
        '  "monitoring_notes": "...",\n'
        '  "protein": "...",\n'
        '  "fiber": "...",\n'
        '  "sugar": "...",\n'
        '  "balance": "...",\n'
        '  "portion": "...",\n'
        '  "protein_quality": "...",\n'
        '  "fiber_vegetable_quality": "...",\n'
        '  "carbohydrate_quality": "...",\n'
        '  "fat_quality": "...",\n'
        '  "simple_sugar_quality": "...",\n'
        '  "portion_volume_assessment": "...",\n'
        '  "satiety_assessment": "...",\n'
        '  "likely_goal_effect": "...",\n'
        '  "one_small_correction": "...",\n'
        '  "next_meal_suggestion": "...",\n'
        '  "no_extreme_compensation_note": "...",\n'
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
    current_context: dict | None = None,
) -> PromptData:
    system = _base_system(TASK_WHAT_TO_EAT, ctx)
    user_ctx = _memory_json(ctx)
    foods_str = ", ".join(available_foods) if available_foods else "typical Iranian/Persian home foods"
    time_str = f"{time_available_minutes} minutes" if time_available_minutes else "unknown"
    extra = f"\nContext/place/last meal if provided: {meal_context}" if meal_context else ""
    structured = (
        "\nStructured current context: " + json.dumps(current_context, ensure_ascii=False)
        if current_context
        else ""
    )
    user = (
        f"User profile: {user_ctx}\n\n"
        + _dislike_constraint(ctx)
        + f"\nAvailable foods: {foods_str}\n"
        f"Hunger level label: {hunger_level}. Interpret hunger on a 1-10 scale when possible.\n"
        f"Time constraint: {time_str}{extra}{structured}\n\n"
        "Use current place/context (home, work, restaurant, travel), available foods, last meal time, current goal, hunger 1-10, time constraints, cooking ability/access, and medical constraints.\n"
        "If key data is missing, either ask concise clarifying questions in reasoning/warnings or provide safe low-risk options with stated assumptions.\n"
        "Return 2-3 practical options: best aligned with goal, fastest option, and a more flexible option when appropriate. Each option should include household portions, why it fits the goal, substitutions, and safety note when relevant.\n"
        "For high-risk or clinical-review users, keep options conservative and avoid aggressive disease-specific advice.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "assessment_summary": "...",\n'
        '  "intervention_summary": "...",\n'
        '  "monitoring_notes": "...",\n'
        '  "options": [{"name": "...", "description": "...", "calories_estimate": int, "prep_time_minutes": int, "tags": ["best_aligned|fastest|flexible"], "option_type": "best_goal_aligned|fastest|flexible|general", "household_portions": "...", "why_it_fits_goal": "...", "safety_note": null, "substitutions": ["..."]}],\n'
        '  "best_goal_aligned_option": {"name": "...", "description": "...", "option_type": "best_goal_aligned"},\n'
        '  "fastest_option": {"name": "...", "description": "...", "option_type": "fastest"},\n'
        '  "flexible_option": {"name": "...", "description": "...", "option_type": "flexible"},\n'
        '  "reasoning_summary": "...",\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="what_to_eat_now", system=system, user=user)


def for_craving_support(ctx: NutritionMemoryContext, request_context: dict) -> PromptData:
    system = _base_system(TASK_CRAVING_SUPPORT, ctx)
    user = (
        f"User memory/context:\n{_memory_json(ctx)}\n\n"
        f"Craving support request:\n{json.dumps(request_context, ensure_ascii=False)}\n\n"
        "Provide calm craving support. Normalize the experience without shame.\n"
        "Distinguish physical hunger from craving when possible.\n"
        "Identify likely triggers such as sleep, stress, long gaps between meals, low protein, restriction, emotion, habit, or environment.\n"
        "Give immediate practical options, one better-aligned choice, one flexible choice, and one prevention tip.\n"
        "Avoid all-or-nothing language, severe restriction, fasting, detox, purging, or exercise compensation.\n"
        "Do not ban rice, bread, sweets, or restaurant foods absolutely; portion, balance, and context matter.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "calming_message": "...",\n'
        '  "likely_triggers": ["..."],\n'
        '  "hunger_vs_craving_assessment": "...",\n'
        '  "immediate_options": [{"title": "...", "description": "...", "household_portions": "...", "why_it_helps": "...", "substitutions": ["..."]}],\n'
        '  "better_choice": {"title": "...", "description": "...", "household_portions": "...", "why_it_helps": "..."},\n'
        '  "flexible_choice": {"title": "...", "description": "...", "household_portions": "...", "why_it_helps": "..."},\n'
        '  "prevention_tip": "...",\n'
        '  "follow_up_question": "...",\n'
        '  "safety_notes": [],\n'
        '  "requires_human_review": false\n'
        "}"
    )
    return PromptData(task_type="craving_support", system=system, user=user)


def for_slip_recovery(ctx: NutritionMemoryContext, request_context: dict) -> PromptData:
    system = _base_system(TASK_SLIP_RECOVERY, ctx)
    user = (
        f"User memory/context:\n{_memory_json(ctx)}\n\n"
        f"Slip recovery request:\n{json.dumps(request_context, ensure_ascii=False)}\n\n"
        "Follow this 6-step slip recovery protocol:\n"
        "1. Calm the user.\n"
        "2. Say this is useful data, not a failure.\n"
        "3. Ask what happened before it using concise trigger questions.\n"
        "4. Detect the likely pattern.\n"
        "5. Suggest one small adjustment.\n"
        "6. Return to the next meal or tomorrow without punishment.\n"
        "Never say the diet is ruined. Never suggest fasting, detox, purging, skipping meals, extreme exercise, or extreme restriction after overeating.\n"
        "Avoid shame, blame, all-or-nothing language, and the phrase 'you failed'.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "calming_message": "...",\n'
        '  "data_not_failure_message": "...",\n'
        '  "likely_trigger_questions": ["..."],\n'
        '  "pattern_hypothesis": "...",\n'
        '  "one_small_adjustment": "...",\n'
        '  "next_meal_plan": "...",\n'
        '  "tomorrow_reset_note": "...",\n'
        '  "no_extreme_compensation_note": "...",\n'
        '  "safety_notes": [],\n'
        '  "requires_human_review": false\n'
        "}"
    )
    return PromptData(task_type="slip_recovery", system=system, user=user)


def for_context_guidance(ctx: NutritionMemoryContext, request_context: dict) -> PromptData:
    system = _base_system(TASK_CONTEXT_GUIDANCE, ctx)
    user = (
        f"User memory/context:\n{_memory_json(ctx)}\n\n"
        f"Restaurant/party/travel request:\n{json.dumps(request_context, ensure_ascii=False)}\n\n"
        "Give restaurant, party, travel, or work eating guidance with no absolute bans.\n"
        "Suggest the best available choice and a flexible choice.\n"
        "Use portion strategy, plate balance, suitable drink advice, dessert/sweets strategy, and next-meal adjustment without punishment.\n"
        "Balance protein, vegetables/fiber, controlled carbohydrate, and realistic Iranian/Persian foods when suitable.\n"
        "If the user chooses a high-calorie option, avoid shame and give a practical portion/context strategy.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "best_available_choice": "...",\n'
        '  "flexible_choice": "...",\n'
        '  "portion_strategy": "...",\n'
        '  "plate_balance_tip": "...",\n'
        '  "drink_tip": "...",\n'
        '  "dessert_or_snack_strategy": "...",\n'
        '  "if_user_chooses_high_calorie_option": "...",\n'
        '  "next_meal_adjustment": "...",\n'
        '  "safety_notes": [],\n'
        '  "requires_human_review": false\n'
        "}"
    )
    return PromptData(task_type="context_guidance", system=system, user=user)


def for_chat_message(
    ctx: NutritionMemoryContext,
    user_message: str,
    history: list[dict[str, str]],
) -> PromptData:
    user_ctx_json = _memory_json(ctx)
    restaurant_freq = _resolve_eating_out_freq(ctx)
    restaurant_hint = (
        f"\n- User eats out {restaurant_freq}. Proactively mention restaurant strategy when the topic "
        "arises or when it is relevant to the user's current question."
        if restaurant_freq and restaurant_freq.lower() not in ("never", "")
        else ""
    )

    system = (
        _base_system(TASK_CHAT, ctx)
        + "\nChat behavior:\n"
        "- Use profile and conversation memory, but do not expose system internals.\n"
        "- Ask one concise follow-up question when key nutrition data is missing and a safe answer needs it.\n"
        "- Do not over-question; give practical guidance when safe.\n"
        "- Mention human review when risk context requires it.\n"
        "- Match food examples to locale: Persian patterns for fa users, Arabic patterns for ar users, international for en.\n"
        "- Never repeat the same medical warning sentence twice in a single response.\n"
        f"{restaurant_hint}"
        "\n- If the user asks about flexibility, cravings, or 'getting tired of the diet', proactively introduce the concept of "
        "controlled cheating (چیتینگ کنترل‌شده / Controlled Cheating / وجبة مرنة محسوبة) as planned flexibility to improve adherence.\n"
        "- Answers about restaurant, gluten-free, or meal alternatives must reflect the user's current goal, budget, allergies, culture, and eating-out frequency.\n"
    )

    clean_history: list[dict[str, str]] = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-6:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    user = (
        f"User profile context: {user_ctx_json}\n\n"
        + _dislike_constraint(ctx)
        + f"\nUser message: {user_message}\n\n"
        "Give a concise, natural nutrition-companion response. Return JSON exactly as:\n"
        '{"reply": "...", "assessment_summary": "...", "monitoring_notes": "..."}'
    )
    return PromptData(
        task_type="chat_message",
        system=system,
        user=user,
        history_messages=clean_history,
    )


def _controlled_cheating_section(ctx: NutritionMemoryContext, locale: str) -> str:
    if locale == "fa":
        section_name = "«چیتینگ کنترل‌شده»"
        title_str = "چیتینگ کنترل‌شده"
    elif locale == "ar":
        section_name = "«وجبة مرنة محسوبة»"
        title_str = "وجبة مرنة محسوبة"
    else:
        section_name = '"Controlled Cheating"'
        title_str = "Controlled Cheating"

    goal = ctx.goal_type or "general_health_companion"
    safe_goals = {
        "diabetes_support", "kidney_disease", "pregnancy_breastfeeding_caution",
        "eating_disorder_history", "clinical_review_required",
    }
    is_safe = goal in safe_goals or ctx.clinical_review_required or ctx.risk_level in ("high", "clinical_review_required")
    binge = ctx.binge_history

    if is_safe or binge:
        cheat_guidance = (
            "Keep it CONSERVATIVE: a small treat within safe limits. "
            "No full cheat day. Avoid allergens and medically contraindicated items. "
            "Frame as a small enjoyable moment, not a diet break."
        )
    elif goal in ("muscle_gain", "weight_gain"):
        cheat_guidance = (
            "Higher-carb refeed meal: larger rice/bread serving with protein-rich items. "
            "Include specific portions. Frame as planned refeed for muscle recovery, not a binge."
        )
    elif goal == "weight_loss":
        cheat_guidance = (
            "ONE cheat MEAL (not a full cheat day): user's favourite reasonable food with a portion cap. "
            "Include next-meal guidance to return to plan. No guilt, no extreme compensation."
        )
    else:
        cheat_guidance = (
            "One flexible meal: the user's favourite food with household-portion guidance. "
            "Enjoy without guilt. Return to plan at the next meal."
        )

    return (
        f"CONTROLLED CHEATING — MANDATORY FOR EVERY 7-DAY PLAN:\n"
        f"- Choose exactly ONE day: day 5 or 6 (never day 1).\n"
        f"- On that day: set cheat_meal_guidance to a {section_name} description.\n"
        f"- ALSO add a MEAL ENTRY in the meals array for that day:\n"
        f'  meal_slot="controlled_cheating", meal_type="controlled_cheating", title="{title_str}",\n'
        f"  description=(include: exact timing, portion guidance, 2-3 allowed examples, next-meal balancing rule),\n"
        f"  time_window_start='20:00', time_window_end='22:00', meal_order=9.\n"
        f"- {cheat_guidance}\n"
        "- Description must state: این یک وعده کنترل‌شده است، نه پرخوری. وعده بعدی به برنامه عادی برمی‌گردد.\n"
        "- Do NOT claim this 'shocks metabolism' or make unsupported metabolic claims.\n"
        "- NEVER include allergen foods or medically unsafe items.\n"
        "- Frame professionally: planned flexibility improves adherence and reduces psychological burnout.\n"
    )


def _high_budget_iranian_premium_section(ctx: NutritionMemoryContext, locale: str) -> str:
    """Extra instructions for fa+likes_iranian_food+premium users to avoid cheap-meal drift."""
    if locale != "fa" or not ctx.likes_iranian_food or ctx.budget_tier != "premium":
        return ""
    return (
        "HIGH-BUDGET IRANIAN MEAL QUALITY — MANDATORY OVERRIDE:\n"
        "User has food_budget=high + likes_iranian_food=True + locale=fa. "
        "The plan MUST reflect Iranian premium home-cooking standards. HARD RULES:\n"
        "- Include at least 4 of these premium protein mains across the 7 days:\n"
        "  زرشک‌پلو با مرغ، پلو مرغ / چلو مرغ، جوجه کباب با برنج کنترل‌شده،\n"
        "  سبزی‌پلو با ماهی، خورشت قیمه یا قورمه‌سبزی با گوشت یا مرغ،\n"
        "  کباب تابه‌ای کم‌چرب، خوراک مرغ یا گوشت با سیب‌زمینی یا سبزیجات.\n"
        "- MINIMUM 3 lunches must include PREMIUM PROTEIN: chicken, fish, lean meat, or kebab.\n"
        "- Lentil/bean soup as PRIMARY main meal: MAXIMUM 2 out of 7 days total. "
        "They may appear as dinner or side, not as the dominant main for most days.\n"
        "- Never plan برنج ساده as a standalone meal — it must accompany خورشت or کباب with stated quantity.\n"
        "- Breakfast: include at least 2 days of تخم‌مرغ (نیمرو/آب‌پز/کوکو) or پنیر+گردو+نان سنگک or ماست پرچرب+عسل.\n"
        "- shopping_notes and budget_guidance must reflect high-budget premium ingredients "
        "(مرغ تازه، ماهی، گوشت، زرشک، خلال بادام، روغن زیتون), NOT economy staples.\n"
        "VIOLATION CHECK: After generating the plan, if more than 2 lunches are عدسی/آش/لوبیا/سوپ ساده, REPLACE them.\n"
    )


def _restaurant_guidance_section(ctx: NutritionMemoryContext, locale: str) -> str:
    freq = _resolve_eating_out_freq(ctx)
    if freq.lower() in ("never", ""):
        return ""

    if locale == "fa":
        examples = (
            "رستوران ایرانی: جوجه کباب با نان (بدون برنج یا برنج محدود) + سالاد؛ "
            "کباب کوبیده یک سیخ با نان سنگک؛ آبگوشت بدون نان اضافه؛ "
            "ماهی کبابی با سبزی؛ دوری‌کردن از غذاهای سرخ‌کردنی، سس‌های پرکالری، دوغ شیرین."
        )
    elif locale == "ar":
        examples = (
            "مطعم عربي: دجاج مشوي بدون صلصة كثيرة + سلطة؛ شاورما دجاج (بدون صلصة ثقيلة)؛ "
            "شوربة عدس + خبز محدود؛ تجنب المقليات والمشروبات المحلاة."
        )
    else:
        examples = (
            "Restaurant strategy: grilled protein + salad; avoid heavy sauces, fried items, "
            "sugary drinks; choose grilled over fried; share dessert or skip."
        )

    return (
        f"RESTAURANT / EATING-OUT GUIDANCE — REQUIRED (user eats out {freq}):\n"
        "- Include restaurant_party_travel_guidance field on at least 2 days of the 7-day plan.\n"
        "- Include: best available restaurant choice, what to avoid, how to balance next meal after eating out.\n"
        f"- Practical locale-specific examples: {examples}\n"
        "- Do NOT say 'never eat restaurant food'. Provide practical, non-shaming strategy.\n"
        "- If user eats out on a cheat day, link the guidance to the controlled cheating block.\n"
    )


def _anti_repetition_section() -> str:
    return (
        "ANTI-REPETITION RULE — MANDATORY:\n"
        "- Do NOT use the same complete main meal (same name) more than twice across the 7 days.\n"
        "- Do NOT place the same main protein on adjacent days' lunch AND dinner.\n"
        "- Rotate proteins: chicken, fish/tuna, legumes (lentils, beans, chickpeas), eggs (if allowed), red meat (max once per week).\n"
        "- Rotate main carbs across days: rice, bread, potato, rice noodles, mixed polo — vary them.\n"
        "- Exception: user may prefer simple repetition — only repeat if user explicitly asked for it or has very low cooking ability.\n"
    )


def _gluten_free_alternatives_section(ctx: NutritionMemoryContext) -> str:
    allergies_lower = [a.lower() for a in ctx.allergies]
    has_gluten = any(
        "gluten" in a or "wheat" in a or "گندم" in a or "گلوتن" in a
        for a in allergies_lower
    )
    if not has_gluten:
        return ""
    disliked_text = " ".join(ctx.disliked_foods).lower()
    rice_disliked = "برنج" in disliked_text or "rice" in disliked_text
    lentil_disliked = "عدس" in disliked_text or "lentil" in disliked_text
    budget = ctx.budget_tier if ctx.budget_tier != "unknown" else "standard"
    if rice_disliked:
        alternatives = (
            "rotate between: سیب‌زمینی/potato, نان ذرت بدون گلوتن/certified gluten-free corn bread, "
            "quinoa or buckwheat if appropriate and available, certified gluten-free oats, and other corn-based options. "
            "Do not suggest rice-derived bread, noodles, flour, or grains because rice is disliked."
        )
    elif budget == "economic":
        alternatives = (
            "rotate between: برنج (rice), سیب‌زمینی (potato), نان برنجی/ذرت (rice/corn bread if available), "
            + ("bean soup and chickpea soup. " if lentil_disliked else "lentil soup, bean soup, chickpea soup. ")
            + "Avoid repeating one staple every single day."
        )
    else:
        alternatives = (
            "rotate between: برنج/rice, سیب‌زمینی/potato, رشته برنجی/rice noodles, نان برنجی/ذرت/rice-corn bread, "
            "quinoa or buckwheat (if available), certified GF oats, corn-based options. "
            "Do NOT default to only lentils and plain rice every day."
        )
    return (
        "GLUTEN-FREE ALTERNATIVES — MANDATORY (user has gluten restriction):\n"
        "- Every meal must be completely gluten-free.\n"
        "- Never include normal wheat bread (سنگک، بربری، لواش یا تافتون معمولی), wheat flour, regular pasta/noodles, barley unless certified gluten-free, rye, couscous, رشته or آش رشته.\n"
        f"- For bread/grain/pasta slots: {alternatives}\n"
        "- When Iranian breakfast normally uses bread, actively specify نان بدون گلوتن or a practical safe gluten-free bread/grain alternative; never merely remove bread.\n"
        "- Increase variety of proteins alongside grains: fish, chicken, legumes — ROTATED across days.\n"
        "- Never use wheat, barley, rye, regular pasta, couscous, or standard bread.\n"
        "- Restaurant guidance must ask about wheat/flour in marinades, sauces, soups and fried coatings; prefer safe grilled protein with an allowed gluten-free side and salad, avoid breaded foods unless confirmed gluten-free, and mention cross-contamination calmly.\n"
    )


def for_generate_week_plan(
    ctx: NutritionMemoryContext,
    locale: str,
    extra_context: str | None = None,
) -> PromptData:
    effective_locale = _normalize_locale(locale)
    task_tag = _LOCALE_TASK_MAP.get(effective_locale, TASK_GENERATE_WEEK_FA)
    system = _base_system(task_tag, ctx, locale=effective_locale)

    user_ctx = _memory_json(ctx)

    # Build allergen constraint section
    allergen_lines: list[str] = []
    _ALLERGEN_VARIANTS_PROMPT: dict[str, list[str]] = {
        "egg": ["egg", "eggs", "omelet", "omelette", "تخم مرغ", "تخم‌مرغ", "نیمرو", "املت", "آملت", "عجة", "بيض", "بيضة"],
        "gluten": ["wheat", "gluten", "گندم"],
        "peanut": ["peanut", "بادام زمینی"],
        "lactose": ["milk", "dairy", "شیر", "لبنیات"],
        "fish": ["fish", "salmon", "ماهی", "سالمون"],
        "shellfish": ["shrimp", "crab", "میگو", "خرچنگ"],
        "soy": ["soy", "tofu", "سویا"],
    }
    if ctx.allergies:
        allergen_lines.append("HARD CONSTRAINTS — CRITICAL — DO NOT VIOLATE:")
        for allergen in ctx.allergies:
            a_lower = allergen.lower()
            matched_variants: list[str] = []
            for key, variants in _ALLERGEN_VARIANTS_PROMPT.items():
                if a_lower in key or any(a_lower in v.lower() for v in variants):
                    matched_variants = variants
                    break
            if matched_variants:
                allergen_lines.append(f"- User has '{allergen}' allergy. NEVER include: {', '.join(matched_variants)}")
            else:
                allergen_lines.append(f"- User has '{allergen}' allergy. NEVER include any form of '{allergen}' in any meal.")
    if ctx.disliked_foods:
        disliked_str = ", ".join(ctx.disliked_foods[:10])
        allergen_lines.append(
            f"DISLIKED FOODS — HARD PERSONALIZATION CONSTRAINT (same priority as allergy):\n"
            f"NEVER include these foods ANYWHERE in the JSON: {disliked_str}\n"
            "This applies to every field: title, description, food_items, alternatives, "
            "shopping_notes, cheat_meal_guidance, restaurant_guidance, and notes.\n"
            "If a common Iranian dish is disliked, replace it with a culturally similar accepted dish.\n"
            "Before returning JSON, mentally scan every string field and remove any disliked food."
        )

    allergen_section = "\n".join(allergen_lines) if allergen_lines else ""

    # Budget tier constraints
    budget_tier = ctx.budget_tier if ctx.budget_tier != "unknown" else "standard"
    if budget_tier == "economic":
        budget_section = (
            "BUDGET CONSTRAINT — CRITICAL:\n"
            "User has an ECONOMIC (low-cost) budget. HARD RULES:\n"
            "- Use only affordable staples: legumes (lentils, beans, chickpeas), eggs (if not allergic), "
            "chicken in controlled portions, local fish (if affordable), plain yogurt/cheese (if allowed), "
            "seasonal vegetables and fruits, rice/bread/potatoes in controlled amounts.\n"
            "- NEVER include in any meal: salmon, quinoa, avocado, blueberry/berries as staple, "
            "imported nuts, protein powder, steak, shrimp, lobster, caviar, exotic superfoods, "
            "premium supplements, costly restaurant meals.\n"
            "- Alternatives must also be economic and affordable.\n"
            "- Cheat meal must be low-cost and realistic.\n"
            "- Restaurant guidance must suggest lower-cost healthy options only.\n"
            "- Design for batch cooking: reuse affordable ingredients across the week.\n"
            "- Include budget_tier='economic', budget_guidance (explaining the economic approach), "
            "and shopping_notes (affordable shopping list) in each day.\n"
        )
    elif budget_tier == "premium":
        budget_section = (
            "BUDGET CONSTRAINT:\n"
            "User has a PREMIUM budget. Wider food variety is acceptable:\n"
            "- Allow more fish varieties, lean meats, specialty grains, premium dairy, varied nuts/seeds (if allowed).\n"
            "- Keep the plan medically safe and goal-aligned — do not add expensive foods unless nutritionally useful.\n"
            "- Include budget_tier='premium', budget_guidance, and shopping_notes in each day.\n"
        )
    else:
        budget_section = (
            "BUDGET CONSTRAINT:\n"
            "User has a STANDARD budget. Use balanced common foods:\n"
            "- Allow moderate variety: chicken, fish occasionally, dairy (if allowed), legumes, eggs (if allowed), seasonal produce.\n"
            "- Avoid making every meal premium. Alternatives should stay normal-cost.\n"
            "- Include budget_tier='standard', budget_guidance, and shopping_notes in each day.\n"
        )

    # Determine exercise days
    exercise_days = ctx.exercise_days_per_week or 0
    training_note = (
        f"User exercises {exercise_days} day(s) per week. Mark those as day_type=training_day and include pre_workout and post_workout meal slots."
        if exercise_days > 0
        else "User does not exercise regularly. Use day_type=rest_day for all days."
    )

    culture_section = _CULTURE_FOOD_INSTRUCTIONS.get(effective_locale, _CULTURE_FOOD_INSTRUCTIONS["en"])
    cheating_section = _controlled_cheating_section(ctx, effective_locale)
    restaurant_section = _restaurant_guidance_section(ctx, effective_locale)
    anti_repetition_section = _anti_repetition_section()
    gluten_section = _gluten_free_alternatives_section(ctx)
    iranian_premium_section = _high_budget_iranian_premium_section(ctx, effective_locale)

    user = (
        f"User profile:\n{user_ctx}\n\n"
        + (f"{allergen_section}\n\n" if allergen_section else "")
        + (f"{gluten_section}\n" if gluten_section else "")
        + f"{budget_section}\n"
        + (f"{iranian_premium_section}\n" if iranian_premium_section else "")
        + f"{culture_section}\n"
        + f"{anti_repetition_section}\n"
        + f"{cheating_section}\n"
        + (f"{restaurant_section}\n" if restaurant_section else "")
        + f"Generate exactly 7 days of meal plan in locale={effective_locale}.\n"
        + f"{training_note}\n"
        + "Use household portions. Include time windows for each meal. Provide calories and macros.\n"
        + "PORTION GUIDANCE RULES — MANDATORY for every meal's portion_guidance AND description fields:\n"
        + "- NEVER produce a meal with only a food name and no quantity — every component must have an amount.\n"
        + "- NEVER use vague phrases in either field: کنترل‌شده، مقدار مناسب، کمی، به مقدار کافی، متعادل، یک وعده.\n"
        + "- The 'description' field must also contain explicit quantities for every food component, "
        + "written as a readable list joined with '+'. Examples:\n"
        + "  صبحانه: '۲ کف دست نان سنگک + ۳۰ گرم پنیر کم‌چرب + ۲ عدد گردو + ۱ فنجان چای'\n"
        + "  ناهار (برنج+خورشت): '۷ قاشق غذاخوری برنج پخته + ۴ قاشق قورمه‌سبزی + ۱ کاسه سالاد'\n"
        + "  ناهار (ماکارانی): '۱.۵ لیوان ماکارانی پخته + ۱ کف دست گوشت چرخ‌کرده + ۱ بشقاب سالاد'\n"
        + "  شام (عدسی): '۱ کاسه متوسط عدسی + ۳ قاشق ماست کم‌چرب + سبزی خوردن'\n"
        + "  میان‌وعده: '۱ عدد سیب + ۱۰ عدد بادام'\n"
        + "- Bread: '۲ کف دست نان [type]' — NEVER only 'برش نان' without کف دست.\n"
        + "- Rice + stew (قرمه‌سبزی، قیمه، فسنجان …): '۷ قاشق غذاخوری برنج پخته + ۴ قاشق خورش [name]'.\n"
        + "- Mixed polo (لوبیاپلو، عدس‌پلو، سبزی‌پلو، استانبولی): '۸ قاشق غذاخوری [polo name]'.\n"
        + "- Chicken/meat: '۱ کف دست مرغ پخته، حدود ۱۲۰ گرم'.\n"
        + "- Yogurt: '۱ کاسه کوچک ماست، حدود ۱۵۰ گرم'. Cheese: '۳۰ گرم پنیر (اندازه قوطی کبریت)'.\n"
        + "- Fruit: '۱ عدد میوه متوسط (نام میوه)'. Salad/vegetables: '۱ کاسه متوسط'. Soup: '۱ کاسه متوسط'.\n"
        + "- EVERY portion_guidance must be a specific, measurable household unit — no exceptions.\n"
        + "WARNINGS RULE: Do NOT add a 'consult your doctor before starting' warning — the system "
        + "injects the canonical medical-consultation warning automatically for clinical users. "
        + "Include warnings only for genuine day-specific dietary notes (e.g. salt restriction, allergen caution).\n"
        + "Meal order (use only relevant slots):\n"
        + "1. breakfast (07:00-09:00)\n"
        + "2. morning_snack (10:30-11:00)\n"
        + "3. lunch (12:30-14:00)\n"
        + "4. pre_workout (ONLY on training days, 30-60 min before workout)\n"
        + "5. post_workout (ONLY on training days, within 30 min after workout)\n"
        + "6. afternoon_snack (15:30-16:30)\n"
        + "7. dinner (19:00-20:30)\n"
        + "8. optional_evening_snack (ONLY if clinically appropriate)\n\n"
        + "Return JSON only:\n"
        + "{\n"
        + f'  "locale": "{effective_locale}",\n'
        + '  "days": [\n'
        + '    {\n'
        + '      "day_index": 1,\n'
        + '      "title": "...",\n'
        + '      "summary": "...",\n'
        + '      "day_type": "training_day|rest_day|light_activity_day",\n'
        + '      "diet_type": "...",\n'
        + '      "difficulty_level": "beginner|intermediate|advanced",\n'
        + '      "daily_calories": 1800,\n'
        + '      "daily_macros": {"protein_g": 90, "carbs_g": 220, "fat_g": 60, "fiber_g": 25},\n'
        + '      "hydration_goal": "...",\n'
        + '      "hydration_plan": "...",\n'
        + '      "training_guidance": "...",\n'
        + '      "sleep_wake_guidance": "...",\n'
        + '      "cheat_meal_guidance": "...",\n'
        + '      "budget_tier": "economic|standard|premium",\n'
        + '      "budget_guidance": "...",\n'
        + '      "shopping_notes": "...",\n'
        + '      "medical_warnings": [],\n'
        + '      "notes": "...",\n'
        + '      "warnings": [],\n'
        + '      "meals": [\n'
        + '        {\n'
        + '          "meal_slot": "breakfast",\n'
        + '          "meal_type": "breakfast",\n'
        + '          "meal_order": 1,\n'
        + '          "title": "...",\n'
        + '          "description": "...",\n'
        + '          "time_window_start": "07:00",\n'
        + '          "time_window_end": "09:00",\n'
        + '          "calories_estimate": 400,\n'
        + '          "protein_g": 20,\n'
        + '          "carbs_g": 50,\n'
        + '          "fat_g": 12,\n'
        + '          "portion_guidance": "...",\n'
        + '          "food_items": [{"name": "...", "amount": "2", "unit": "برش", "calories_estimate": 160}],\n'
        + '          "alternatives": ["..."],\n'
        + '          "workout_relation": "none",\n'
        + '          "drink_guidance": "...",\n'
        + '          "preparation_notes": null\n'
        + '        }\n'
        + '      ]\n'
        + '    }\n'
        + '  ]\n'
        + "}"
    )
    if extra_context:
        user = f"Special instruction for this request: {extra_context}\n\n" + user
    return PromptData(task_type=f"generate_week_{effective_locale}", system=system, user=user)


def for_repair_week_plan(
    ctx: NutritionMemoryContext,
    locale: str,
    original_plan: dict,
    issues: list[object],
) -> PromptData:
    """Build a precise LLM repair request from deterministic review findings."""
    effective_locale = _normalize_locale(locale)
    task_type = f"repair_week_{effective_locale}"
    issue_data = [
        {
            "code": getattr(issue, "code", "unknown"),
            "severity": getattr(issue, "severity", "error"),
            "path": getattr(issue, "path", "$"),
            "message": getattr(issue, "message", str(issue)),
            "details": getattr(issue, "details", {}),
        }
        for issue in issues
    ]
    gluten_section = _gluten_free_alternatives_section(ctx)
    system = _base_system(_LOCALE_REPAIR_TASK_MAP[effective_locale], ctx, locale=effective_locale) + (
        "\nYou are repairing a rejected 7-day nutrition plan. The deterministic reviewer only "
        "reports defects; you are responsible for selecting all foods. Return valid JSON only, "
        "with no markdown or commentary. Preserve safe valid parts when useful, or regenerate the "
        "whole week. Do not omit required sections."
    )
    user = (
        f"LOCALE:\n{effective_locale}\n\n"
        f"USER MEMORY/PROFILE JSON:\n{json.dumps(ctx.to_prompt_memory(), ensure_ascii=False)}\n\n"
        f"REJECTED PLAN JSON:\n{json.dumps(original_plan, ensure_ascii=False)}\n\n"
        f"EXACT REVIEW ISSUES JSON:\n{json.dumps(issue_data, ensure_ascii=False)}\n\n"
        "REPAIR REQUIREMENTS:\n"
        "- Return the complete plan object with exactly 7 days and the same output contract as a generated week plan.\n"
        "- Repair using culture, locale, budget, goal, allergies/intolerances, disliked foods, breakfast habit, and activity pattern.\n"
        "- Never repeat low-quality economic meals for premium users.\n"
        "- Do not use سیب‌زمینی آبپز با میوه as a full breakfast.\n"
        "- Do not repeat عدسی با برنج for high-budget/high-protein users unless explicitly requested.\n"
        "- Do not repeat soup as the default dinner.\n"
        "- Include exactly one visible meal with meal_type and meal_slot 'cheating_date', title exactly 'Cheating Date', on day 5 or 6, with a clear controlled-flexibility description and time window.\n"
        "- Every meal needs measurable portions and time_window_start/time_window_end.\n"
        "- Never place allergies, intolerances, or disliked foods in any user-visible field.\n"
        f"- Remove every exact disliked-food term everywhere in visible JSON, including title, description, portion_guidance, food_items, alternatives, shopping_notes, budget_guidance, cheat_meal_guidance, restaurant_party_travel_guidance, notes, and warnings: {json.dumps(ctx.disliked_foods, ensure_ascii=False)}.\n"
        "- Choose culturally appropriate alternatives yourself; do not merely delete a staple and leave meals incomplete.\n"
        "- Return JSON only; no markdown outside JSON.\n"
        + (f"\n{gluten_section}\nUse نان بدون گلوتن and safe gluten-free grain alternatives where bread/grain is expected. Check sauces, marinades, soups, fried coatings, and cross-contamination in restaurant guidance.\n" if gluten_section else "")
    )
    return PromptData(task_type=task_type, system=system, user=user)


def for_weekly_report(
    ctx: NutritionMemoryContext,
    weekly_metrics: dict,
    locale: str | None = None,
) -> PromptData:
    effective_locale = _normalize_locale(locale)
    system = (
        _base_system(TASK_WEEKLY_REPORT, ctx, locale=effective_locale)
        + "\nWeekly report rules:\n"
        "- Use NutritionMemoryContext and the deterministic weekly metrics; do not invent missing data.\n"
        "- Explain patterns in simple, supportive, non-judgmental language.\n"
        "- Provide exactly three strengths, exactly two small adjustments, and one small next-week goal.\n"
        "- Mention human review when risk context or red-flag symptoms require it.\n"
        "- Never recommend fasting, detox, purging, skipping meals, extreme exercise, or severe calorie restriction as compensation.\n"
    )
    user = (
        f"User memory/context:\n{_memory_json(ctx)}\n\n"
        f"Deterministic weekly metrics:\n{json.dumps(weekly_metrics, ensure_ascii=False, indent=2)}\n\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "summary": "...",\n'
        '  "behavior_pattern_summary": "...",\n'
        '  "three_strengths": ["...", "...", "..."],\n'
        '  "two_small_adjustments": ["...", "..."],\n'
        '  "next_week_small_goal": "...",\n'
        '  "monitoring_notes": "...",\n'
        '  "safety_notes": [],\n'
        '  "requires_human_review": false\n'
        "}"
    )
    return PromptData(task_type="weekly_report", system=system, user=user)


def for_adapt_plan(
    ctx: NutritionMemoryContext,
    current_plan_title: str | None,
    reason: str,
    recent_context: dict,
) -> PromptData:
    system = _base_system(TASK_ADAPT_PLAN, ctx)
    user_ctx = _memory_json(ctx)
    plan_info = f"Current plan: {current_plan_title}" if current_plan_title else "No active plan"
    ctx_str = json.dumps(recent_context, ensure_ascii=False) if recent_context else "{}"
    user = (
        f"User profile: {user_ctx}\n\n"
        + _dislike_constraint(ctx)
        + f"\n{plan_info}\n"
        f"Reason for adjustment: {reason}\n"
        f"Recent context: {ctx_str}\n\n"
        "Diet is a living plan. Adjust the active plan/day based on new data when safe and useful.\n"
        "Consider hunger, sleep, stress, activity, adherence, cravings, symptoms, eating out, travel/work constraints, medical risk, active plan context, and memory context.\n"
        "Do not recommend punishment, fasting after overeating, skipping meals, detox, purging, extreme exercise, aggressive compensation, or medication changes.\n"
        "When schema allows, provide practical revised meals using household portions and simple reasons for important changes.\n"
        "Ask one concise follow-up question only if critical data is missing.\n"
        "Return JSON exactly in this shape:\n"
        "{\n"
        '  "summary": "...",\n'
        '  "assessment_summary": "...",\n'
        '  "nutrition_diagnosis": "...",\n'
        '  "intervention_summary": "...",\n'
        '  "monitoring_notes": "...",\n'
        '  "changes": ["..."],\n'
        '  "updated_guidelines": {"calories": int, "protein_g": float, "carbs_g": float, "fat_g": float, "fiber_g": float, "water_liters": float, "notes": "..."},\n'
        '  "revised_meals": [{"meal_type": "breakfast|lunch|dinner|snack", "title": "...", "description": "...", "portion_guidance": "...", "alternatives": ["..."], "preparation_notes": null}],\n'
        '  "revised_day": {"day_index": 1, "title": "...", "summary": "...", "hydration_goal": "...", "notes": "...", "warnings": [], "meals": []},\n'
        '  "changed_items": ["..."],\n'
        '  "reason_for_changes": "...",\n'
        '  "safety_notes": ["..."],\n'
        '  "requires_human_review": false,\n'
        '  "follow_up_question": null,\n'
        '  "warnings": []\n'
        "}"
    )
    return PromptData(task_type="adapt_plan", system=system, user=user)
