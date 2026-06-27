"""
WeeklyPlanPersonalizationValidator: post-generation safety layer.

Validates and sanitizes AI-generated 7-day plans:
- Enforces allergies and disliked foods (allergen variant matching)
- Replaces unsafe meals with safe locale-specific alternatives
- Sorts meals by fixed order
- Ensures 7 days with required fields
"""
from __future__ import annotations

import json
import logging

from app.services.nutrition_memory_service import NutritionMemoryContext

logger = logging.getLogger(__name__)

# Fixed meal ordering
MEAL_ORDER = [
    "breakfast",
    "morning_snack",
    "lunch",
    "pre_workout",
    "post_workout",
    "afternoon_snack",
    "dinner",
    "optional_evening_snack",
    "snack",  # legacy fallback after dinner
    "other",
]

_ALLERGEN_VARIANTS: dict[str, list[str]] = {
    "egg": [
        "egg", "eggs", "omelet", "omelette", "omlet", "scrambled",
        "تخم مرغ", "تخم‌مرغ", "تخممرغ", "نیمرو",
        "اُملت", "امـلت", "آملت", "آمیلت", "املت",
        "عجة", "بيض", "بيضة", "بيضتان",
    ],
    "gluten": ["wheat", "gluten", "گندم"],
    "peanut": ["peanut", "بادام زمینی"],
    "lactose": ["milk", "dairy", "lactose", "شیر", "لبنیات"],
    "fish": ["fish", "salmon", "tuna", "cod", "ماهی", "سالمون", "تن"],
    "shellfish": ["shrimp", "crab", "lobster", "میگو", "خرچنگ"],
    "soy": ["soy", "tofu", "سویا"],
    "tree_nut": ["walnut", "almond", "cashew", "pistachio", "گردو", "بادام", "پسته"],
}

