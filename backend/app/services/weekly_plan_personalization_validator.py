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

from app.services.nutrition_memory_service import NutritionMemoryContext, normalize_budget_tier

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
    "cheating_date",
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
    "gluten": [
        "wheat", "gluten", "bread", "pasta", "flour", "noodle", "lasagna",
        "rye", "barley", "semolina", "couscous", "tortilla",
        "گندم", "نان", "رشته", "آرد", "خبز",
        "ماکارونی", "پاستا", "خمیر", "نان سبوس‌دار", "لازانیا",
        "گلوتن", "طحين", "معكرونة",
    ],
    "peanut": ["peanut", "بادام زمینی"],
    "lactose": [
        "milk", "dairy", "lactose", "yogurt", "yoghurt", "cheese", "cream",
        "kefir", "doogh", "whey", "butter",
        "شیر", "لبنیات", "ماست", "یوگورت", "پنیر", "خامه",
        "لاکتوز", "دوغ", "کشک", "آب پنیر",
        "زبادي", "جبن", "حليب", "لبن", "قشطة",
    ],
    "fish": ["fish", "salmon", "tuna", "cod", "ماهی", "سالمون", "تن"],
    "shellfish": ["shrimp", "crab", "lobster", "میگو", "خرچنگ"],
    "soy": ["soy", "tofu", "سویا"],
    "tree_nut": [
        "walnut", "almond", "cashew", "pistachio", "nuts", "nut",
        "گردو", "بادام", "پسته", "آجیل", "مغز", "مكسرات",
    ],
}

