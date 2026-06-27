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

_LOCALE_TASK_MAP = {
    "fa": TASK_GENERATE_WEEK_FA,
    "en": TASK_GENERATE_WEEK_EN,
    "ar": TASK_GENERATE_WEEK_AR,
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
        "- Respect Iranian/Persian food culture when suitable: rice, bread, stews, legumes, yogurt, vegetables, halal meats.\n"
        "- Use realistic foods and household units where useful, such as plate, bowl, cup, spoon, palm, handful, slice.\n"
        "- Consider budget, time, cooking ability, work schedule, family meals, restaurant meals, travel, and food access.\n"
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
        "Generate a practical initial nutrition plan only if the profile is sufficiently complete.\n"
        "Do not create a complete strict diet based only on height, weight, and goal.\n"
        "The plan must include realistic meals/snacks, household portions in descriptions or notes, alternatives, a quick busy-day option, outside-home/restaurant flexibility where possible, a simple scientific reason, and safety warnings when relevant.\n"
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
        f"Available foods: {foods_str}\n"
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
    system = (
        _base_system(TASK_CHAT, ctx)
        + "\nChat behavior:\n"
        "- Use profile and conversation memory, but do not expose system internals.\n"
        "- Ask one concise follow-up question when key nutrition data is missing and a safe answer needs it.\n"
        "- Do not over-question; give practical guidance when safe.\n"
        "- Mention human review when risk context requires it.\n"
        "- For Persian users, prefer Iranian food examples and household units.\n"
    )

    clean_history: list[dict[str, str]] = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-6:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    user = (
        f"User profile context: {user_ctx_json}\n\n"
        f"User message: {user_message}\n\n"
        "Give a concise, natural nutrition-companion response. Return JSON exactly as:\n"
        '{"reply": "...", "assessment_summary": "...", "monitoring_notes": "..."}'
    )
    return PromptData(
        task_type="chat_message",
        system=system,
        user=user,
        history_messages=clean_history,
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
        allergen_lines.append(f"DISLIKED FOODS — DO NOT include: {disliked_str}")

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

    user = (
        f"User profile:\n{user_ctx}\n\n"
        + (f"{allergen_section}\n\n" if allergen_section else "")
        + f"{budget_section}\n"
        + f"Generate exactly 7 days of meal plan in locale={effective_locale}.\n"
        + f"{training_note}\n"
        + "Use household portions. Include time windows for each meal. Provide calories and macros.\n"
        + "PORTION GUIDANCE RULES — MANDATORY for every meal's portion_guidance field:\n"
        + "- NEVER use vague phrases: کنترل‌شده، مقدار مناسب، کمی، به مقدار کافی، متعادل.\n"
        + "- Bread: '۲ کف دست نان' — NEVER only 'برش نان' without کف دست.\n"
        + "- Rice + stew (قرمه‌سبزی، قیمه، فسنجان …): '۵ قاشق غذاخوری برنج + ۴ قاشق غذاخوری خورش [name]'.\n"
        + "- Mixed polo (لوبیاپلو، عدس‌پلو، سبزی‌پلو، استانبولی): '۸ قاشق غذاخوری [polo name]'.\n"
        + "- Chicken/meat: '۱ کف دست مرغ پخته، حدود ۱۲۰ گرم'.\n"
        + "- Yogurt: '۱ کاسه کوچک ماست، حدود ۱۵۰ گرم'. Cheese: 'پنیر به اندازه ۱ قوطی کبریت'.\n"
        + "- Fruit: '۱ عدد متوسط'. Salad/vegetables: '۱ کاسه متوسط'. Soup: '۱ کاسه متوسط'.\n"
        + "- EVERY portion_guidance must be a specific, measurable household unit — no exceptions.\n"
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
        f"{plan_info}\n"
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