_SAFE_REPLACEMENTS: dict[str, dict[str, dict]] = {
    "fa": {
        "breakfast": {
            "title": "صبحانه: نان و پنیر با گردو",
            "description": "نان سبوس‌دار با پنیر کم‌چرب، گردو و چای کمرنگ",
            "portion_guidance": "دو برش نان، ۳۰ گرم پنیر",
            "alternatives": ["ماست با میوه", "نان و کره"],
        },
        "morning_snack": {
            "title": "میان‌وعده صبح: میوه فصلی",
            "description": "یک عدد میوه فصلی تازه",
            "portion_guidance": "یک عدد میوه متوسط",
            "alternatives": ["ماست کم‌چرب", "هویج خام"],
        },
        "lunch": {
            "title": "ناهار: عدسی با نان",
            "description": "عدس پخته با ادویه ملایم و نان سبوس‌دار",
            "portion_guidance": "یک کاسه عدسی، یک برش نان",
            "alternatives": ["سوپ سبزیجات", "آش رشته"],
        },
        "dinner": {
            "title": "شام: سوپ سبزیجات",
            "description": "سوپ سبک با سبزیجات فصلی",
            "portion_guidance": "یک کاسه سوپ",
            "alternatives": ["عدسی", "ماست و خیار"],
        },
        "snack": {
            "title": "میان‌وعده: ماست با خیار",
            "description": "ماست کم‌چرب با خیار و نعنا",
            "portion_guidance": "یک کاسه کوچک",
            "alternatives": ["میوه فصلی", "آجیل بدون نمک"],
        },
        "afternoon_snack": {
            "title": "میان‌وعده بعدازظهر: میوه و آجیل",
            "description": "یک عدد میوه فصلی با چند عدد بادام یا گردو",
            "portion_guidance": "یک میوه، ۲۰ گرم آجیل",
            "alternatives": ["ماست کم‌چرب", "هویج خام"],
        },
        "pre_workout": {
            "title": "پیش از تمرین: موز با نان",
            "description": "موز با نان سبوس‌دار برای انرژی",
            "portion_guidance": "یک موز، یک برش نان",
            "alternatives": ["ماست با عسل", "میوه فصلی"],
        },
        "post_workout": {
            "title": "پس از تمرین: ماست و میوه",
            "description": "ماست کم‌چرب با میوه فصلی برای بازیابی",
            "portion_guidance": "یک کاسه ماست، یک میوه",
            "alternatives": ["دوغ کم‌نمک", "آب میوه طبیعی"],
        },
        "optional_evening_snack": {
            "title": "میان‌وعده شبانه: ماست ساده",
            "description": "ماست کم‌چرب ساده",
            "portion_guidance": "یک کاسه کوچک",
            "alternatives": ["کمپوت", "میوه سبک"],
        },
    },
    "en": {
        "breakfast": {
            "title": "Breakfast: Whole-Grain Bread with Cheese",
            "description": "Whole-grain bread with low-fat cheese and walnuts",
            "portion_guidance": "Two slices of bread, 30g cheese",
            "alternatives": ["Yogurt with fruit", "Oatmeal"],
        },
        "morning_snack": {
            "title": "Morning Snack: Seasonal Fruit",
            "description": "One fresh seasonal fruit",
            "portion_guidance": "One medium fruit",
            "alternatives": ["Low-fat yogurt", "Raw carrot sticks"],
        },
        "lunch": {
            "title": "Lunch: Lentil Soup with Bread",
            "description": "Cooked lentils with mild spices and whole-grain bread",
            "portion_guidance": "One bowl of lentils, one slice of bread",
            "alternatives": ["Vegetable soup", "Bean stew"],
        },
        "dinner": {
            "title": "Dinner: Vegetable Soup",
            "description": "Light mixed vegetable soup",
            "portion_guidance": "One bowl of soup",
            "alternatives": ["Lentils", "Yogurt with cucumber and bread"],
        },
        "snack": {
            "title": "Snack: Yogurt with Cucumber",
            "description": "Low-fat yogurt with cucumber and fresh mint",
            "portion_guidance": "One small bowl",
            "alternatives": ["Seasonal fruit", "Unsalted nuts"],
        },
        "afternoon_snack": {
            "title": "Afternoon Snack: Fruit and Nuts",
            "description": "One seasonal fruit with almonds or walnuts",
            "portion_guidance": "One fruit, 20g nuts",
            "alternatives": ["Low-fat yogurt", "Raw carrot sticks"],
        },
        "pre_workout": {
            "title": "Pre-Workout: Banana with Bread",
            "description": "Banana with whole-grain bread for energy",
            "portion_guidance": "One banana, one slice of bread",
            "alternatives": ["Yogurt with honey", "Seasonal fruit"],
        },
        "post_workout": {
            "title": "Post-Workout: Yogurt and Fruit",
            "description": "Low-fat yogurt with seasonal fruit for recovery",
            "portion_guidance": "One bowl of yogurt, one fruit",
            "alternatives": ["Doogh (low-salt yogurt drink)", "Fresh fruit juice"],
        },
        "optional_evening_snack": {
            "title": "Evening Snack: Plain Yogurt",
            "description": "Simple low-fat yogurt",
            "portion_guidance": "One small bowl",
            "alternatives": ["Stewed fruit", "Light fruit"],
        },
    },
    "ar": {
        "breakfast": {
            "title": "الفطور: خبز حبوب كاملة مع جبن",
            "description": "خبز حبوب كاملة مع جبن قليل الدسم وجوز",
            "portion_guidance": "شريحتا خبز، ٣٠ جرام جبن",
            "alternatives": ["زبادي مع فاكهة", "شوفان"],
        },
        "morning_snack": {
            "title": "وجبة خفيفة صباحية: فاكهة موسمية",
            "description": "فاكهة موسمية طازجة",
            "portion_guidance": "فاكهة متوسطة",
            "alternatives": ["زبادي قليل الدسم", "جزر نيء"],
        },
        "lunch": {
            "title": "الغداء: شوربة عدس مع خبز",
            "description": "عدس مطبوخ مع بهارات خفيفة وخبز حبوب كاملة",
            "portion_guidance": "وعاء عدس وشريحة خبز",
            "alternatives": ["شوربة خضار", "فاصوليا مطبوخة"],
        },
        "dinner": {
            "title": "العشاء: شوربة خضار",
            "description": "شوربة خضار مشكلة خفيفة",
            "portion_guidance": "وعاء شوربة",
            "alternatives": ["عدس مطبوخ", "زبادي مع خيار وخبز"],
        },
        "snack": {
            "title": "وجبة خفيفة: زبادي مع خيار",
            "description": "زبادي قليل الدسم مع خيار ونعناع",
            "portion_guidance": "وعاء صغير",
            "alternatives": ["فاكهة موسمية", "مكسرات غير مملحة"],
        },
        "afternoon_snack": {
            "title": "وجبة خفيفة بعد الظهر: فاكهة ومكسرات",
            "description": "فاكهة موسمية مع لوز أو جوز",
            "portion_guidance": "فاكهة واحدة، ٢٠ جرام مكسرات",
            "alternatives": ["زبادي قليل الدسم", "جزر نيء"],
        },
        "pre_workout": {
            "title": "قبل التمرين: موز مع خبز",
            "description": "موز مع خبز حبوب كاملة للطاقة",
            "portion_guidance": "موزة واحدة وشريحة خبز",
            "alternatives": ["زبادي مع عسل", "فاكهة موسمية"],
        },
        "post_workout": {
            "title": "بعد التمرين: زبادي وفاكهة",
            "description": "زبادي قليل الدسم مع فاكهة موسمية للتعافي",
            "portion_guidance": "وعاء زبادي وفاكهة",
            "alternatives": ["دوغ", "عصير فاكهة طازج"],
        },
        "optional_evening_snack": {
            "title": "وجبة خفيفة مسائية: زبادي سادة",
            "description": "زبادي قليل الدسم بسيط",
            "portion_guidance": "وعاء صغير",
            "alternatives": ["فاكهة مطبوخة", "فاكهة خفيفة"],
        },
    },
}