# Ordered candidates per locale+slot. Candidate 0 has NO common allergens;
# later candidates progressively allow dairy, then gluten/nuts.
# _safe_replacement() iterates until one passes _meal_is_safe().
_REPLACEMENT_CANDIDATES: dict[str, dict[str, list[dict]]] = {
    "fa": {
        "breakfast": [
            {
                "title": "صبحانه: سیب‌زمینی آب‌پز با میوه",
                "description": "سیب‌زمینی آب‌پز با میوه فصلی و چای کمرنگ",
                "portion_guidance": "یک عدد سیب‌زمینی متوسط، یک میوه فصلی",
                "alternatives": ["خرما با میوه", "موز"],
                "food_items": [
                    {"name": "سیب‌زمینی آب‌پز", "amount": "150", "unit": "گرم", "calories_estimate": 120},
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 60},
                ],
            },
            {
                "title": "صبحانه: ماست ساده با میوه",
                "description": "ماست کم‌چرب با میوه فصلی",
                "portion_guidance": "یک کاسه ماست، یک میوه",
                "alternatives": ["دوغ با میوه", "میوه فصلی"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "200", "unit": "گرم", "calories_estimate": 100},
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 60},
                ],
            },
            {
                "title": "صبحانه: نان و پنیر",
                "description": "نان سبوس‌دار با پنیر کم‌چرب و چای",
                "portion_guidance": "دو برش نان، ۳۰ گرم پنیر",
                "alternatives": ["ماست با میوه", "نان و کره"],
                "food_items": [
                    {"name": "نان سبوس‌دار", "amount": "60", "unit": "گرم", "calories_estimate": 150},
                    {"name": "پنیر کم‌چرب", "amount": "30", "unit": "گرم", "calories_estimate": 70},
                ],
            },
        ],
        "morning_snack": [
            {
                "title": "میان‌وعده صبح: میوه فصلی",
                "description": "یک عدد میوه فصلی تازه",
                "portion_guidance": "یک عدد میوه متوسط",
                "alternatives": ["هویج خام", "خیار تازه"],
                "food_items": [
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 70},
                ],
            },
            {
                "title": "میان‌وعده صبح: هویج و خیار",
                "description": "هویج و خیار تازه برش‌خورده",
                "portion_guidance": "دو هویج کوچک، یک خیار",
                "alternatives": ["میوه فصلی", "کرفس تازه"],
                "food_items": [
                    {"name": "هویج", "amount": "100", "unit": "گرم", "calories_estimate": 40},
                    {"name": "خیار", "amount": "100", "unit": "گرم", "calories_estimate": 15},
                ],
            },
            {
                "title": "میان‌وعده صبح: ماست کم‌چرب",
                "description": "ماست ساده کم‌چرب",
                "portion_guidance": "یک کاسه کوچک",
                "alternatives": ["میوه فصلی", "هویج خام"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "150", "unit": "گرم", "calories_estimate": 75},
                ],
            },
        ],
        "lunch": [
            {
                "title": "ناهار: عدسی با برنج",
                "description": "عدس پخته با ادویه ملایم و برنج",
                "portion_guidance": "یک کاسه عدسی، نصف کاسه برنج",
                "alternatives": ["سوپ سبزیجات", "مرغ با سبزیجات"],
                "food_items": [
                    {"name": "عدس پخته", "amount": "150", "unit": "گرم", "calories_estimate": 180},
                    {"name": "برنج", "amount": "100", "unit": "گرم", "calories_estimate": 130},
                ],
            },
            {
                "title": "ناهار: مرغ آب‌پز با سبزیجات",
                "description": "مرغ آب‌پز با سبزیجات فصلی",
                "portion_guidance": "۱۲۰ گرم مرغ، یک کاسه سبزیجات",
                "alternatives": ["عدسی با برنج", "سوپ سبزیجات"],
                "food_items": [
                    {"name": "مرغ آب‌پز", "amount": "120", "unit": "گرم", "calories_estimate": 200},
                    {"name": "سبزیجات فصلی", "amount": "150", "unit": "گرم", "calories_estimate": 50},
                ],
            },
            {
                "title": "ناهار: عدسی با نان",
                "description": "عدس پخته با ادویه ملایم و نان سبوس‌دار",
                "portion_guidance": "یک کاسه عدسی، یک برش نان",
                "alternatives": ["سوپ سبزیجات", "مرغ با سبزیجات"],
                "food_items": [
                    {"name": "عدس پخته", "amount": "150", "unit": "گرم", "calories_estimate": 180},
                    {"name": "نان سبوس‌دار", "amount": "40", "unit": "گرم", "calories_estimate": 100},
                ],
            },
        ],
        "dinner": [
            {
                "title": "شام: سوپ سبزیجات",
                "description": "سوپ سبک با سبزیجات فصلی",
                "portion_guidance": "یک کاسه سوپ",
                "alternatives": ["عدسی", "مرغ با سبزیجات"],
                "food_items": [
                    {"name": "سوپ سبزیجات", "amount": "300", "unit": "میلی‌لیتر", "calories_estimate": 120},
                ],
            },
            {
                "title": "شام: مرغ آب‌پز با سبزیجات",
                "description": "مرغ آب‌پز سبک با سبزیجات بخارپز",
                "portion_guidance": "۱۰۰ گرم مرغ، یک کاسه سبزیجات",
                "alternatives": ["سوپ سبزیجات", "عدسی"],
                "food_items": [
                    {"name": "مرغ آب‌پز", "amount": "100", "unit": "گرم", "calories_estimate": 165},
                    {"name": "سبزیجات بخارپز", "amount": "150", "unit": "گرم", "calories_estimate": 50},
                ],
            },
            {
                "title": "شام: عدسی با نان",
                "description": "عدسی ساده با نان سبوس‌دار",
                "portion_guidance": "یک کاسه، یک برش نان",
                "alternatives": ["سوپ سبزیجات", "مرغ با سبزیجات"],
                "food_items": [
                    {"name": "عدسی", "amount": "200", "unit": "گرم", "calories_estimate": 150},
                    {"name": "نان سبوس‌دار", "amount": "40", "unit": "گرم", "calories_estimate": 100},
                ],
            },
        ],
        "snack": [
            {
                "title": "میان‌وعده: میوه فصلی",
                "description": "میوه فصلی تازه",
                "portion_guidance": "یک عدد میوه متوسط",
                "alternatives": ["هویج خام", "خیار تازه"],
                "food_items": [
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 70},
                ],
            },
            {
                "title": "میان‌وعده: هویج و خیار",
                "description": "هویج و خیار تازه",
                "portion_guidance": "دو هویج، یک خیار",
                "alternatives": ["میوه فصلی", "کرفس"],
                "food_items": [
                    {"name": "هویج", "amount": "100", "unit": "گرم", "calories_estimate": 40},
                    {"name": "خیار", "amount": "100", "unit": "گرم", "calories_estimate": 15},
                ],
            },
            {
                "title": "میان‌وعده: ماست با خیار",
                "description": "ماست کم‌چرب با خیار و نعنا",
                "portion_guidance": "یک کاسه کوچک",
                "alternatives": ["میوه فصلی", "هویج خام"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "150", "unit": "گرم", "calories_estimate": 75},
                    {"name": "خیار", "amount": "50", "unit": "گرم", "calories_estimate": 8},
                ],
            },
        ],
        "afternoon_snack": [
            {
                "title": "میان‌وعده بعدازظهر: میوه فصلی",
                "description": "یک عدد میوه فصلی تازه",
                "portion_guidance": "یک میوه متوسط",
                "alternatives": ["هویج خام", "خیار تازه"],
                "food_items": [
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 70},
                ],
            },
            {
                "title": "میان‌وعده بعدازظهر: هویج و خیار",
                "description": "هویج و خیار تازه برش‌خورده",
                "portion_guidance": "دو هویج کوچک، یک خیار",
                "alternatives": ["میوه فصلی", "کرفس"],
                "food_items": [
                    {"name": "هویج", "amount": "100", "unit": "گرم", "calories_estimate": 40},
                    {"name": "خیار", "amount": "100", "unit": "گرم", "calories_estimate": 15},
                ],
            },
            {
                "title": "میان‌وعده بعدازظهر: ماست کم‌چرب",
                "description": "ماست ساده کم‌چرب",
                "portion_guidance": "یک کاسه کوچک",
                "alternatives": ["میوه فصلی", "هویج خام"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "150", "unit": "گرم", "calories_estimate": 75},
                ],
            },
        ],
        "pre_workout": [
            {
                "title": "پیش از تمرین: موز",
                "description": "موز رسیده برای انرژی سریع",
                "portion_guidance": "یک تا دو موز",
                "alternatives": ["خرما", "میوه فصلی شیرین"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "عدد", "calories_estimate": 100},
                ],
            },
            {
                "title": "پیش از تمرین: موز با برنج",
                "description": "موز با برنج برای انرژی پایدار",
                "portion_guidance": "یک موز، نصف کاسه برنج",
                "alternatives": ["خرما", "میوه فصلی"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "عدد", "calories_estimate": 100},
                    {"name": "برنج", "amount": "100", "unit": "گرم", "calories_estimate": 130},
                ],
            },
            {
                "title": "پیش از تمرین: موز با نان",
                "description": "موز با نان سبوس‌دار برای انرژی",
                "portion_guidance": "یک موز، یک برش نان",
                "alternatives": ["میوه فصلی", "خرما"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "عدد", "calories_estimate": 100},
                    {"name": "نان سبوس‌دار", "amount": "40", "unit": "گرم", "calories_estimate": 100},
                ],
            },
        ],
        "post_workout": [
            {
                "title": "پس از تمرین: مرغ آب‌پز با سبزیجات",
                "description": "مرغ آب‌پز با سبزیجات بخارپز برای بازیابی",
                "portion_guidance": "۱۲۰ گرم مرغ، یک کاسه سبزیجات",
                "alternatives": ["عدسی", "نخود پخته"],
                "food_items": [
                    {"name": "مرغ آب‌پز", "amount": "120", "unit": "گرم", "calories_estimate": 200},
                    {"name": "سبزیجات بخارپز", "amount": "150", "unit": "گرم", "calories_estimate": 50},
                ],
            },
            {
                "title": "پس از تمرین: ماست و میوه",
                "description": "ماست کم‌چرب با میوه فصلی برای بازیابی",
                "portion_guidance": "یک کاسه ماست، یک میوه",
                "alternatives": ["دوغ کم‌نمک", "آب میوه طبیعی"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "200", "unit": "گرم", "calories_estimate": 100},
                    {"name": "میوه فصلی", "amount": "1", "unit": "عدد", "calories_estimate": 60},
                ],
            },
        ],
        "optional_evening_snack": [
            {
                "title": "میان‌وعده شبانه: میوه سبک",
                "description": "میوه سبک مثل سیب یا گلابی",
                "portion_guidance": "یک عدد کوچک",
                "alternatives": ["کمپوت بدون شکر", "خیار"],
                "food_items": [
                    {"name": "سیب", "amount": "1", "unit": "عدد", "calories_estimate": 70},
                ],
            },
            {
                "title": "میان‌وعده شبانه: ماست ساده",
                "description": "ماست کم‌چرب ساده",
                "portion_guidance": "یک کاسه کوچک",
                "alternatives": ["کمپوت", "میوه سبک"],
                "food_items": [
                    {"name": "ماست کم‌چرب", "amount": "150", "unit": "گرم", "calories_estimate": 75},
                ],
            },
        ],
    },
    "en": {
        "breakfast": [
            {
                "title": "Breakfast: Boiled Potato with Fruit",
                "description": "Boiled potato with seasonal fruit and herbal tea",
                "portion_guidance": "One medium potato, one piece of fruit",
                "alternatives": ["Dates with fruit", "Banana"],
                "food_items": [
                    {"name": "Boiled potato", "amount": "150", "unit": "g", "calories_estimate": 120},
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 60},
                ],
            },
            {
                "title": "Breakfast: Low-fat Yogurt with Fruit",
                "description": "Low-fat yogurt with seasonal fruit",
                "portion_guidance": "One bowl yogurt, one fruit",
                "alternatives": ["Kefir with fruit", "Seasonal fruit"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "200", "unit": "g", "calories_estimate": 100},
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 60},
                ],
            },
            {
                "title": "Breakfast: Whole-Grain Bread with Cheese",
                "description": "Whole-grain bread with low-fat cheese and tea",
                "portion_guidance": "Two slices of bread, 30g cheese",
                "alternatives": ["Yogurt with fruit", "Oatmeal"],
                "food_items": [
                    {"name": "Whole-grain bread", "amount": "60", "unit": "g", "calories_estimate": 150},
                    {"name": "Low-fat cheese", "amount": "30", "unit": "g", "calories_estimate": 70},
                ],
            },
        ],
        "morning_snack": [
            {
                "title": "Morning Snack: Seasonal Fruit",
                "description": "One fresh seasonal fruit",
                "portion_guidance": "One medium fruit",
                "alternatives": ["Raw carrot sticks", "Cucumber slices"],
                "food_items": [
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 70},
                ],
            },
            {
                "title": "Morning Snack: Carrot and Cucumber",
                "description": "Fresh sliced carrot and cucumber",
                "portion_guidance": "Two small carrots, one cucumber",
                "alternatives": ["Seasonal fruit", "Celery sticks"],
                "food_items": [
                    {"name": "Carrot", "amount": "100", "unit": "g", "calories_estimate": 40},
                    {"name": "Cucumber", "amount": "100", "unit": "g", "calories_estimate": 15},
                ],
            },
            {
                "title": "Morning Snack: Low-fat Yogurt",
                "description": "Plain low-fat yogurt",
                "portion_guidance": "One small bowl",
                "alternatives": ["Seasonal fruit", "Raw carrot sticks"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "150", "unit": "g", "calories_estimate": 75},
                ],
            },
        ],
        "lunch": [
            {
                "title": "Lunch: Lentil Soup with Rice",
                "description": "Cooked lentils with mild spices and rice",
                "portion_guidance": "One bowl lentils, half bowl rice",
                "alternatives": ["Vegetable soup", "Chicken with vegetables"],
                "food_items": [
                    {"name": "Cooked lentils", "amount": "150", "unit": "g", "calories_estimate": 180},
                    {"name": "Rice", "amount": "100", "unit": "g", "calories_estimate": 130},
                ],
            },
            {
                "title": "Lunch: Steamed Chicken with Vegetables",
                "description": "Boiled chicken with seasonal vegetables",
                "portion_guidance": "120g chicken, one bowl vegetables",
                "alternatives": ["Lentil soup with rice", "Vegetable soup"],
                "food_items": [
                    {"name": "Boiled chicken", "amount": "120", "unit": "g", "calories_estimate": 200},
                    {"name": "Seasonal vegetables", "amount": "150", "unit": "g", "calories_estimate": 50},
                ],
            },
            {
                "title": "Lunch: Lentil Soup with Bread",
                "description": "Cooked lentils with mild spices and whole-grain bread",
                "portion_guidance": "One bowl of lentils, one slice of bread",
                "alternatives": ["Vegetable soup", "Bean stew"],
                "food_items": [
                    {"name": "Cooked lentils", "amount": "150", "unit": "g", "calories_estimate": 180},
                    {"name": "Whole-grain bread", "amount": "40", "unit": "g", "calories_estimate": 100},
                ],
            },
        ],
        "dinner": [
            {
                "title": "Dinner: Vegetable Soup",
                "description": "Light mixed vegetable soup",
                "portion_guidance": "One bowl of soup",
                "alternatives": ["Lentils", "Chicken with vegetables"],
                "food_items": [
                    {"name": "Vegetable soup", "amount": "300", "unit": "ml", "calories_estimate": 120},
                ],
            },
            {
                "title": "Dinner: Chicken with Steamed Vegetables",
                "description": "Light boiled chicken with steamed vegetables",
                "portion_guidance": "100g chicken, one bowl vegetables",
                "alternatives": ["Vegetable soup", "Lentil soup"],
                "food_items": [
                    {"name": "Boiled chicken", "amount": "100", "unit": "g", "calories_estimate": 165},
                    {"name": "Steamed vegetables", "amount": "150", "unit": "g", "calories_estimate": 50},
                ],
            },
            {
                "title": "Dinner: Lentil Soup with Bread",
                "description": "Simple lentil soup with whole-grain bread",
                "portion_guidance": "One bowl, one slice of bread",
                "alternatives": ["Vegetable soup", "Chicken with vegetables"],
                "food_items": [
                    {"name": "Lentil soup", "amount": "200", "unit": "g", "calories_estimate": 150},
                    {"name": "Whole-grain bread", "amount": "40", "unit": "g", "calories_estimate": 100},
                ],
            },
        ],
        "snack": [
            {
                "title": "Snack: Seasonal Fruit",
                "description": "Fresh seasonal fruit",
                "portion_guidance": "One medium fruit",
                "alternatives": ["Raw carrot sticks", "Cucumber slices"],
                "food_items": [
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 70},
                ],
            },
            {
                "title": "Snack: Carrot and Cucumber",
                "description": "Fresh carrot and cucumber",
                "portion_guidance": "Two carrots, one cucumber",
                "alternatives": ["Seasonal fruit", "Celery"],
                "food_items": [
                    {"name": "Carrot", "amount": "100", "unit": "g", "calories_estimate": 40},
                    {"name": "Cucumber", "amount": "100", "unit": "g", "calories_estimate": 15},
                ],
            },
            {
                "title": "Snack: Yogurt with Cucumber",
                "description": "Low-fat yogurt with cucumber and fresh mint",
                "portion_guidance": "One small bowl",
                "alternatives": ["Seasonal fruit", "Raw carrot sticks"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "150", "unit": "g", "calories_estimate": 75},
                    {"name": "Cucumber", "amount": "50", "unit": "g", "calories_estimate": 8},
                ],
            },
        ],
        "afternoon_snack": [
            {
                "title": "Afternoon Snack: Seasonal Fruit",
                "description": "One fresh seasonal fruit",
                "portion_guidance": "One medium fruit",
                "alternatives": ["Raw carrot sticks", "Cucumber slices"],
                "food_items": [
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 70},
                ],
            },
            {
                "title": "Afternoon Snack: Carrot and Cucumber",
                "description": "Fresh sliced carrot and cucumber",
                "portion_guidance": "Two small carrots, one cucumber",
                "alternatives": ["Seasonal fruit", "Celery sticks"],
                "food_items": [
                    {"name": "Carrot", "amount": "100", "unit": "g", "calories_estimate": 40},
                    {"name": "Cucumber", "amount": "100", "unit": "g", "calories_estimate": 15},
                ],
            },
            {
                "title": "Afternoon Snack: Low-fat Yogurt",
                "description": "Plain low-fat yogurt",
                "portion_guidance": "One small bowl",
                "alternatives": ["Seasonal fruit", "Raw carrot sticks"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "150", "unit": "g", "calories_estimate": 75},
                ],
            },
        ],
        "pre_workout": [
            {
                "title": "Pre-Workout: Banana",
                "description": "Ripe banana for quick energy",
                "portion_guidance": "One to two bananas",
                "alternatives": ["Dates", "Sweet seasonal fruit"],
                "food_items": [
                    {"name": "Banana", "amount": "1", "unit": "piece", "calories_estimate": 100},
                ],
            },
            {
                "title": "Pre-Workout: Banana with Rice",
                "description": "Banana with rice for sustained energy",
                "portion_guidance": "One banana, half bowl rice",
                "alternatives": ["Dates", "Seasonal fruit"],
                "food_items": [
                    {"name": "Banana", "amount": "1", "unit": "piece", "calories_estimate": 100},
                    {"name": "Rice", "amount": "100", "unit": "g", "calories_estimate": 130},
                ],
            },
            {
                "title": "Pre-Workout: Banana with Bread",
                "description": "Banana with whole-grain bread for energy",
                "portion_guidance": "One banana, one slice of bread",
                "alternatives": ["Seasonal fruit", "Dates"],
                "food_items": [
                    {"name": "Banana", "amount": "1", "unit": "piece", "calories_estimate": 100},
                    {"name": "Whole-grain bread", "amount": "40", "unit": "g", "calories_estimate": 100},
                ],
            },
        ],
        "post_workout": [
            {
                "title": "Post-Workout: Chicken with Vegetables",
                "description": "Boiled chicken with steamed vegetables for recovery",
                "portion_guidance": "120g chicken, one bowl vegetables",
                "alternatives": ["Lentil soup", "Cooked chickpeas"],
                "food_items": [
                    {"name": "Boiled chicken", "amount": "120", "unit": "g", "calories_estimate": 200},
                    {"name": "Steamed vegetables", "amount": "150", "unit": "g", "calories_estimate": 50},
                ],
            },
            {
                "title": "Post-Workout: Yogurt and Fruit",
                "description": "Low-fat yogurt with seasonal fruit for recovery",
                "portion_guidance": "One bowl of yogurt, one fruit",
                "alternatives": ["Fresh fruit juice", "Fruit smoothie"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "200", "unit": "g", "calories_estimate": 100},
                    {"name": "Seasonal fruit", "amount": "1", "unit": "piece", "calories_estimate": 60},
                ],
            },
        ],
        "optional_evening_snack": [
            {
                "title": "Evening Snack: Light Fruit",
                "description": "Light fruit like apple or pear",
                "portion_guidance": "One small piece",
                "alternatives": ["Unsweetened stewed fruit", "Cucumber"],
                "food_items": [
                    {"name": "Apple", "amount": "1", "unit": "piece", "calories_estimate": 70},
                ],
            },
            {
                "title": "Evening Snack: Plain Yogurt",
                "description": "Simple low-fat yogurt",
                "portion_guidance": "One small bowl",
                "alternatives": ["Stewed fruit", "Light fruit"],
                "food_items": [
                    {"name": "Low-fat yogurt", "amount": "150", "unit": "g", "calories_estimate": 75},
                ],
            },
        ],
    },
    "ar": {
        "breakfast": [
            {
                "title": "الفطور: بطاطا مسلوقة مع فاكهة",
                "description": "بطاطا مسلوقة مع فاكهة موسمية وشاي أعشاب",
                "portion_guidance": "بطاطا متوسطة واحدة وقطعة فاكهة",
                "alternatives": ["تمر مع فاكهة", "موز"],
                "food_items": [
                    {"name": "بطاطا مسلوقة", "amount": "150", "unit": "جرام", "calories_estimate": 120},
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 60},
                ],
            },
            {
                "title": "الفطور: زبادي قليل الدسم مع فاكهة",
                "description": "زبادي قليل الدسم مع فاكهة موسمية",
                "portion_guidance": "وعاء زبادي وقطعة فاكهة",
                "alternatives": ["كفير مع فاكهة", "فاكهة موسمية"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "200", "unit": "جرام", "calories_estimate": 100},
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 60},
                ],
            },
            {
                "title": "الفطور: خبز حبوب كاملة مع جبن",
                "description": "خبز حبوب كاملة مع جبن قليل الدسم وشاي",
                "portion_guidance": "شريحتا خبز، ٣٠ جرام جبن",
                "alternatives": ["زبادي مع فاكهة", "فاكهة موسمية"],
                "food_items": [
                    {"name": "خبز حبوب كاملة", "amount": "60", "unit": "جرام", "calories_estimate": 150},
                    {"name": "جبن قليل الدسم", "amount": "30", "unit": "جرام", "calories_estimate": 70},
                ],
            },
        ],
        "morning_snack": [
            {
                "title": "وجبة خفيفة صباحية: فاكهة موسمية",
                "description": "فاكهة موسمية طازجة",
                "portion_guidance": "فاكهة متوسطة",
                "alternatives": ["جزر نيء", "خيار مقطع"],
                "food_items": [
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 70},
                ],
            },
            {
                "title": "وجبة خفيفة صباحية: جزر وخيار",
                "description": "جزر وخيار طازج مقطع",
                "portion_guidance": "جزرتان صغيرتان وخيارة واحدة",
                "alternatives": ["فاكهة موسمية", "كرفس"],
                "food_items": [
                    {"name": "جزر", "amount": "100", "unit": "جرام", "calories_estimate": 40},
                    {"name": "خيار", "amount": "100", "unit": "جرام", "calories_estimate": 15},
                ],
            },
            {
                "title": "وجبة خفيفة صباحية: زبادي قليل الدسم",
                "description": "زبادي سادة قليل الدسم",
                "portion_guidance": "وعاء صغير",
                "alternatives": ["فاكهة موسمية", "جزر نيء"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "150", "unit": "جرام", "calories_estimate": 75},
                ],
            },
        ],
        "lunch": [
            {
                "title": "الغداء: شوربة عدس مع أرز",
                "description": "عدس مطبوخ مع بهارات خفيفة وأرز",
                "portion_guidance": "وعاء عدس ونصف وعاء أرز",
                "alternatives": ["شوربة خضار", "دجاج مع خضار"],
                "food_items": [
                    {"name": "عدس مطبوخ", "amount": "150", "unit": "جرام", "calories_estimate": 180},
                    {"name": "أرز", "amount": "100", "unit": "جرام", "calories_estimate": 130},
                ],
            },
            {
                "title": "الغداء: دجاج مسلوق مع خضار",
                "description": "دجاج مسلوق مع خضار موسمية",
                "portion_guidance": "١٢٠ جرام دجاج ووعاء خضار",
                "alternatives": ["شوربة عدس مع أرز", "شوربة خضار"],
                "food_items": [
                    {"name": "دجاج مسلوق", "amount": "120", "unit": "جرام", "calories_estimate": 200},
                    {"name": "خضار موسمية", "amount": "150", "unit": "جرام", "calories_estimate": 50},
                ],
            },
            {
                "title": "الغداء: شوربة عدس مع خبز",
                "description": "عدس مطبوخ مع بهارات خفيفة وخبز حبوب كاملة",
                "portion_guidance": "وعاء عدس وشريحة خبز",
                "alternatives": ["شوربة خضار", "فاصوليا مطبوخة"],
                "food_items": [
                    {"name": "عدس مطبوخ", "amount": "150", "unit": "جرام", "calories_estimate": 180},
                    {"name": "خبز حبوب كاملة", "amount": "40", "unit": "جرام", "calories_estimate": 100},
                ],
            },
        ],
        "dinner": [
            {
                "title": "العشاء: شوربة خضار",
                "description": "شوربة خضار مشكلة خفيفة",
                "portion_guidance": "وعاء شوربة",
                "alternatives": ["عدس مطبوخ", "دجاج مع خضار"],
                "food_items": [
                    {"name": "شوربة خضار", "amount": "300", "unit": "مل", "calories_estimate": 120},
                ],
            },
            {
                "title": "العشاء: دجاج مع خضار مطبوخة على البخار",
                "description": "دجاج مسلوق خفيف مع خضار مطبوخة على البخار",
                "portion_guidance": "١٠٠ جرام دجاج ووعاء خضار",
                "alternatives": ["شوربة خضار", "شوربة عدس"],
                "food_items": [
                    {"name": "دجاج مسلوق", "amount": "100", "unit": "جرام", "calories_estimate": 165},
                    {"name": "خضار مطبوخة على البخار", "amount": "150", "unit": "جرام", "calories_estimate": 50},
                ],
            },
            {
                "title": "العشاء: شوربة عدس مع خبز",
                "description": "شوربة عدس بسيطة مع خبز حبوب كاملة",
                "portion_guidance": "وعاء وشريحة خبز",
                "alternatives": ["شوربة خضار", "دجاج مع خضار"],
                "food_items": [
                    {"name": "شوربة عدس", "amount": "200", "unit": "جرام", "calories_estimate": 150},
                    {"name": "خبز حبوب كاملة", "amount": "40", "unit": "جرام", "calories_estimate": 100},
                ],
            },
        ],
        "snack": [
            {
                "title": "وجبة خفيفة: فاكهة موسمية",
                "description": "فاكهة موسمية طازجة",
                "portion_guidance": "فاكهة متوسطة",
                "alternatives": ["جزر نيء", "خيار مقطع"],
                "food_items": [
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 70},
                ],
            },
            {
                "title": "وجبة خفيفة: جزر وخيار",
                "description": "جزر وخيار طازج",
                "portion_guidance": "جزرتان وخيارة",
                "alternatives": ["فاكهة موسمية", "كرفس"],
                "food_items": [
                    {"name": "جزر", "amount": "100", "unit": "جرام", "calories_estimate": 40},
                    {"name": "خيار", "amount": "100", "unit": "جرام", "calories_estimate": 15},
                ],
            },
            {
                "title": "وجبة خفيفة: زبادي مع خيار",
                "description": "زبادي قليل الدسم مع خيار ونعناع",
                "portion_guidance": "وعاء صغير",
                "alternatives": ["فاكهة موسمية", "جزر نيء"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "150", "unit": "جرام", "calories_estimate": 75},
                    {"name": "خيار", "amount": "50", "unit": "جرام", "calories_estimate": 8},
                ],
            },
        ],
        "afternoon_snack": [
            {
                "title": "وجبة خفيفة بعد الظهر: فاكهة موسمية",
                "description": "فاكهة موسمية طازجة",
                "portion_guidance": "فاكهة متوسطة",
                "alternatives": ["جزر نيء", "خيار"],
                "food_items": [
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 70},
                ],
            },
            {
                "title": "وجبة خفيفة بعد الظهر: جزر وخيار",
                "description": "جزر وخيار طازج مقطع",
                "portion_guidance": "جزرتان صغيرتان وخيارة",
                "alternatives": ["فاكهة موسمية", "كرفس"],
                "food_items": [
                    {"name": "جزر", "amount": "100", "unit": "جرام", "calories_estimate": 40},
                    {"name": "خيار", "amount": "100", "unit": "جرام", "calories_estimate": 15},
                ],
            },
            {
                "title": "وجبة خفيفة بعد الظهر: زبادي قليل الدسم",
                "description": "زبادي سادة قليل الدسم",
                "portion_guidance": "وعاء صغير",
                "alternatives": ["فاكهة موسمية", "جزر نيء"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "150", "unit": "جرام", "calories_estimate": 75},
                ],
            },
        ],
        "pre_workout": [
            {
                "title": "قبل التمرين: موز",
                "description": "موز ناضج للطاقة السريعة",
                "portion_guidance": "موزة إلى موزتان",
                "alternatives": ["تمر", "فاكهة موسمية حلوة"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "قطعة", "calories_estimate": 100},
                ],
            },
            {
                "title": "قبل التمرين: موز مع أرز",
                "description": "موز مع أرز للطاقة المستدامة",
                "portion_guidance": "موزة ونصف وعاء أرز",
                "alternatives": ["تمر", "فاكهة موسمية"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "قطعة", "calories_estimate": 100},
                    {"name": "أرز", "amount": "100", "unit": "جرام", "calories_estimate": 130},
                ],
            },
            {
                "title": "قبل التمرين: موز مع خبز",
                "description": "موز مع خبز حبوب كاملة للطاقة",
                "portion_guidance": "موزة وشريحة خبز",
                "alternatives": ["فاكهة موسمية", "تمر"],
                "food_items": [
                    {"name": "موز", "amount": "1", "unit": "قطعة", "calories_estimate": 100},
                    {"name": "خبز حبوب كاملة", "amount": "40", "unit": "جرام", "calories_estimate": 100},
                ],
            },
        ],
        "post_workout": [
            {
                "title": "بعد التمرين: دجاج مع خضار",
                "description": "دجاج مسلوق مع خضار مطبوخة على البخار للتعافي",
                "portion_guidance": "١٢٠ جرام دجاج ووعاء خضار",
                "alternatives": ["شوربة عدس", "حمص مطبوخ"],
                "food_items": [
                    {"name": "دجاج مسلوق", "amount": "120", "unit": "جرام", "calories_estimate": 200},
                    {"name": "خضار مطبوخة على البخار", "amount": "150", "unit": "جرام", "calories_estimate": 50},
                ],
            },
            {
                "title": "بعد التمرين: زبادي وفاكهة",
                "description": "زبادي قليل الدسم مع فاكهة موسمية للتعافي",
                "portion_guidance": "وعاء زبادي وفاكهة",
                "alternatives": ["عصير فاكهة طازج", "فاكهة موسمية"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "200", "unit": "جرام", "calories_estimate": 100},
                    {"name": "فاكهة موسمية", "amount": "1", "unit": "قطعة", "calories_estimate": 60},
                ],
            },
        ],
        "optional_evening_snack": [
            {
                "title": "وجبة خفيفة مسائية: فاكهة خفيفة",
                "description": "فاكهة خفيفة مثل تفاحة أو إجاص",
                "portion_guidance": "قطعة صغيرة واحدة",
                "alternatives": ["فاكهة مطبوخة بدون سكر", "خيار"],
                "food_items": [
                    {"name": "تفاحة", "amount": "1", "unit": "قطعة", "calories_estimate": 70},
                ],
            },
            {
                "title": "وجبة خفيفة مسائية: زبادي سادة",
                "description": "زبادي قليل الدسم بسيط",
                "portion_guidance": "وعاء صغير",
                "alternatives": ["فاكهة مطبوخة", "فاكهة خفيفة"],
                "food_items": [
                    {"name": "زبادي قليل الدسم", "amount": "150", "unit": "جرام", "calories_estimate": 75},
                ],
            },
        ],
    },
}

# Last-resort fallback with no common allergens: rice + steamed vegetables
_ULTRA_SAFE_FALLBACK: dict[str, dict] = {
    "fa": {
        "title": "وعده: برنج با سبزیجات بخارپز",
        "description": "برنج ساده با سبزیجات بخارپز فصلی",
        "portion_guidance": "یک کاسه کوچک برنج، یک کاسه سبزیجات",
        "alternatives": ["عدسی ساده", "سوپ سبزیجات"],
        "food_items": [
            {"name": "برنج", "amount": "150", "unit": "گرم", "calories_estimate": 180},
            {"name": "سبزیجات بخارپز", "amount": "150", "unit": "گرم", "calories_estimate": 50},
        ],
    },
    "en": {
        "title": "Meal: Steamed Rice with Vegetables",
        "description": "Plain steamed rice with seasonal vegetables",
        "portion_guidance": "One small bowl rice, one bowl vegetables",
        "alternatives": ["Simple lentil soup", "Vegetable soup"],
        "food_items": [
            {"name": "Rice", "amount": "150", "unit": "g", "calories_estimate": 180},
            {"name": "Steamed vegetables", "amount": "150", "unit": "g", "calories_estimate": 50},
        ],
    },
    "ar": {
        "title": "وجبة: أرز مع خضار مطبوخة على البخار",
        "description": "أرز سادة مع خضار موسمية مطبوخة على البخار",
        "portion_guidance": "وعاء صغير أرز ووعاء خضار",
        "alternatives": ["شوربة عدس بسيطة", "شوربة خضار"],
        "food_items": [
            {"name": "أرز", "amount": "150", "unit": "جرام", "calories_estimate": 180},
            {"name": "خضار مطبوخة على البخار", "amount": "150", "unit": "جرام", "calories_estimate": 50},
        ],
    },
}