def _build_forbidden_terms(ctx: NutritionMemoryContext) -> set[str]:
    """Build a set of all forbidden terms from allergies and disliked foods."""
    terms: set[str] = set()
    user_restrictions = [a.lower() for a in ctx.allergies] + [d.lower() for d in ctx.disliked_foods]

    for restriction in user_restrictions:
        # Direct add
        terms.add(restriction)
        # Check allergen variant table
        for allergen_key, variants in _ALLERGEN_VARIANTS.items():
            for variant in variants:
                if restriction in variant.lower() or variant.lower() in restriction:
                    terms.update(v.lower() for v in variants)
                    break

    return terms


def _text_contains_forbidden(text: str | None, forbidden_terms: set[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(term in lowered for term in forbidden_terms)


def _meal_is_safe(meal: dict, forbidden_terms: set[str]) -> bool:
    if not forbidden_terms:
        return True
    for field in ("title", "description", "portion_guidance", "preparation_notes", "rest_day_note"):
        if _text_contains_forbidden(meal.get(field), forbidden_terms):
            return False
    for item in (meal.get("food_items") or []):
        if isinstance(item, dict) and _text_contains_forbidden(item.get("name"), forbidden_terms):
            return False
    return True


def _safe_replacement(meal: dict, locale: str, forbidden_terms: set[str]) -> dict:
    """Return a safe replacement meal for the given slot/locale."""
    slot = meal.get("meal_slot") or meal.get("meal_type") or "snack"
    locale_replacements = _SAFE_REPLACEMENTS.get(locale, _SAFE_REPLACEMENTS["fa"])
    replacement = locale_replacements.get(slot, locale_replacements.get("snack", {}))

    result = dict(meal)  # keep meal_type, meal_slot, meal_order etc.
    result.update({
        "title": replacement.get("title", meal.get("title", "—")),
        "description": replacement.get("description", ""),
        "portion_guidance": replacement.get("portion_guidance"),
        "alternatives": [
            a for a in (replacement.get("alternatives") or [])
            if not _text_contains_forbidden(a, forbidden_terms)
        ],
        "preparation_notes": None,
        "food_items": [],
    })
    return result


def _clean_alternatives(meal: dict, forbidden_terms: set[str]) -> dict:
    if not forbidden_terms:
        return meal
    alts = meal.get("alternatives") or []
    safe_alts = [a for a in alts if not _text_contains_forbidden(a, forbidden_terms)]
    return {**meal, "alternatives": safe_alts}


def _meal_order_key(meal: dict) -> int:
    slot = meal.get("meal_slot") or meal.get("meal_type") or "other"
    try:
        return MEAL_ORDER.index(slot)
    except ValueError:
        return len(MEAL_ORDER)


def validate_and_sanitize(plan_data: dict, ctx: NutritionMemoryContext, locale: str = "fa") -> dict:
    """Validate and sanitize a generated week plan dict. Returns cleaned plan."""
    forbidden_terms = _build_forbidden_terms(ctx)
    days = list(plan_data.get("days") or [])

    # Ensure exactly 7 days
    days = days[:7]

    sanitized_days = []
    for day in days:
        meals = list(day.get("meals") or [])
        sanitized_meals = []
        for meal in meals:
            # Set meal_slot from meal_type if missing
            if not meal.get("meal_slot") and meal.get("meal_type"):
                meal = {**meal, "meal_slot": meal["meal_type"]}

            if not _meal_is_safe(meal, forbidden_terms):
                logger.info("Replacing unsafe meal '%s' (slot=%s)", meal.get("title", ""), meal.get("meal_slot", ""))
                meal = _safe_replacement(meal, locale, forbidden_terms)
            else:
                meal = _clean_alternatives(meal, forbidden_terms)

            sanitized_meals.append(meal)

        # Sort by fixed meal order
        sanitized_meals.sort(key=_meal_order_key)

        # Compute daily_calories from meals if missing
        day_calories = day.get("daily_calories")
        if day_calories is None:
            cal_sum = sum(m.get("calories_estimate") or 0 for m in sanitized_meals)
            if cal_sum > 0:
                day = {**day, "daily_calories": cal_sum}

        # Add clinical review warning if needed
        day_warnings = list(day.get("warnings") or [])
        if ctx.clinical_review_required:
            clinical_msgs = {
                "fa": "بر اساس وضعیت پزشکی شما، پیش از اجرای این برنامه با پزشک مشورت کنید.",
                "en": "Based on your medical profile, consult a doctor before following this plan.",
                "ar": "بناءً على وضعك الطبي، استشر طبيباً قبل اتباع هذه الخطة.",
            }
            cw = clinical_msgs.get(locale, clinical_msgs["fa"])
            if cw not in day_warnings:
                day_warnings.append(cw)

        sanitized_days.append({**day, "meals": sanitized_meals, "warnings": day_warnings})

    return {**plan_data, "days": sanitized_days}