# Allergen-tagged economic shopping ingredients: (name, frozenset of allergen groups)
_ECONOMIC_SHOPPING_ITEMS: dict[str, list[tuple[str, frozenset]]] = {
    "fa": [
        ("حبوبات خشک (عدس، لوبیا، نخود)", frozenset()),
        ("مرغ", frozenset()),
        ("سبزیجات فصلی", frozenset()),
        ("برنج", frozenset()),
        ("سیب‌زمینی", frozenset()),
        ("میوه فصلی", frozenset()),
        ("ماست ساده", frozenset({"lactose"})),
        ("نان سبوس‌دار", frozenset({"gluten"})),
        ("تخم‌مرغ", frozenset({"egg"})),
    ],
    "en": [
        ("dry legumes (lentils, beans, chickpeas)", frozenset()),
        ("chicken", frozenset()),
        ("seasonal vegetables", frozenset()),
        ("rice", frozenset()),
        ("potatoes", frozenset()),
        ("seasonal fruits", frozenset()),
        ("plain yogurt", frozenset({"lactose"})),
        ("whole-grain bread", frozenset({"gluten"})),
        ("eggs", frozenset({"egg"})),
    ],
    "ar": [
        ("البقوليات الجافة (عدس وفاصوليا وحمص)", frozenset()),
        ("الدجاج", frozenset()),
        ("الخضار الموسمية", frozenset()),
        ("الأرز", frozenset()),
        ("البطاطا", frozenset()),
        ("الفواكه الموسمية", frozenset()),
        ("الزبادي العادي", frozenset({"lactose"})),
        ("الخبز الكامل", frozenset({"gluten"})),
        ("البيض", frozenset({"egg"})),
    ],
}

_ECONOMIC_BASE_ITEMS: dict[str, list[tuple[str, frozenset]]] = {
    "fa": [
        ("حبوبات", frozenset()),
        ("مرغ", frozenset()),
        ("سبزیجات فصلی", frozenset()),
        ("برنج", frozenset()),
        ("ماست", frozenset({"lactose"})),
        ("نان سبوس‌دار", frozenset({"gluten"})),
        ("تخم‌مرغ", frozenset({"egg"})),
    ],
    "en": [
        ("legumes", frozenset()),
        ("chicken", frozenset()),
        ("seasonal vegetables", frozenset()),
        ("rice", frozenset()),
        ("yogurt", frozenset({"lactose"})),
        ("whole-grain bread", frozenset({"gluten"})),
        ("eggs", frozenset({"egg"})),
    ],
    "ar": [
        ("البقوليات", frozenset()),
        ("الدجاج", frozenset()),
        ("الخضار الموسمية", frozenset()),
        ("الأرز", frozenset()),
        ("الزبادي", frozenset({"lactose"})),
        ("الخبز الكامل", frozenset({"gluten"})),
        ("البيض", frozenset({"egg"})),
    ],
}


def _detect_active_allergen_groups(forbidden_terms: set[str]) -> set[str]:
    """Return which allergen group keys have active restrictions."""
    active: set[str] = set()
    for group, variants in _ALLERGEN_VARIANTS.items():
        if any(v.lower() in forbidden_terms for v in variants):
            active.add(group)
    return active


def _build_economic_budget_guidance(locale: str, active_allergens: set[str]) -> str:
    items_list = _ECONOMIC_BASE_ITEMS.get(locale, _ECONOMIC_BASE_ITEMS["fa"])
    safe_items = [name for name, groups in items_list if not (groups & active_allergens)]
    sep = "، " if locale != "en" else ", "
    items_str = sep.join(safe_items)
    templates = {
        "fa": f"این برنامه برای بودجه اقتصادی طراحی شده است. {items_str} پایه این برنامه هستند.",
        "en": f"This plan is designed for an economic budget. Affordable, nutritious staples — {items_str} — form the foundation.",
        "ar": f"هذه الخطة مصممة لميزانية اقتصادية. تُشكّل المكونات الميسورة — {items_str} — أساس الخطة.",
    }
    return templates.get(locale, templates["fa"])


def _build_economic_shopping_notes(locale: str, active_allergens: set[str]) -> str:
    items_list = _ECONOMIC_SHOPPING_ITEMS.get(locale, _ECONOMIC_SHOPPING_ITEMS["fa"])
    safe_items = [name for name, groups in items_list if not (groups & active_allergens)]
    sep = "، " if locale != "en" else ", "
    items_str = sep.join(safe_items)
    prefixes = {"fa": "خرید پیشنهادی: ", "en": "Shopping tip: ", "ar": "نصيحة للتسوق: "}
    suffixes = {
        "fa": ". از خرید عمده حبوبات و سبزیجات فصلی صرفه‌جویی کنید.",
        "en": ". Buy legumes and seasonal produce in bulk to save cost.",
        "ar": ". اشتر البقوليات والخضار الموسمية بالجملة لتوفير التكاليف.",
    }
    return prefixes.get(locale, "") + items_str + suffixes.get(locale, "")


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
    for field in ("title", "description", "portion_guidance", "preparation_notes", "rest_day_note", "drink_guidance", "workout_relation"):
        if _text_contains_forbidden(meal.get(field), forbidden_terms):
            return False
    for item in (meal.get("food_items") or []):
        if isinstance(item, dict) and _text_contains_forbidden(item.get("name"), forbidden_terms):
            return False
    return True


def _safe_replacement(meal: dict, locale: str, forbidden_terms: set[str]) -> dict:
    """Return the first allergen-safe candidate for this slot/locale, or the ultra-safe fallback."""
    slot = meal.get("meal_slot") or meal.get("meal_type") or "snack"
    locale_candidates = _REPLACEMENT_CANDIDATES.get(locale, _REPLACEMENT_CANDIDATES["fa"])
    candidates = locale_candidates.get(slot, locale_candidates.get("snack", []))

    for candidate in candidates:
        candidate_meal = {
            **meal,
            "title": candidate["title"],
            "description": candidate.get("description", ""),
            "portion_guidance": candidate.get("portion_guidance"),
            "alternatives": [
                a for a in (candidate.get("alternatives") or [])
                if not _text_contains_forbidden(a, forbidden_terms)
            ],
            "preparation_notes": None,
            "food_items": candidate.get("food_items") or [],
        }
        if _meal_is_safe(candidate_meal, forbidden_terms):
            return candidate_meal

    fallback_locale = locale if locale in _ULTRA_SAFE_FALLBACK else "fa"
    fallback = _ULTRA_SAFE_FALLBACK[fallback_locale]
    return {
        **meal,
        "title": fallback["title"],
        "description": fallback.get("description", ""),
        "portion_guidance": fallback.get("portion_guidance"),
        "alternatives": [
            a for a in (fallback.get("alternatives") or [])
            if not _text_contains_forbidden(a, forbidden_terms)
        ],
        "preparation_notes": None,
        "food_items": fallback.get("food_items") or [],
    }


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


def canonical_meal_order_value(slot: str) -> int:
    """Return the 1-based canonical display order for a meal slot name. Unknown slots → 10."""
    try:
        return MEAL_ORDER.index(slot) + 1
    except ValueError:
        return len(MEAL_ORDER)


def sort_meals_canonically(meals: list[dict]) -> list[dict]:
    """Sort meal dicts by canonical slot order, then time_window_start, then id.

    Canonical slot order is always primary — persisted meal_order values are NOT
    used so stale DB values from older generated plans cannot affect display order.
    Upgrades legacy 'snack' slot by time_window_start before sorting.
    """
    def _key(m: dict) -> tuple:
        raw = (m.get("meal_slot") or m.get("meal_type") or "other").strip()
        slot = _infer_slot_from_time(raw, m.get("time_window_start"))
        idx = MEAL_ORDER.index(slot) if slot in MEAL_ORDER else len(MEAL_ORDER)
        return (idx, m.get("time_window_start") or "", str(m.get("id") or ""))
    return sorted(meals, key=_key)


_EXPENSIVE_TERMS: set[str] = {
    # English / internal
    "salmon", "quinoa", "avocado", "blueberry", "blueberries", "steak", "shrimp",
    "lobster", "protein powder", "protein shake", "caviar", "imported nuts",
    "cashew nut", "cashews", "brazil nut", "macadamia", "açaí", "acai",
    "truffle", "specialty supplement", "premium supplement",
    # Persian
    "سالمون", "کینوا", "آووکادو", "بلوبری", "استیک", "میگو", "خاویار",
    "پودر پروتئین", "شیک پروتئین", "مکمل گران", "مغز وارداتی",
    "بادام برزیلی", "ماکادمیا",
    # Arabic
    "سلمون", "كينوا", "أفوكادو", "توت أزرق", "ستيك", "جمبري", "كافيار",
    "بروتين بودرة",
}

_BUDGET_GUIDANCE: dict[str, dict[str, str]] = {
    "economic": {
        "fa": "این برنامه برای بودجه اقتصادی طراحی شده است. غذاهای ارزان‌قیمت و پرانرژی مثل حبوبات، مرغ، ماست، نان سبوس‌دار و سبزیجات فصلی پایه این برنامه هستند.",
        "en": "This plan is designed for an economic budget. Affordable, nutritious staples — legumes, chicken, yogurt, whole-grain bread, and seasonal vegetables — form the foundation.",
        "ar": "هذه الخطة مصممة لميزانية اقتصادية. تُشكّل الأطعمة المغذية والميسورة — البقوليات والدجاج والزبادي والخبز الكامل والخضار الموسمية — أساس الخطة.",
    },
    "standard": {
        "fa": "این برنامه برای بودجه معمولی طراحی شده است. تنوع غذایی مناسب با استفاده از مواد قابل دسترس و اقتصادی.",
        "en": "This plan is designed for a standard budget. Balanced variety using accessible, reasonably priced ingredients.",
        "ar": "هذه الخطة مصممة لميزانية عادية. تنوع متوازن باستخدام مكونات ميسورة ومعقولة السعر.",
    },
    "premium": {
        "fa": "این برنامه برای بودجه متنوع طراحی شده است. امکان استفاده از پروتئین‌های متنوع، ماهی بیشتر و محصولات لبنی خاص وجود دارد.",
        "en": "This plan is designed for a premium budget. Greater variety with lean meats, more fish, specialty dairy, and varied proteins is supported.",
        "ar": "هذه الخطة مصممة لميزانية متميزة. يُدعم التنوع الأكبر مع اللحوم الخالية من الدهون والأسماك ومنتجات الألبان المتنوعة.",
    },
    "unknown": {
        "fa": "برنامه با فرض بودجه معمولی طراحی شده است.",
        "en": "Plan designed assuming a standard budget.",
        "ar": "تم تصميم الخطة بافتراض ميزانية عادية.",
    },
}

_SHOPPING_NOTES: dict[str, dict[str, str]] = {
    "economic": {
        "fa": "خرید پیشنهادی: حبوبات خشک (عدس، لوبیا، نخود)، مرغ، ماست ساده، نان سبوس‌دار، سبزیجات فصلی، برنج، تخم‌مرغ (اگر آلرژی ندارید). از خرید عمده حبوبات و سبزیجات فصلی صرفه‌جویی کنید.",
        "en": "Shopping tip: Dry legumes (lentils, beans, chickpeas), chicken, plain yogurt, whole-grain bread, seasonal vegetables, rice, eggs (if no allergy). Buy legumes and seasonal produce in bulk to save cost.",
        "ar": "نصيحة للتسوق: البقوليات الجافة (العدس والفاصوليا والحمص) والدجاج والزبادي العادي والخبز الكامل والخضار الموسمية والأرز والبيض (إن لم يكن لديك حساسية). اشتر البقوليات والخضار الموسمية بالجملة لتوفير التكاليف.",
    },
    "standard": {
        "fa": "خرید پیشنهادی: مرغ، ماهی محلی، لبنیات، حبوبات، سبزیجات و میوه فصلی، غلات کامل.",
        "en": "Shopping tip: Chicken, local fish, dairy, legumes, seasonal vegetables and fruits, whole grains.",
        "ar": "نصيحة للتسوق: الدجاج والأسماك المحلية ومنتجات الألبان والبقوليات والخضار والفواكه الموسمية والحبوب الكاملة.",
    },
    "premium": {
        "fa": "خرید پیشنهادی: پروتئین‌های متنوع (ماهی، مرغ، گوشت کم‌چرب)، لبنیات خاص، مغزهای مجاز، میوه‌های متنوع، سبزیجات تازه.",
        "en": "Shopping tip: Varied proteins (fish, chicken, lean meat), specialty dairy, allowed nuts, diverse fruits, fresh vegetables.",
        "ar": "نصيحة للتسوق: بروتينات متنوعة (أسماك ودجاج ولحوم خالية من الدهون) ومنتجات ألبان متخصصة ومكسرات مسموح بها وفواكه متنوعة وخضار طازجة.",
    },
    "unknown": {
        "fa": "خرید پیشنهادی: مواد غذایی اصلی متناسب با اهداف برنامه.",
        "en": "Shopping tip: Core ingredients appropriate for the plan's goals.",
        "ar": "نصيحة للتسوق: المكونات الأساسية المناسبة لأهداف الخطة.",
    },
}


def _meal_contains_expensive(meal: dict) -> bool:
    for field in ("title", "description", "portion_guidance", "preparation_notes"):
        text = (meal.get(field) or "").lower()
        if any(term in text for term in _EXPENSIVE_TERMS):
            return True
    for item in (meal.get("food_items") or []):
        if isinstance(item, dict):
            name = (item.get("name") or "").lower()
            if any(term in name for term in _EXPENSIVE_TERMS):
                return True
    return False


def _enforce_budget_tier(
    days: list[dict],
    budget_tier: str,
    locale: str,
    forbidden_terms: set[str],
) -> list[dict]:
    """For economic budget: replace obviously expensive meals with affordable ones."""
    if budget_tier != "economic":
        return days
    result = []
    for day in days:
        meals = list(day.get("meals") or [])
        updated_meals = []
        for meal in meals:
            if _meal_contains_expensive(meal):
                logger.info(
                    "Budget enforcement (economic): replacing expensive meal '%s'",
                    meal.get("title", ""),
                )
                replacement = _safe_replacement(meal, locale, forbidden_terms)
                updated_meals.append(replacement)
            else:
                updated_meals.append(meal)
        result.append({**day, "meals": updated_meals})
    return result


# ─── Safe replacement strings for day-level allergen repair ──────────────────

_SAFE_HYDRATION_GUIDANCE: dict[str, str] = {
    "fa": "آب کافی در طول روز بنوشید و از نوشیدنی‌های طبیعی مجاز استفاده کنید.",
    "en": "Drink enough water throughout the day and choose naturally safe beverages.",
    "ar": "اشرب كمية كافية من الماء طوال اليوم واختر المشروبات الطبيعية الآمنة.",
}

_SAFE_RESTAURANT_GUIDANCE: dict[str, str] = {
    "fa": "در رستوران و مسافرت، غذاهای ساده مجاز را انتخاب کنید و درباره آلرژن‌ها از پرسنل بپرسید.",
    "en": "At restaurants and while traveling, choose simple allowed foods and ask staff about allergen content.",
    "ar": "في المطاعم وأثناء السفر، اختر الأطعمة البسيطة المسموح بها واسأل الموظفين عن مسببات الحساسية.",
}

_SAFE_SUPPLEMENTS_GUIDANCE: dict[str, str] = {
    "fa": "با پزشک یا متخصص تغذیه در مورد مکمل‌های مناسب برای شما مشورت کنید.",
    "en": "Consult your doctor or dietitian about appropriate supplements for your specific needs.",
    "ar": "استشر طبيبك أو أخصائي التغذية حول المكملات الغذائية المناسبة لاحتياجاتك.",
}

_SAFE_CHEAT_MEAL_GUIDANCE: dict[str, str] = {
    "fa": "اگر وعده‌ای آزاد می‌خواهید، از غذاهایی استفاده کنید که با آلرژی‌های شما سازگار باشند.",
    "en": "If you want a flexible meal, choose foods that are safe and compatible with your allergies.",
    "ar": "إذا أردت وجبة مرنة، اختر أطعمة آمنة ومتوافقة مع حساسيتك الغذائية.",
}


def _build_allergen_safe_budget_guidance(locale: str, budget_tier: str, active_allergens: set[str]) -> str:
    if budget_tier == "economic":
        return _build_economic_budget_guidance(locale, active_allergens)
    phrases = {
        "fa": "این برنامه غذایی با توجه به محدودیت‌های تغذیه‌ای شما طراحی شده است.",
        "en": "This meal plan is designed with your dietary restrictions in mind.",
        "ar": "تم تصميم هذه الخطة الغذائية مع مراعاة قيودك الغذائية.",
    }
    return phrases.get(locale, phrases["fa"])


def _build_allergen_safe_shopping_notes(locale: str, budget_tier: str, active_allergens: set[str]) -> str:
    if budget_tier == "economic":
        return _build_economic_shopping_notes(locale, active_allergens)
    phrases = {
        "fa": "خرید پیشنهادی: مواد غذایی مجاز و متناسب با محدودیت‌های تغذیه‌ای شما.",
        "en": "Shopping tip: Choose foods that are safe and compatible with your dietary restrictions.",
        "ar": "نصيحة للتسوق: اختر الأطعمة الآمنة والمتوافقة مع قيودك الغذائية.",
    }
    return phrases.get(locale, phrases["fa"])


def _infer_slot_from_time(slot: str, time_window_start: str | None) -> str:
    """For legacy 'snack' slot, upgrade to a specific slot based on time of day."""
    if slot != "snack" or not time_window_start:
        return slot
    try:
        hour = int(str(time_window_start).split(":")[0])
        if hour < 12:
            return "morning_snack"
        elif hour < 17:
            return "afternoon_snack"
        elif hour >= 20:
            return "optional_evening_snack"
    except (ValueError, AttributeError, IndexError):
        pass
    return slot


def _clean_string_list(items: list, forbidden_terms: set[str]) -> list:
    return [item for item in items if isinstance(item, str) and not _text_contains_forbidden(item, forbidden_terms)]


def _repair_meal_in_final_pass(meal: dict, locale: str, forbidden_terms: set[str]) -> dict:
    """Final-pass repair: replace any meal still containing forbidden terms after the main loop."""
    if not forbidden_terms:
        return meal

    has_forbidden = any(
        _text_contains_forbidden(meal.get(f), forbidden_terms)
        for f in ("title", "description", "portion_guidance", "preparation_notes",
                  "rest_day_note", "drink_guidance", "workout_relation")
    )
    if not has_forbidden:
        has_forbidden = any(
            isinstance(item, dict) and _text_contains_forbidden(item.get("name"), forbidden_terms)
            for item in (meal.get("food_items") or [])
        )
    if not has_forbidden:
        has_forbidden = any(
            _text_contains_forbidden(alt, forbidden_terms)
            for alt in (meal.get("alternatives") or [])
        )

    if not has_forbidden:
        return meal

    logger.warning(
        "Final pass: replacing meal '%s' (slot=%s) still containing forbidden terms",
        meal.get("title", ""), meal.get("meal_slot", ""),
    )
    replacement = _safe_replacement(meal, locale, forbidden_terms)
    if _meal_is_safe(replacement, forbidden_terms):
        return replacement

    fallback_locale = locale if locale in _ULTRA_SAFE_FALLBACK else "fa"
    fallback = _ULTRA_SAFE_FALLBACK[fallback_locale]
    return {
        **meal,
        "title": fallback["title"],
        "description": fallback.get("description", ""),
        "portion_guidance": fallback.get("portion_guidance"),
        "alternatives": [],
        "preparation_notes": None,
        "drink_guidance": None,
        "workout_relation": None,
        "rest_day_note": None,
        "food_items": fallback.get("food_items") or [],
    }


def _repair_day_level_fields(
    day: dict,
    forbidden_terms: set[str],
    budget_tier: str,
    active_allergens: set[str],
    locale: str,
) -> dict:
    """Repair all day-level string and list fields that still contain forbidden terms."""
    if not forbidden_terms:
        return day

    day = dict(day)

    for field in ("hydration_plan", "drinks_plan"):
        if _text_contains_forbidden(day.get(field), forbidden_terms):
            logger.info("Repairing forbidden term in day.%s", field)
            day[field] = _SAFE_HYDRATION_GUIDANCE.get(locale, _SAFE_HYDRATION_GUIDANCE["fa"])

    if _text_contains_forbidden(day.get("restaurant_party_travel_guidance"), forbidden_terms):
        logger.info("Repairing forbidden term in day.restaurant_party_travel_guidance")
        day["restaurant_party_travel_guidance"] = _SAFE_RESTAURANT_GUIDANCE.get(locale, _SAFE_RESTAURANT_GUIDANCE["fa"])

    if _text_contains_forbidden(day.get("supplements_vitamins_guidance"), forbidden_terms):
        logger.info("Repairing forbidden term in day.supplements_vitamins_guidance")
        day["supplements_vitamins_guidance"] = _SAFE_SUPPLEMENTS_GUIDANCE.get(locale, _SAFE_SUPPLEMENTS_GUIDANCE["fa"])

    if _text_contains_forbidden(day.get("cheat_meal_guidance"), forbidden_terms):
        logger.info("Repairing forbidden term in day.cheat_meal_guidance")
        day["cheat_meal_guidance"] = _SAFE_CHEAT_MEAL_GUIDANCE.get(locale, _SAFE_CHEAT_MEAL_GUIDANCE["fa"])

    if _text_contains_forbidden(day.get("budget_guidance"), forbidden_terms):
        logger.info("Repairing forbidden term in day.budget_guidance")
        day["budget_guidance"] = _build_allergen_safe_budget_guidance(locale, budget_tier, active_allergens)

    if _text_contains_forbidden(day.get("shopping_notes"), forbidden_terms):
        logger.info("Repairing forbidden term in day.shopping_notes")
        day["shopping_notes"] = _build_allergen_safe_shopping_notes(locale, budget_tier, active_allergens)

    for field in ("summary", "training_guidance", "sleep_wake_guidance", "notes",
                  "hydration_goal", "progress_tracking_guidance", "adjustment_rules"):
        if _text_contains_forbidden(day.get(field), forbidden_terms):
            logger.info("Nullifying day.%s containing forbidden term", field)
            day[field] = None

    for field in ("allowed_foods", "limited_foods", "warnings", "medical_warnings"):
        items = day.get(field)
        if isinstance(items, list):
            cleaned = _clean_string_list(items, forbidden_terms)
            if len(cleaned) != len(items):
                logger.info("Removed %d forbidden items from day.%s", len(items) - len(cleaned), field)
                day[field] = cleaned

    return day


def _final_recursive_repair(
    days: list[dict],
    forbidden_terms: set[str],
    budget_tier: str,
    active_allergens: set[str],
    locale: str,
) -> list[dict]:
    """Full recursive scan and repair of all user-visible fields across all days."""
    if not forbidden_terms:
        return days

    result = []
    for day in days:
        meals = [_repair_meal_in_final_pass(m, locale, forbidden_terms) for m in (day.get("meals") or [])]
        day_repaired = _repair_day_level_fields(
            {**day, "meals": meals},
            forbidden_terms, budget_tier, active_allergens, locale,
        )
        result.append(day_repaired)
    return result


_VAGUE_PORTION_WORDS: frozenset[str] = frozenset({
    "کنترل‌شده", "کنترل شده", "مقدار مناسب", "مقداری",
    "به مقدار", "به اندازه کافی", "متعادل", "کمی",
})

_POLO_DISHES_REPAIR: list[tuple[str, str]] = [
    ("لوبیاپلو", "۸ قاشق غذاخوری لوبیاپلو"),
    ("عدس‌پلو", "۸ قاشق غذاخوری عدس‌پلو"),
    ("عدس پلو", "۸ قاشق غذاخوری عدس‌پلو"),
    ("سبزی‌پلو", "۷ قاشق غذاخوری سبزی‌پلو"),
    ("سبزی پلو", "۷ قاشق غذاخوری سبزی‌پلو"),
    ("باقالی پلو", "۸ قاشق غذاخوری باقالی‌پلو"),
    ("ماش پلو", "۸ قاشق غذاخوری ماش‌پلو"),
    ("شوید پلو", "۷ قاشق غذاخوری شوید‌پلو"),
    ("استانبولی", "۸ قاشق غذاخوری استانبولی"),
    ("ماکارونی", "۸ قاشق غذاخوری ماکارونی"),
]

_STEW_NAME_MAP: dict[str, str] = {
    "قرمه‌سبزی": "خورش قرمه‌سبزی",
    "قرمه سبزی": "خورش قرمه‌سبزی",
    "قیمه": "خورش قیمه",
    "فسنجان": "خورش فسنجان",
    "کرفس": "خورش کرفس",
    "خوراک مرغ": "خوراک مرغ",
}


def _portion_guidance_is_vague(guidance: str | None) -> bool:
    """Return True when portion_guidance is missing or contains vague phrases."""
    if not guidance or not guidance.strip():
        return True
    for word in _VAGUE_PORTION_WORDS:
        if word in guidance:
            return True
    # "برش نان" without "کف دست" is still vague
    if "برش نان" in guidance and "کف دست" not in guidance:
        return True
    return False


def _repair_portion_guidance(meal: dict, active_allergens: set[str]) -> str:
    """Infer practical household-unit portion guidance from meal title/description."""
    title = (meal.get("title") or "").lower()
    desc = (meal.get("description") or "").lower()
    combined = f"{title} {desc}"

    # 1. Mixed polo / one-pot dishes (must check before plain rice)
    for dish, guidance in _POLO_DISHES_REPAIR:
        if dish.lower() in combined:
            return guidance

    # 2. Rice + stew
    has_rice = "برنج" in combined
    has_stew = "خورش" in combined or any(k.lower() in combined for k in _STEW_NAME_MAP)
    if has_rice and has_stew:
        stew_label = "خورش"
        for key, label in _STEW_NAME_MAP.items():
            if key.lower() in combined:
                stew_label = label
                break
        return f"۵ قاشق غذاخوری برنج + ۴ قاشق غذاخوری {stew_label}"

    # 3. Plain rice
    if has_rice:
        return "۸ قاشق غذاخوری برنج"

    # 4. Bread — skip if gluten allergy
    if "نان" in combined and "gluten" not in active_allergens:
        return "۲ کف دست نان"

    # 5. Protein
    if "مرغ" in combined:
        return "۱ کف دست مرغ پخته، حدود ۱۲۰ گرم"
    if "گوشت" in combined:
        return "۱ کف دست گوشت کم‌چرب، حدود ۱۰۰ گرم"
    if "ماهی" in combined:
        return "۱ کف دست ماهی پخته، حدود ۱۲۰ گرم"

    # 6. Dairy — skip if lactose allergy
    if "ماست" in combined and "lactose" not in active_allergens:
        return "۱ کاسه کوچک ماست، حدود ۱۵۰ گرم"
    if "پنیر" in combined and "lactose" not in active_allergens:
        return "پنیر به اندازه ۱ قوطی کبریت"

    # 7. Salad / vegetables
    if "سالاد" in combined:
        return "۱ کاسه متوسط سالاد"
    if "سبزیجات" in combined or "سبزی" in combined:
        return "۱ تا ۲ کاسه سبزیجات"

    # 8. Soup / legume
    if "سوپ" in combined or "عدسی" in combined or "آش" in combined:
        return "۱ کاسه متوسط"

    # 9. Fruit
    if any(f in combined for f in ("میوه", "سیب", "موز", "پرتقال", "گلابی")):
        return "۱ عدد متوسط"

    # Generic measurable fallback
    return "یک وعده متوسط با اندازه‌گیری خانگی: ۱ کاسه متوسط یا طبق مقدار ذکرشده در آیتم‌های غذایی"


def collect_user_visible_text(plan: dict) -> str:
    """Collect all user-visible text from a validated plan (used in tests and safety assertions)."""
    _DAY_STR = (
        "title", "summary", "hydration_goal", "hydration_plan", "drinks_plan",
        "training_guidance", "sleep_wake_guidance", "cheat_meal_guidance",
        "budget_guidance", "shopping_notes", "restaurant_party_travel_guidance",
        "supplements_vitamins_guidance", "progress_tracking_guidance",
        "adjustment_rules", "notes",
    )
    _DAY_LIST = ("allowed_foods", "limited_foods", "warnings", "medical_warnings")
    _MEAL_STR = (
        "title", "description", "portion_guidance", "preparation_notes",
        "rest_day_note", "drink_guidance", "workout_relation",
    )
    parts: list[str] = []
    for day in plan.get("days") or []:
        for f in _DAY_STR:
            v = day.get(f)
            if v:
                parts.append(str(v))
        for f in _DAY_LIST:
            for item in (day.get(f) or []):
                if item:
                    parts.append(str(item))
        for meal in (day.get("meals") or []):
            for f in _MEAL_STR:
                v = meal.get(f)
                if v:
                    parts.append(str(v))
            for alt in (meal.get("alternatives") or []):
                if alt:
                    parts.append(str(alt))
            for fi in (meal.get("food_items") or []):
                if isinstance(fi, dict) and fi.get("name"):
                    parts.append(str(fi["name"]))
    return " ".join(parts).lower()


# ── Premium Persian lunch pool (used when budget=premium and locale=fa) ──────
_PREMIUM_PERSIAN_LUNCHES = [
    {
        "title": "ناهار: قورمه‌سبزی با گوشت و برنج",
        "description": "۱۵۰ گرم گوشت گوسفند در قورمه‌سبزی + ۸ قاشق غذاخوری برنج پخته + سبزی‌خوردن آزاد",
        "portion_guidance": "۱۵۰ گرم گوشت + ۸ قاشق برنج + سبزی‌خوردن آزاد",
        "alternatives": ["چلوکباب کوبیده با برنج", "خورشت فسنجان با مرغ"],
    },
    {
        "title": "ناهار: چلوکباب کوبیده",
        "description": "۲ سیخ کباب کوبیده گوشت مخلوط (۲۰۰ گرم) + ۸ قاشق برنج پخته + گوجه کبابی + سبزی‌خوردن",
        "portion_guidance": "۲ سیخ کباب (۲۰۰ گرم) + ۸ قاشق برنج",
        "alternatives": ["چلوکباب برگ", "جوجه‌کباب با برنج"],
    },
    {
        "title": "ناهار: جوجه‌کباب با برنج",
        "description": "۱۸۰ گرم جوجه‌کباب گریل‌شده + ۸ قاشق غذاخوری برنج پخته + سالاد شیرازی + سبزی‌خوردن",
        "portion_guidance": "۱۸۰ گرم جوجه + ۸ قاشق برنج + سالاد شیرازی",
        "alternatives": ["زرشک‌پلو با مرغ", "کباب تابه‌ای کم‌روغن با برنج"],
    },
    {
        "title": "ناهار: خورشت فسنجان با مرغ و برنج",
        "description": "۱۵۰ گرم مرغ در خورشت فسنجان + ۸ قاشق برنج پخته + سبزی‌خوردن",
        "portion_guidance": "۱۵۰ گرم مرغ + ۸ قاشق برنج",
        "alternatives": ["قورمه‌سبزی با گوشت", "چلوکباب کوبیده"],
    },
    {
        "title": "ناهار: ماهی سالمون گریل با سبزیجات",
        "description": "۲۰۰ گرم فیله سالمون گریل‌شده + ۸ قاشق برنج یا سیب‌زمینی پخته + سالاد فصل",
        "portion_guidance": "۲۰۰ گرم سالمون + ۸ قاشق برنج + سالاد",
        "alternatives": ["سبزی‌پلو با ماهی سفید", "میگو گریل با سبزیجات"],
    },
    {
        "title": "ناهار: زرشک‌پلو با مرغ",
        "description": "۱۵۰ گرم مرغ (ران یا سینه) + ۸ قاشق زرشک‌پلو + سالاد شیرازی",
        "portion_guidance": "۱۵۰ گرم مرغ + ۸ قاشق زرشک‌پلو + سالاد",
        "alternatives": ["جوجه‌کباب با برنج", "خورشت مرغ با برنج"],
    },
    {
        "title": "ناهار: کباب برگ با برنج",
        "description": "۲ سیخ کباب برگ (فیله گوسفند ۱۸۰ گرم) + ۸ قاشق برنج پخته + گوجه کبابی",
        "portion_guidance": "۲ سیخ کباب (۱۸۰ گرم) + ۸ قاشق برنج",
        "alternatives": ["چلوکباب کوبیده", "جوجه‌کباب با برنج"],
    },
]

_PREMIUM_PROTEIN_KEYWORDS = (
    "جوجه", "مرغ", "گوشت", "کباب", "فسنجان", "قورمه", "ماهی", "سالمون",
    "زرشک‌پلو", "میگو", "فیله", "گوساله", "گوسفند",
)

_ECONOMIC_LUNCH_KEYWORDS = ("عدس", "لوبیا", "آش", "سوپ", "کوکو سبزی", "ماش")


def _lunch_is_premium_protein(meal: dict) -> bool:
    title = (meal.get("title") or "").lower()
    desc = (meal.get("description") or "").lower()
    text = title + " " + desc
    return any(kw in text for kw in _PREMIUM_PROTEIN_KEYWORDS)


def _enforce_premium_persian_lunches(days: list[dict]) -> list[dict]:
    """For premium Persian plans: ensure ≥5 of 7 lunches have premium animal protein."""
    if len(days) < 7:
        return days

    lunch_indices: list[tuple[int, int]] = []  # (day_idx, meal_idx)
    premium_count = 0
    for d_idx, day in enumerate(days):
        for m_idx, meal in enumerate(day.get("meals") or []):
            if (meal.get("meal_type") or meal.get("meal_slot") or "") == "lunch":
                lunch_indices.append((d_idx, m_idx))
                if _lunch_is_premium_protein(meal):
                    premium_count += 1

    if premium_count >= 5:
        return days  # already good

    result = [dict(d) for d in days]
    pool_idx = 0
    needed = 5 - premium_count

    for d_idx, m_idx in lunch_indices:
        if needed <= 0:
            break
        day_meals = list(result[d_idx].get("meals") or [])
        meal = day_meals[m_idx]
        if _lunch_is_premium_protein(meal):
            continue
        replacement = dict(_PREMIUM_PERSIAN_LUNCHES[pool_idx % len(_PREMIUM_PERSIAN_LUNCHES)])
        replacement["meal_type"] = "lunch"
        replacement["meal_slot"] = "lunch"
        replacement["preparation_notes"] = None
        day_meals[m_idx] = replacement
        result[d_idx] = {**result[d_idx], "meals": day_meals}
        pool_idx += 1
        needed -= 1
        logger.info("Replaced economic lunch on day %d with premium: %s", d_idx + 1, replacement["title"])

    return result


def _inject_cheating_date(days: list[dict], locale: str) -> list[dict]:
    """Ensure exactly one cheating_date meal exists on day 5 or 6 (1-indexed)."""
    _CHEAT_DESCRIPTIONS = {
        "fa": (
            "یک وعده انعطاف‌پذیر برنامه‌ریزی‌شده — مثلاً جوجه‌کباب یا چلوکباب در رستوران، "
            "یا غذای مورد علاقه با حجم کنترل‌شده. وعده بعدی به برنامه عادی برمی‌گردد. "
            "زمان پیشنهادی: ۲۰ تا ۲۲."
        ),
        "en": (
            "A planned flexible meal — e.g. grilled chicken or kebab at a restaurant, "
            "or a favourite food in a controlled portion. Next meal returns to plan. "
            "Suggested time: 20:00–22:00."
        ),
        "ar": (
            "وجبة مرنة مخططة — مثلاً دجاج مشوي أو كباب في مطعم، "
            "أو طعام مفضل بكمية محكومة. الوجبة التالية تعود إلى الخطة. "
            "الوقت المقترح: 20:00–22:00."
        ),
    }
    cheat_desc = _CHEAT_DESCRIPTIONS.get(locale, _CHEAT_DESCRIPTIONS["fa"])
    cheat_meal = {
        "meal_type": "cheating_date",
        "meal_slot": "cheating_date",
        "title": "Cheating Date",
        "description": cheat_desc,
        "portion_guidance": "حجم کنترل‌شده: نه بیشتر از ۱ تا ۲ واحد غذای دلخواه" if locale == "fa"
                            else "Controlled portion: no more than 1–2 servings of chosen food",
        "alternatives": [],
        "preparation_notes": None,
        "time_window_start": "20:00",
        "time_window_end": "22:00",
        "meal_order": 9,
    }

    # Check if any day already has a cheating_date meal
    def _has_cheat(day: dict) -> bool:
        return any(
            (m.get("meal_type") or m.get("meal_slot") or "") in ("cheating_date", "controlled_cheating")
            for m in (day.get("meals") or [])
        )

    already_has = any(_has_cheat(d) for d in days)
    if already_has:
        # Normalise controlled_cheating → cheating_date
        result = []
        for day in days:
            updated_meals = []
            for m in (day.get("meals") or []):
                mt = m.get("meal_type") or m.get("meal_slot") or ""
                if mt == "controlled_cheating":
                    m = {**m, "meal_type": "cheating_date", "meal_slot": "cheating_date",
                         "title": "Cheating Date"}
                updated_meals.append(m)
            result.append({**day, "meals": updated_meals})
        return result

    # Prefer day 6 (index 5), fallback to day 5 (index 4)
    if len(days) < 5:
        return days
    target_idx = 5 if len(days) >= 6 else 4
    result = list(days)
    day = dict(result[target_idx])
    day["meals"] = list(day.get("meals") or []) + [cheat_meal]
    result[target_idx] = day
    logger.info("Injected Cheating Date meal on day %d", target_idx + 1)
    return result


def validate_and_sanitize(plan_data: dict, ctx: NutritionMemoryContext, locale: str = "fa") -> dict:
    """Validate and sanitize a generated week plan dict. Returns cleaned plan."""
    forbidden_terms = _build_forbidden_terms(ctx)
    active_allergens = _detect_active_allergen_groups(forbidden_terms)
    days = list(plan_data.get("days") or [])

    # Ensure at most 7 days
    days = days[:7]

    budget_tier = normalize_budget_tier(ctx.food_budget)

    # Build default budget guidance/shopping notes — allergen-aware for all budget tiers
    if budget_tier == "economic" and active_allergens:
        default_budget_guidance = _build_economic_budget_guidance(locale, active_allergens)
        default_shopping_notes = _build_economic_shopping_notes(locale, active_allergens)
    else:
        default_budget_guidance = _BUDGET_GUIDANCE.get(budget_tier, _BUDGET_GUIDANCE["unknown"]).get(locale, "")
        default_shopping_notes = _SHOPPING_NOTES.get(budget_tier, _SHOPPING_NOTES["unknown"]).get(locale, "")
        # Static notes for standard/premium budgets may reference allergen foods (e.g. "لبنیات")
        if active_allergens and forbidden_terms:
            if _text_contains_forbidden(default_budget_guidance, forbidden_terms):
                default_budget_guidance = _build_allergen_safe_budget_guidance(locale, budget_tier, active_allergens)
            if _text_contains_forbidden(default_shopping_notes, forbidden_terms):
                default_shopping_notes = _build_allergen_safe_shopping_notes(locale, budget_tier, active_allergens)

    sanitized_days = []
    for day in days:
        meals = list(day.get("meals") or [])
        sanitized_meals = []
        for meal in meals:
            # Set meal_slot from meal_type if missing
            if not meal.get("meal_slot") and meal.get("meal_type"):
                meal = {**meal, "meal_slot": meal["meal_type"]}
            # Upgrade legacy "snack" slot to a specific slot based on time of day
            if (meal.get("meal_slot") or meal.get("meal_type")) == "snack":
                upgraded = _infer_slot_from_time("snack", meal.get("time_window_start"))
                if upgraded != "snack":
                    meal = {**meal, "meal_slot": upgraded}

            if not _meal_is_safe(meal, forbidden_terms):
                logger.info("Replacing unsafe meal '%s' (slot=%s)", meal.get("title", ""), meal.get("meal_slot", ""))
                meal = _safe_replacement(meal, locale, forbidden_terms)
            else:
                meal = _clean_alternatives(meal, forbidden_terms)

            # Repair vague portion guidance (locale=fa only; en/ar get raw AI output)
            if locale == "fa" and _portion_guidance_is_vague(meal.get("portion_guidance")):
                repaired = _repair_portion_guidance(meal, active_allergens)
                meal = {**meal, "portion_guidance": repaired}
                logger.info("Repaired vague portion_guidance for meal '%s'", meal.get("title", ""))

            sanitized_meals.append(meal)

        # Sort by canonical meal order, then stamp 1-based meal_order for stable DB storage
        sanitized_meals.sort(key=_meal_order_key)
        for idx, meal in enumerate(sanitized_meals):
            sanitized_meals[idx] = {**meal, "meal_order": _meal_order_key(meal) + 1}

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

        # Select budget guidance/shopping notes; repair AI-provided values that contain allergens
        day_bg = day.get("budget_guidance")
        if day_bg and forbidden_terms and _text_contains_forbidden(day_bg, forbidden_terms):
            day_bg = _build_allergen_safe_budget_guidance(locale, budget_tier, active_allergens)
        if not day_bg:
            day_bg = default_budget_guidance

        day_sn = day.get("shopping_notes")
        if day_sn and forbidden_terms and _text_contains_forbidden(day_sn, forbidden_terms):
            day_sn = _build_allergen_safe_shopping_notes(locale, budget_tier, active_allergens)
        if not day_sn:
            day_sn = default_shopping_notes

        sanitized_days.append({
            **day,
            "meals": sanitized_meals,
            "warnings": day_warnings,
            "budget_tier": budget_tier,
            "budget_guidance": day_bg,
            "shopping_notes": day_sn,
        })

    # Apply budget enforcement (economic: replace expensive meals) after allergy pass
    sanitized_days = _enforce_budget_tier(sanitized_days, budget_tier, locale, forbidden_terms)

    # Quality gate A: ensure Cheating Date meal on day 5 or 6 (all plans)
    sanitized_days = _inject_cheating_date(sanitized_days, locale)

    # Quality gate B: for premium Persian plans, enforce ≥5 premium-protein lunches
    if budget_tier == "premium" and locale == "fa":
        sanitized_days = _enforce_premium_persian_lunches(sanitized_days)

    # Final recursive repair: scan and fix all user-visible fields across all days
    sanitized_days = _final_recursive_repair(
        sanitized_days, forbidden_terms, budget_tier, active_allergens, locale
    )

    return {**plan_data, "days": sanitized_days}
