"""
MockAIProvider: deterministic Persian-friendly structured responses.

No external API calls. App works fully end-to-end with this provider.
PromptBuilder embeds TASK:<type> markers that this provider reads to pick the right mock.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.services.ai_provider import AIProvider, AIProviderResult

if TYPE_CHECKING:
    from app.services.nutrition_memory_service import NutritionMemoryContext

# Task markers injected by PromptBuilder into the system message
TASK_GENERATE_PLAN = "TASK:generate_plan"
TASK_ANALYZE_MEAL = "TASK:analyze_meal"
TASK_WHAT_TO_EAT = "TASK:what_to_eat_now"
TASK_ADAPT_PLAN = "TASK:adapt_plan"
TASK_CHAT = "TASK:chat_message"
TASK_CRAVING_SUPPORT = "TASK:craving_support"
TASK_SLIP_RECOVERY = "TASK:slip_recovery"
TASK_CONTEXT_GUIDANCE = "TASK:context_guidance"
TASK_GENERATE_WEEK_FA = "TASK:generate_week_fa"
TASK_GENERATE_WEEK_EN = "TASK:generate_week_en"
TASK_GENERATE_WEEK_AR = "TASK:generate_week_ar"
TASK_WEEKLY_REPORT = "TASK:weekly_report"


def _make_week_fa() -> dict:
    days = [
        {
            "day_index": 1,
            "title": "روز اول — شروع سبک",
            "summary": "یک روز شروع آرام با وعده‌های ساده و مقوی.",
            "hydration_goal": "حداقل ۸ لیوان آب در طول روز",
            "notes": "از غذاهای سرخ‌شده پرهیز کنید.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: نان و پنیر با گردو",
                    "description": "نان سبوس‌دار با پنیر کم‌چرب، گردو و چای کمرنگ",
                    "portion_guidance": "دو برش نان، ۳۰ گرم پنیر",
                    "alternatives": ["ماست با میوه", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: قورمه‌سبزی با برنج",
                    "description": "خورشت قورمه‌سبزی خانگی با برنج کنترل‌شده و سالاد شیرازی",
                    "portion_guidance": "یک کاسه کوچک برنج، یک کاسه خورشت",
                    "alternatives": ["عدسی با نان", "کوکو سبزی"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: عدسی با ماست",
                    "description": "سوپ عدس با ادویه ملایم و ماست کم‌چرب و سبزی خوردن",
                    "portion_guidance": "یک کاسه متوسط سوپ، یک کاسه کوچک ماست",
                    "alternatives": ["سوپ سبزیجات", "لبو با نان"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: میوه و آجیل",
                    "description": "یک عدد میوه فصلی با مشتی گردو یا بادام",
                    "portion_guidance": "یک عدد میوه، ۲۰ تا ۳۰ گرم آجیل",
                    "alternatives": ["ماست کم‌چرب", "هویج خام"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 2,
            "title": "روز دوم — انرژی متعادل",
            "summary": "تمرکز بر پروتئین و سبزیجات تازه.",
            "hydration_goal": "۸ لیوان آب یا دوغ کم‌نمک",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: نان و پنیر و گردو",
                    "description": "نان سبوس‌دار با پنیر کم‌چرب، گردو و چای کمرنگ",
                    "portion_guidance": "دو برش نان، ۳۰ گرم پنیر، ۵ عدد گردو",
                    "alternatives": ["ماست با عسل", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: کوکو سبزی با سالاد",
                    "description": "کوکو سبزی خانگی با سالاد فصل و نان",
                    "portion_guidance": "دو تکه کوکو، یک بشقاب سالاد",
                    "alternatives": ["آش رشته", "جوجه کباب با سالاد"],
                    "preparation_notes": "با روغن زیتون بپزید.",
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: سوپ مرغ و سبزیجات",
                    "description": "سوپ سبک با مرغ، هویج، و کرفس",
                    "portion_guidance": "یک کاسه بزرگ سوپ با نان",
                    "alternatives": ["ماهی بخارپز", "مرغ آب‌پز با سبزیجات"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: ماست با خیار",
                    "description": "ماست کم‌چرب با خیار رنده‌شده و نعنا",
                    "portion_guidance": "یک کاسه کوچک",
                    "alternatives": ["میوه فصلی", "هویج با ماست"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 3,
            "title": "روز سوم — فیبر و سبزیجات",
            "summary": "روزی با تأکید بر سبزیجات و فیبر برای سلامت گوارش.",
            "hydration_goal": "۸ تا ۱۰ لیوان آب",
            "notes": "از نان سفید کمتر استفاده کنید.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: ماست با میوه",
                    "description": "ماست کم‌چرب با میوه فصلی، عسل طبیعی و کمی دارچین",
                    "portion_guidance": "یک کاسه ماست، یک عدد میوه",
                    "alternatives": ["پنیر با گوجه", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: آش رشته",
                    "description": "آش رشته خانگی با آب‌لیمو و نعنا داغ",
                    "portion_guidance": "یک کاسه متوسط آش",
                    "alternatives": ["قرمه‌سبزی با برنج", "لوبیاپلو"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: عدسی با سالاد",
                    "description": "عدسی گرم با سالاد ساده",
                    "portion_guidance": "یک کاسه متوسط عدسی، یک بشقاب سالاد",
                    "alternatives": ["سوپ جو", "لوبیا پخته"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: هویج و کرفس",
                    "description": "هویج و کرفس خام با کمی ماست یا آب‌لیمو",
                    "portion_guidance": "یک مشت سبزیجات خام",
                    "alternatives": ["بادام", "سیب"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 4,
            "title": "روز چهارم — پروتئین سالم",
            "summary": "تمرکز بر پروتئین‌های سالم و کربوهیدرات متعادل.",
            "hydration_goal": "۸ لیوان آب",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: ماست چکیده با گردو",
                    "description": "ماست چکیده با گردو و عسل طبیعی",
                    "portion_guidance": "یک کاسه ماست، ۵ عدد گردو، یک قاشق عسل",
                    "alternatives": ["پنیر و سبزی", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: مرغ با سبزیجات",
                    "description": "سینه مرغ بخارپز با سبزیجات فصلی و برنج کنترل‌شده",
                    "portion_guidance": "یک سینه مرغ، نصف کاسه برنج، یک بشقاب سبزیجات",
                    "alternatives": ["ماهی سالمون", "لبو پلو"],
                    "preparation_notes": "مرغ را بدون پوست بپزید.",
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: لوبیا پخته با نان",
                    "description": "لوبیا چیتی پخته با سیر، گوجه و نان سبوس‌دار",
                    "portion_guidance": "یک کاسه لوبیا، یک برش نان",
                    "alternatives": ["سوپ عدس", "کوکو سیب‌زمینی"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: دوغ و میوه",
                    "description": "یک لیوان دوغ کم‌نمک با یک عدد میوه فصلی",
                    "portion_guidance": "۲۵۰ میلی‌لیتر دوغ، یک میوه",
                    "alternatives": ["ماست", "آجیل"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 5,
            "title": "روز پنجم — تنوع غذایی",
            "summary": "تنوع در طعم‌ها برای حفظ انگیزه.",
            "hydration_goal": "۸ لیوان آب",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: عسل و گردو با ماست",
                    "description": "ماست کم‌چرب با عسل طبیعی، گردو و میوه فصلی",
                    "portion_guidance": "یک کاسه ماست، یک قاشق عسل، ۵ عدد گردو",
                    "alternatives": ["پنیر با نان", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: ماهی بخارپز با سبزیجات",
                    "description": "فیله ماهی بخارپز با لیمو، دیل و سبزیجات فصلی",
                    "portion_guidance": "۱۵۰ گرم ماهی، یک بشقاب سبزیجات",
                    "alternatives": ["مرغ گریل", "کباب کوبیده سبک"],
                    "preparation_notes": "با حداقل نمک بپزید.",
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: آش جو",
                    "description": "آش جو با سبزیجات تازه و یک قاشق آب‌لیمو",
                    "portion_guidance": "یک کاسه آش",
                    "alternatives": ["سوپ عدس", "عدسی"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: میوه فصلی",
                    "description": "یک عدد میوه فصلی تازه مثل سیب، گلابی یا هلو",
                    "portion_guidance": "یک عدد میوه متوسط",
                    "alternatives": ["بادام", "ماست"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 6,
            "title": "روز ششم — سبک و آرام",
            "summary": "وعده‌های سبک‌تر برای استراحت بدن.",
            "hydration_goal": "۸ لیوان آب",
            "notes": "امروز می‌توانید بیشتر استراحت کنید.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: چای با شیر و نان",
                    "description": "چای با کمی شیر، نان سبوس‌دار با کره کم‌نمک یا پنیر",
                    "portion_guidance": "یک فنجان چای، یک برش نان",
                    "alternatives": ["ماست با عسل", "میوه با آجیل"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: سبزی پلو با ماهی",
                    "description": "برنج با سبزیجات (شوید، جعفری) با ماهی سفید کوچک",
                    "portion_guidance": "نصف کاسه برنج، ۱۰۰ گرم ماهی",
                    "alternatives": ["کوکو سبزی", "مرغ با سبزیجات"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: سوپ سبزیجات",
                    "description": "سوپ سبک با سبزیجات مختلف، بدون خامه",
                    "portion_guidance": "یک کاسه بزرگ سوپ",
                    "alternatives": ["عدسی", "ماست با خیار و نان"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: کشمش و بادام",
                    "description": "مخلوط کشمش و بادام بدون نمک",
                    "portion_guidance": "یک مشت کوچک (۲۵ گرم)",
                    "alternatives": ["میوه فصلی", "ماست"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 7,
            "title": "روز هفتم — جمع‌بندی هفته",
            "summary": "روز آخر هفته — غذاهای مورد علاقه سالم را امتحان کنید.",
            "hydration_goal": "۸ تا ۱۰ لیوان آب",
            "notes": "هفته بعد می‌توانید برنامه جدید بسازید.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "صبحانه: ماست با میوه و گردو",
                    "description": "ماست کم‌چرب با میوه فصلی و گردو",
                    "portion_guidance": "یک کاسه ماست، یک میوه، ۵ عدد گردو",
                    "alternatives": ["پنیر و گردو", "نان و کره"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "ناهار: خوراک عدس با برنج",
                    "description": "عدس پخته با پیاز داغ، سیب‌زمینی و برنج کنترل‌شده",
                    "portion_guidance": "یک کاسه عدس، نصف کاسه برنج",
                    "alternatives": ["قورمه‌سبزی", "جوجه کباب"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "شام: کشک بادمجان",
                    "description": "کشک بادمجان با نان سبوس‌دار و سالاد",
                    "portion_guidance": "یک بشقاب کوچک کشک بادمجان، یک برش نان",
                    "alternatives": ["ماست با خیار", "سوپ"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "میان‌وعده: چای با بادام",
                    "description": "چای کمرنگ با ۵ عدد بادام یا گردو",
                    "portion_guidance": "یک فنجان چای، ۲۰ گرم آجیل",
                    "alternatives": ["میوه فصلی", "دوغ"],
                    "preparation_notes": None,
                },
            ],
        },
    ]
    return {"locale": "fa", "days": days}


def _make_week_en() -> dict:
    days = [
        {
            "day_index": 1,
            "title": "Day 1 — Gentle Start",
            "summary": "A calm first day with simple, nourishing meals.",
            "hydration_goal": "At least 8 glasses of water throughout the day",
            "notes": "Avoid fried foods today.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Bread and Cheese with Walnuts",
                    "description": "Whole-grain bread with low-fat cheese, walnuts, and light tea",
                    "portion_guidance": "Two slices of bread, 30g cheese, 5 walnuts",
                    "alternatives": ["Yogurt with fruit", "Oatmeal"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Herb Stew with Rice (Ghormeh Sabzi)",
                    "description": "Homemade herb stew (ghormeh sabzi) with a controlled rice portion and shirazi salad",
                    "portion_guidance": "One small bowl of rice, one bowl of stew",
                    "alternatives": ["Lentil soup with bread", "Herb frittata (kuku sabzi)"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Lentil Soup with Yogurt",
                    "description": "Light lentil soup with mild spices, low-fat yogurt, and fresh herbs",
                    "portion_guidance": "One medium bowl of soup, one small bowl of yogurt",
                    "alternatives": ["Vegetable soup", "Beet with bread"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Fruit and Nuts",
                    "description": "One seasonal fruit with a handful of walnuts or almonds",
                    "portion_guidance": "One fruit, 20–30 g nuts",
                    "alternatives": ["Low-fat yogurt", "Raw carrot sticks"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 2,
            "title": "Day 2 — Balanced Energy",
            "summary": "Focus on protein and fresh vegetables.",
            "hydration_goal": "8 glasses of water or low-salt yogurt drink (doogh)",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Whole-Grain Bread with Cheese and Walnuts",
                    "description": "Whole-grain bread with low-fat cheese, walnuts, and light tea",
                    "portion_guidance": "Two slices of bread, 30 g cheese, 5 walnuts",
                    "alternatives": ["Yogurt with honey", "Cheese with bread"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Herb Frittata (Kuku Sabzi) with Salad",
                    "description": "Homemade herb frittata with seasonal salad and bread",
                    "portion_guidance": "Two pieces of frittata, one plate of salad",
                    "alternatives": ["Thick noodle soup (ash reshteh)", "Grilled chicken with salad"],
                    "preparation_notes": "Cook with olive oil.",
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Chicken and Vegetable Soup",
                    "description": "Light soup with chicken, carrots, and celery",
                    "portion_guidance": "One large bowl of soup with bread",
                    "alternatives": ["Steamed fish", "Boiled chicken with vegetables"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Yogurt with Cucumber",
                    "description": "Low-fat yogurt with grated cucumber and fresh mint",
                    "portion_guidance": "One small bowl",
                    "alternatives": ["Seasonal fruit", "Carrot with yogurt"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 3,
            "title": "Day 3 — Fiber and Greens",
            "summary": "A day focused on vegetables and fiber for digestive health.",
            "hydration_goal": "8 to 10 glasses of water",
            "notes": "Reduce white bread today.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Yogurt with Fruit",
                    "description": "Low-fat yogurt with seasonal fruit, natural honey, and a pinch of cinnamon",
                    "portion_guidance": "One bowl of yogurt, one fruit",
                    "alternatives": ["Cheese with tomato", "Whole-grain bread with cheese"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Thick Noodle Soup (Ash Reshteh)",
                    "description": "Homemade thick noodle soup with lemon juice and fried mint",
                    "portion_guidance": "One medium bowl of soup",
                    "alternatives": ["Herb stew with rice", "Bean and rice (loobia polo)"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Lentil Soup",
                    "description": "Homemade lentil soup with mild spices and fresh herbs",
                    "portion_guidance": "One medium bowl of lentil soup",
                    "alternatives": ["Barley soup", "Bean stew"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Carrot and Celery Sticks",
                    "description": "Raw carrot and celery sticks with a little yogurt or lemon",
                    "portion_guidance": "A handful of raw vegetables",
                    "alternatives": ["Almonds", "Apple"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 4,
            "title": "Day 4 — Healthy Protein",
            "summary": "Focus on lean proteins and balanced carbohydrates.",
            "hydration_goal": "8 glasses of water",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Yogurt with Walnuts and Honey",
                    "description": "Thick yogurt with walnuts and natural honey",
                    "portion_guidance": "One bowl of yogurt, 5 walnuts, one teaspoon of honey",
                    "alternatives": ["Cheese and herbs", "Whole-grain bread with cheese"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Steamed Chicken with Vegetables",
                    "description": "Steamed chicken breast with seasonal vegetables and a controlled rice portion",
                    "portion_guidance": "One chicken breast, half bowl of rice, one plate of vegetables",
                    "alternatives": ["Salmon fillet", "Beet rice (loobia polo)"],
                    "preparation_notes": "Remove skin from chicken before cooking.",
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Cooked Beans with Bread",
                    "description": "Pinto beans cooked with garlic, tomato, and whole-grain bread",
                    "portion_guidance": "One bowl of beans, one slice of bread",
                    "alternatives": ["Lentil soup", "Potato frittata"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Yogurt Drink (Doogh) and Fruit",
                    "description": "One glass of low-salt doogh with one seasonal fruit",
                    "portion_guidance": "250 ml doogh, one fruit",
                    "alternatives": ["Plain yogurt", "Mixed nuts"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 5,
            "title": "Day 5 — Variety and Flavor",
            "summary": "Food variety to keep motivation high.",
            "hydration_goal": "8 glasses of water",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Honey and Walnut Yogurt Bowl",
                    "description": "Low-fat yogurt with natural honey, walnuts, and seasonal fruit",
                    "portion_guidance": "One bowl of yogurt, one teaspoon of honey, 5 walnuts",
                    "alternatives": ["Cheese with bread", "Whole-grain bread with olive oil"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Steamed Fish with Vegetables",
                    "description": "Steamed fish fillet with lemon, dill, and seasonal vegetables",
                    "portion_guidance": "150 g fish, one plate of vegetables",
                    "alternatives": ["Grilled chicken", "Light lamb kabob"],
                    "preparation_notes": "Minimize added salt.",
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Barley Soup",
                    "description": "Light barley soup with mixed vegetables and a squeeze of lemon",
                    "portion_guidance": "One bowl of soup",
                    "alternatives": ["Lentil soup", "Lentils (adasi)"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Seasonal Fruit",
                    "description": "One fresh seasonal fruit such as apple, pear, or peach",
                    "portion_guidance": "One medium fruit",
                    "alternatives": ["Almonds", "Yogurt"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 6,
            "title": "Day 6 — Light and Restful",
            "summary": "Lighter meals to give your body a rest.",
            "hydration_goal": "8 glasses of water",
            "notes": "Take a gentle walk if possible.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Tea with Bread and Cheese",
                    "description": "Light tea, whole-grain bread with low-salt butter or cheese",
                    "portion_guidance": "One cup of tea, one slice of bread",
                    "alternatives": ["Yogurt with honey", "Fruit with nuts"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Herb Rice with Fish (Sabzi Polo Mahi)",
                    "description": "Rice with fresh herbs (dill, parsley) and a small piece of white fish",
                    "portion_guidance": "Half bowl of rice, 100 g fish",
                    "alternatives": ["Herb frittata (kuku sabzi)", "Chicken with vegetables"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Vegetable Soup",
                    "description": "Light mixed vegetable soup without cream",
                    "portion_guidance": "One large bowl of soup",
                    "alternatives": ["Lentils (adasi)", "Yogurt with cucumber and bread"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Raisins and Almonds",
                    "description": "Mixed raisins and unsalted almonds",
                    "portion_guidance": "A small handful (25 g)",
                    "alternatives": ["Seasonal fruit", "Yogurt"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 7,
            "title": "Day 7 — Week Wrap-Up",
            "summary": "Last day of the week — try a favorite healthy dish.",
            "hydration_goal": "8 to 10 glasses of water",
            "notes": "You can generate next week's plan when ready.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "Breakfast: Yogurt with Fruit and Walnuts",
                    "description": "Low-fat yogurt with seasonal fruit and walnuts",
                    "portion_guidance": "One bowl of yogurt, one fruit, 5 walnuts",
                    "alternatives": ["Cheese with walnuts", "Whole-grain bread with cheese"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "Lunch: Lentil and Rice Dish",
                    "description": "Cooked lentils with fried onion, potato, and controlled rice portion",
                    "portion_guidance": "One bowl of lentils, half bowl of rice",
                    "alternatives": ["Ghormeh sabzi (herb stew)", "Grilled chicken kabob"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "Dinner: Eggplant with Kashk (Kashk-e Bademjan)",
                    "description": "Roasted eggplant with kashk (whey) on whole-grain bread with salad",
                    "portion_guidance": "One small plate, one slice of bread",
                    "alternatives": ["Yogurt with cucumber", "Soup"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "Snack: Tea with Nuts",
                    "description": "Light tea with 5 almonds or walnuts",
                    "portion_guidance": "One cup of tea, 20 g nuts",
                    "alternatives": ["Seasonal fruit", "Doogh"],
                    "preparation_notes": None,
                },
            ],
        },
    ]
    return {"locale": "en", "days": days}


def _make_week_ar() -> dict:
    days = [
        {
            "day_index": 1,
            "title": "اليوم الأول — بداية هادئة",
            "summary": "يوم أول هادئ بوجبات بسيطة ومغذية.",
            "hydration_goal": "8 أكواب ماء على الأقل طوال اليوم",
            "notes": "تجنب الأطعمة المقلية اليوم.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: خبز حبوب كاملة مع جبن وجوز",
                    "description": "خبز حبوب كاملة مع جبن قليل الدسم وجوز وشاي خفيف",
                    "portion_guidance": "شريحتا خبز، ٣٠ جرام جبن، ٥ حبات جوز",
                    "alternatives": ["زبادي مع فاكهة", "شوفان"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: يخنة الأعشاب مع الأرز (قورمة سبزي)",
                    "description": "يخنة أعشاب منزلية مع كمية معتدلة من الأرز وسلطة شيرازي",
                    "portion_guidance": "وعاء صغير من الأرز ووعاء من اليخنة",
                    "alternatives": ["شوربة عدس مع خبز", "عجة الأعشاب (كوكو سبزي)"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: شوربة عدس مع زبادي",
                    "description": "شوربة عدس خفيفة مع بهارات معتدلة وزبادي قليل الدسم وأعشاب طازجة",
                    "portion_guidance": "وعاء متوسط من الشوربة ووعاء صغير من الزبادي",
                    "alternatives": ["شوربة خضار", "شمندر مع خبز"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: فاكهة ومكسرات",
                    "description": "فاكهة موسمية مع حفنة من الجوز أو اللوز",
                    "portion_guidance": "فاكهة واحدة، ٢٠-٣٠ جرام مكسرات",
                    "alternatives": ["زبادي قليل الدسم", "جزر نيء"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 2,
            "title": "اليوم الثاني — طاقة متوازنة",
            "summary": "التركيز على البروتين والخضار الطازجة.",
            "hydration_goal": "٨ أكواب ماء أو مشروب اللبن قليل الملح (دوغ)",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: خبز حبوب كاملة مع جبن وجوز",
                    "description": "خبز حبوب كاملة مع جبن قليل الدسم وجوز وشاي خفيف",
                    "portion_guidance": "شريحتا خبز، ٣٠ جرام جبن، ٥ حبات جوز",
                    "alternatives": ["زبادي مع عسل", "جبن مع خبز"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: عجة الأعشاب (كوكو سبزي) مع سلطة",
                    "description": "عجة أعشاب منزلية مع سلطة فصلية وخبز",
                    "portion_guidance": "قطعتان من العجة وطبق سلطة",
                    "alternatives": ["شوربة مكرونة سميكة (آش رشته)", "دجاج مشوي مع سلطة"],
                    "preparation_notes": "اطهي بزيت الزيتون.",
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: شوربة دجاج وخضار",
                    "description": "شوربة خفيفة بالدجاج والجزر والكرفس",
                    "portion_guidance": "وعاء كبير من الشوربة مع خبز",
                    "alternatives": ["سمك مطهو على البخار", "دجاج مسلوق مع خضار"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: زبادي مع خيار",
                    "description": "زبادي قليل الدسم مع خيار مبشور ونعناع طازج",
                    "portion_guidance": "وعاء صغير",
                    "alternatives": ["فاكهة موسمية", "جزر مع زبادي"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 3,
            "title": "اليوم الثالث — الألياف والخضروات",
            "summary": "يوم يركز على الخضار والألياف لصحة الجهاز الهضمي.",
            "hydration_goal": "٨ إلى ١٠ أكواب ماء",
            "notes": "قلل من الخبز الأبيض اليوم.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: زبادي مع فاكهة",
                    "description": "زبادي قليل الدسم مع فاكهة موسمية وعسل طبيعي وقرفة",
                    "portion_guidance": "وعاء زبادي، فاكهة واحدة",
                    "alternatives": ["جبن مع طماطم", "خبز حبوب كاملة مع جبن"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: شوربة مكرونة سميكة بالأعشاب (آش رشته)",
                    "description": "شوربة أعشاب منزلية سميكة مع عصير الليمون والنعناع المقلي",
                    "portion_guidance": "وعاء متوسط",
                    "alternatives": ["يخنة أعشاب مع أرز", "أرز بالفاصوليا"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: شوربة عدس",
                    "description": "شوربة عدس خفيفة مع بهارات معتدلة وأعشاب طازجة",
                    "portion_guidance": "وعاء متوسط من شوربة العدس",
                    "alternatives": ["شوربة شعير", "فاصوليا مطبوخة"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: جزر وكرفس",
                    "description": "جزر وكرفس نيء مع قليل من الزبادي أو الليمون",
                    "portion_guidance": "حفنة من الخضار النيئة",
                    "alternatives": ["لوز", "تفاح"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 4,
            "title": "اليوم الرابع — بروتين صحي",
            "summary": "التركيز على البروتينات الخالية من الدهون والكربوهيدرات المتوازنة.",
            "hydration_goal": "٨ أكواب ماء",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: زبادي مع جوز وعسل",
                    "description": "زبادي مثخن مع جوز وعسل طبيعي",
                    "portion_guidance": "وعاء زبادي، ٥ حبات جوز، ملعقة عسل",
                    "alternatives": ["جبن وأعشاب", "خبز حبوب كاملة مع جبن"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: دجاج مطهو على البخار مع خضار",
                    "description": "صدر دجاج مطهو على البخار مع خضار موسمية وكمية معتدلة من الأرز",
                    "portion_guidance": "صدر دجاج واحد، نصف وعاء أرز، طبق خضار",
                    "alternatives": ["فيليه سلمون", "أرز بالشمندر"],
                    "preparation_notes": "أزل جلد الدجاج قبل الطهي.",
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: فاصوليا مطبوخة مع خبز",
                    "description": "فاصوليا محبوبة مطبوخة بالثوم والطماطم وخبز حبوب كاملة",
                    "portion_guidance": "وعاء فاصوليا وشريحة خبز",
                    "alternatives": ["شوربة عدس", "عجة بطاطس"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: مشروب اللبن (دوغ) مع فاكهة",
                    "description": "كوب من الدوغ قليل الملح مع فاكهة موسمية",
                    "portion_guidance": "٢٥٠ مل دوغ وفاكهة واحدة",
                    "alternatives": ["زبادي", "مكسرات مشكلة"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 5,
            "title": "اليوم الخامس — تنوع ونكهات",
            "summary": "تنوع الأطعمة للحفاظ على الحماس.",
            "hydration_goal": "٨ أكواب ماء",
            "notes": None,
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: وعاء زبادي بالعسل والجوز",
                    "description": "زبادي قليل الدسم مع عسل طبيعي وجوز وفاكهة موسمية",
                    "portion_guidance": "وعاء زبادي، ملعقة عسل، ٥ حبات جوز",
                    "alternatives": ["جبن مع خبز", "خبز حبوب كاملة مع زيت الزيتون"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: سمك مطهو على البخار مع خضار",
                    "description": "فيليه سمك مطهو على البخار مع ليمون وشبت وخضار موسمية",
                    "portion_guidance": "١٥٠ جرام سمك وطبق خضار",
                    "alternatives": ["دجاج مشوي", "كباب خفيف"],
                    "preparation_notes": "استخدم الملح بشكل معتدل.",
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: شوربة شعير",
                    "description": "شوربة شعير خفيفة مع خضار مشكلة وعصير ليمون",
                    "portion_guidance": "وعاء شوربة",
                    "alternatives": ["شوربة عدس", "عدس مطبوخ (عدسي)"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: فاكهة موسمية",
                    "description": "فاكهة موسمية طازجة كالتفاح أو الكمثرى أو الخوخ",
                    "portion_guidance": "فاكهة متوسطة الحجم",
                    "alternatives": ["لوز", "زبادي"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 6,
            "title": "اليوم السادس — خفيف ومريح",
            "summary": "وجبات أخف لإراحة الجسم.",
            "hydration_goal": "٨ أكواب ماء",
            "notes": "تمشَّ قليلاً إن أمكن.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: شاي مع خبز وجبن",
                    "description": "شاي خفيف وخبز حبوب كاملة مع زبدة قليلة الملح أو جبن",
                    "portion_guidance": "كوب شاي وشريحة خبز",
                    "alternatives": ["زبادي مع عسل", "فاكهة مع مكسرات"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: أرز الأعشاب مع السمك (سبزي بولو ماهي)",
                    "description": "أرز مع أعشاب طازجة (شبت وبقدونس) وقطعة صغيرة من السمك الأبيض",
                    "portion_guidance": "نصف وعاء أرز و١٠٠ جرام سمك",
                    "alternatives": ["عجة الأعشاب (كوكو سبزي)", "دجاج مع خضار"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: شوربة خضار",
                    "description": "شوربة خضار مشكلة خفيفة بدون كريمة",
                    "portion_guidance": "وعاء كبير من الشوربة",
                    "alternatives": ["عدس مطبوخ (عدسي)", "زبادي مع خيار وخبز"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: زبيب ولوز",
                    "description": "مزيج من الزبيب واللوز غير المملح",
                    "portion_guidance": "حفنة صغيرة (٢٥ جرام)",
                    "alternatives": ["فاكهة موسمية", "زبادي"],
                    "preparation_notes": None,
                },
            ],
        },
        {
            "day_index": 7,
            "title": "اليوم السابع — ختام الأسبوع",
            "summary": "آخر يوم في الأسبوع — جرب طبقك الصحي المفضل.",
            "hydration_goal": "٨ إلى ١٠ أكواب ماء",
            "notes": "يمكنك إنشاء خطة الأسبوع القادم عند الاستعداد.",
            "warnings": [],
            "meals": [
                {
                    "meal_type": "breakfast",
                    "title": "الفطور: زبادي مع فاكهة وجوز",
                    "description": "زبادي قليل الدسم مع فاكهة موسمية وجوز",
                    "portion_guidance": "وعاء زبادي، فاكهة واحدة، ٥ حبات جوز",
                    "alternatives": ["جبن مع جوز", "خبز حبوب كاملة مع جبن"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "lunch",
                    "title": "الغداء: طبق عدس وأرز",
                    "description": "عدس مطبوخ مع بصل مقلي وبطاطس وكمية معتدلة من الأرز",
                    "portion_guidance": "وعاء عدس ونصف وعاء أرز",
                    "alternatives": ["يخنة أعشاب (قورمة سبزي)", "كباب دجاج مشوي"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "dinner",
                    "title": "العشاء: باذنجان بالكشك (كشك بادمجان)",
                    "description": "باذنجان مشوي مع الكشك (مصل اللبن) على خبز حبوب كاملة وسلطة",
                    "portion_guidance": "طبق صغير وشريحة خبز",
                    "alternatives": ["زبادي مع خيار", "شوربة"],
                    "preparation_notes": None,
                },
                {
                    "meal_type": "snack",
                    "title": "وجبة خفيفة: شاي مع مكسرات",
                    "description": "شاي خفيف مع ٥ حبات لوز أو جوز",
                    "portion_guidance": "كوب شاي و٢٠ جرام مكسرات",
                    "alternatives": ["فاكهة موسمية", "دوغ"],
                    "preparation_notes": None,
                },
            ],
        },
    ]
    return {"locale": "ar", "days": days}


_MOCK_WEEK_FA = _make_week_fa()
_MOCK_WEEK_EN = _make_week_en()
_MOCK_WEEK_AR = _make_week_ar()

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
    "likely_meal": "وعده ترکیبی خانگی",
    "uncertainties": ["مقدار دقیق مواد غذایی و روش پخت مشخص نیست."],
    "protein": "میزان پروتئین در این وعده مناسب است و به حس سیری طولانی‌تر کمک می‌کند.",
    "fiber": "افزودن سبزیجات تازه یا پخته می‌تواند مقدار فیبر را بهتر کند.",
    "sugar": "میزان قند در حد قابل قبول است. از نوشیدنی‌های شیرین در کنار این وعده اجتناب کنید.",
    "balance": "تعادل درشت‌مغذی‌ها خوب است. ترکیب کربوهیدرات، پروتئین و چربی مناسب است.",
    "portion": "حجم وعده مناسب به نظر می‌رسد. به احساس سیری خود توجه کنید.",
    "protein_quality": "مناسب",
    "fiber_vegetable_quality": "قابل بهبود با سبزیجات بیشتر",
    "carbohydrate_quality": "متوسط؛ اگر ممکن است از نان یا غله سبوس‌دار استفاده شود.",
    "fat_quality": "متعادل",
    "simple_sugar_quality": "پایین تا متوسط",
    "portion_volume_assessment": "حجم وعده متوسط است.",
    "satiety_assessment": "سیری نسبتاً خوبی ایجاد می‌کند.",
    "likely_goal_effect": "با هدف تغذیه متعادل همخوانی دارد.",
    "one_small_correction": "یک مشت سبزی یا سالاد اضافه کنید.",
    "next_meal_suggestion": "وعده بعدی را ساده، پروتئینی و همراه سبزی انتخاب کنید.",
    "no_extreme_compensation_note": "برای جبران، حذف وعده، روزه سخت، دیتاکس یا ورزش افراطی توصیه نمی‌شود.",
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
            "option_type": "best_goal_aligned",
            "household_portions": "یک کف دست نان، ۳۰ گرم پنیر، یک بشقاب کوچک سبزی خوردن",
            "why_it_fits_goal": "پروتئین و کربوهیدرات متعادل دارد و سریع آماده می‌شود.",
            "safety_note": None,
            "substitutions": ["ماست چکیده با نان", "تخم‌مرغ آب‌پز با خیار"],
        },
        {
            "name": "پنیر و گردو با نان",
            "description": "منبع پروتئین و چربی سالم. آماده‌سازی ساده و سریع است.",
            "calories_estimate": 250,
            "prep_time_minutes": 3,
            "tags": ["پروتئین‌دار", "ساده", "مقوی"],
            "option_type": "fastest",
            "household_portions": "یک برش نان، ۳۰ گرم پنیر، چند عدد گردو",
            "why_it_fits_goal": "برای گرسنگی بالا سریع و سیرکننده است.",
            "safety_note": None,
            "substitutions": ["ماست چکیده با نان", "عدسی آماده"],
        },
        {
            "name": "میوه فصلی با ماست",
            "description": "سبک و مغذی. پروبیوتیک ماست برای سلامت گوارش مفید است.",
            "calories_estimate": 180,
            "prep_time_minutes": 3,
            "tags": ["سبک", "سریع", "طبیعی"],
            "option_type": "flexible",
            "household_portions": "یک کاسه کوچک ماست و یک عدد میوه متوسط",
            "why_it_fits_goal": "گزینه سبک و قابل انعطاف برای میان‌وعده است.",
            "safety_note": None,
            "substitutions": ["دوغ کم‌نمک", "میوه با چند عدد بادام"],
        },
    ],
    "best_goal_aligned_option": {
        "name": "نان و پنیر با سبزی خوردن",
        "description": "گزینه متعادل و سریع با پروتئین و سبزی.",
        "option_type": "best_goal_aligned",
        "household_portions": "یک کف دست نان، ۳۰ گرم پنیر، سبزی خوردن",
        "why_it_fits_goal": "سیرکننده و متناسب با غذای ایرانی است.",
        "substitutions": ["ماست چکیده با نان"],
    },
    "fastest_option": {
        "name": "پنیر و گردو با نان",
        "description": "سریع و پروتئین‌دار.",
        "option_type": "fastest",
        "household_portions": "یک برش نان، ۳۰ گرم پنیر، چند عدد گردو",
        "why_it_fits_goal": "با زمان کم آماده می‌شود.",
        "substitutions": ["ماست چکیده با نان"],
    },
    "flexible_option": {
        "name": "میوه فصلی با ماست",
        "description": "سبک و قابل جایگزینی.",
        "option_type": "flexible",
        "household_portions": "یک کاسه کوچک ماست و یک میوه",
        "why_it_fits_goal": "برای میان‌وعده سبک مناسب است.",
        "substitutions": ["دوغ کم‌نمک"],
    },
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

_MOCK_CRAVING_SUPPORT = {
    "calming_message": "این هوس خوردن اطلاعات مفیدی درباره بدن و شرایط امروزت می‌دهد، نه نشانه ضعف.",
    "likely_triggers": ["فاصله زیاد بین وعده‌ها", "استرس یا خستگی", "خواب ناکافی", "محدودیت زیاد در روزهای قبل"],
    "hunger_vs_craving_assessment": "اگر گرسنگی بدنی هم بالاست، یک میان‌وعده متعادل بهتر از مقاومت شدید است.",
    "immediate_options": [
        {
            "title": "گزینه متعادل",
            "description": "ماست چکیده با کمی دارچین و چند عدد گردو",
            "household_portions": "یک کاسه کوچک ماست + دو عدد گردو",
            "why_it_helps": "پروتئین و چربی مفید دارد و هوس شیرینی را ملایم‌تر می‌کند.",
            "substitutions": ["پنیر و نان سبوس‌دار", "میوه با چند عدد بادام"],
        },
        {
            "title": "گزینه انعطاف‌پذیر",
            "description": "اگر شیرینی می‌خواهی، مقدار کوچک را کنار چای و بعد از یک میان‌وعده پروتئینی بخور.",
            "household_portions": "یک تکه کوچک شیرینی",
            "why_it_helps": "حذف کامل شیرینی لازم نیست؛ مقدار و زمینه مهم است.",
            "substitutions": ["خرما با گردو", "میوه شیرین"],
        },
    ],
    "better_choice": {
        "title": "ماست و گردو",
        "description": "گزینه سیرکننده‌تر برای وقتی هوس با گرسنگی همراه است.",
        "household_portions": "یک کاسه کوچک + دو عدد گردو",
        "why_it_helps": "به سیری کمک می‌کند و از ریزه‌خواری پشت سر هم کم می‌کند.",
    },
    "flexible_choice": {
        "title": "شیرینی کنترل‌شده",
        "description": "برنج، نان و شیرینی ممنوع نیستند؛ مقدار، تعادل و زمینه مهم است.",
        "household_portions": "یک تکه کوچک",
        "why_it_helps": "انعطاف باعث کاهش حس محرومیت می‌شود.",
    },
    "prevention_tip": "برای زمان‌های هوس شبانه، یک میان‌وعده پروتئینی ساده از قبل آماده کن.",
    "follow_up_question": "این هوس بیشتر بعد از استرس، کم‌خوابی یا فاصله زیاد از وعده قبلی می‌آید؟",
    "safety_notes": [],
    "requires_human_review": False,
}

_MOCK_SLIP_RECOVERY = {
    "calming_message": "آرام باش؛ یک وعده یا یک روز مسیر کلی تو را خراب نمی‌کند.",
    "data_not_failure_message": "این اتفاق داده مفید است، نه شکست.",
    "likely_trigger_questions": [
        "قبل از آن خیلی گرسنه بودی؟",
        "امروز محدودیت شدید یا حذف وعده داشتی؟",
        "استرس، کم‌خوابی یا احساس گناه قبل از خوردن وجود داشت؟",
    ],
    "pattern_hypothesis": "احتمالاً ترکیبی از گرسنگی زیاد، استرس یا محدودیت قبلی باعث شدت خوردن شده است.",
    "one_small_adjustment": "در وعده بعدی یک منبع پروتئین، سبزی/فیبر و مقدار متعادل کربوهیدرات داشته باش.",
    "next_meal_plan": "وعده بعدی را حذف نکن؛ یک بشقاب متعادل مثل مرغ یا تخم‌مرغ با سالاد و کمی نان یا برنج انتخاب کن.",
    "tomorrow_reset_note": "فردا به برنامه معمول برگرد؛ نیازی به جریمه یا سخت‌گیری نیست.",
    "no_extreme_compensation_note": "روزه سخت، حذف وعده، دیتاکس، پاکسازی، استفراغ عمدی یا ورزش افراطی توصیه نمی‌شود.",
    "safety_notes": [],
    "requires_human_review": False,
}

_MOCK_CONTEXT_GUIDANCE = {
    "best_available_choice": "در رستوران، گزینه‌ای با پروتئین مثل جوجه‌کباب یا خوراک مرغ، سالاد و مقدار کنترل‌شده نان یا برنج انتخاب کن.",
    "flexible_choice": "اگر غذای پرکالری‌تر انتخاب کردی، سهم را کوچک‌تر کن و کنار آن سالاد یا ماست ساده بگذار.",
    "portion_strategy": "نصف بشقاب سبزی/سالاد، یک کف دست پروتئین، و یک مشت کربوهیدرات مثل برنج یا نان.",
    "plate_balance_tip": "برنج یا نان ممنوع نیست؛ با پروتئین و سبزی متعادلش کن.",
    "drink_tip": "نوشیدنی بدون قند یا دوغ کم‌نمک بهتر از نوشابه است.",
    "dessert_or_snack_strategy": "اگر دسر می‌خوری، مقدار کوچک را آرام بخور و آن را به شکست تبدیل نکن.",
    "if_user_chooses_high_calorie_option": "همان وعده را با آرامش بخور؛ فقط مقدار را مدیریت کن و از جبران افراطی بعدش پرهیز کن.",
    "next_meal_adjustment": "وعده بعدی را سبک‌تر اما کامل نگه دار: پروتئین، سبزی و آب کافی.",
    "safety_notes": [],
    "requires_human_review": False,
}

_MOCK_WEEKLY_REPORT = {
    "summary": "گزارش این هفته روی الگوهای قابل اقدام تمرکز دارد و بدون قضاوت نوشته شده است.",
    "behavior_pattern_summary": "خواب، استرس، ثبت وعده‌ها و هوس‌ها برای تصمیم‌های کوچک هفته بعد استفاده شوند.",
    "three_strengths": [
        "ثبت داده‌ها به شناخت بهتر بدن کمک کرده است.",
        "تمرکز روی وعده‌های متعادل قابل ادامه است.",
        "بررسی هوس‌ها می‌تواند مسیر تغییر را عملی‌تر کند.",
    ],
    "two_small_adjustments": [
        "در یک وعده روزانه یک منبع پروتئین یا فیبر کوچک اضافه شود.",
        "برای زمان‌های پرریسک، یک میان‌وعده ساده و متعادل از قبل آماده باشد.",
    ],
    "next_week_small_goal": "هفته بعد حداقل پنج چک‌این کوتاه ثبت شود.",
    "monitoring_notes": "خواب، استرس، گرسنگی، هوس و علائم هشدار پیگیری شوند.",
    "safety_notes": [],
    "requires_human_review": False,
}

_MOCK_ADAPT_PLAN = {
    "summary": "برنامه با توجه به بازخورد جدید شما به شکل محافظه‌کارانه تنظیم شد.",
    "assessment_summary": "بازخورد اخیر نشان می‌دهد نیاز به وعده‌های سیرکننده‌تر و انعطاف‌پذیرتر وجود دارد.",
    "nutrition_diagnosis": "احتمالاً فاصله زیاد بین وعده‌ها یا کمبود پروتئین/فیبر باعث گرسنگی یا هوس بیشتر شده است.",
    "intervention_summary": "میان‌وعده پروتئینی و شام سبک‌تر اما سیرکننده‌تر اضافه شد.",
    "monitoring_notes": "در ۲۴ ساعت آینده گرسنگی، انرژی و خواب را پایش کنید.",
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
    "revised_meals": [
        {
            "meal_type": "snack",
            "title": "میان‌وعده سیرکننده: ماست و گردو",
            "description": "یک کاسه کوچک ماست کم‌چرب با ۲ عدد گردو و دارچین.",
            "portion_guidance": "یک کاسه کوچک + ۲ عدد گردو",
            "alternatives": ["پنیر و گردو", "میوه با چند بادام"],
            "preparation_notes": "برای کاهش هوس شیرینی، آرام و بدون عجله میل شود.",
        },
        {
            "meal_type": "dinner",
            "title": "شام متعادل: عدسی با سالاد",
            "description": "عدسی گرم با سالاد ساده و کمی نان سبوس‌دار.",
            "portion_guidance": "یک کاسه متوسط عدسی + یک بشقاب سالاد",
            "alternatives": ["سوپ مرغ و سبزیجات", "سوپ جو با نان"],
            "preparation_notes": None,
        },
    ],
    "revised_day": {
        "day_index": 1,
        "title": "روز تنظیم‌شده",
        "summary": "وعده‌های امروز برای سیری بهتر و بدون جبران افراطی تنظیم شد.",
        "hydration_goal": "۶ تا ۸ لیوان آب در طول روز",
        "notes": "هیچ وعده‌ای حذف نشود؛ فقط ترکیب وعده‌ها متعادل‌تر شود.",
        "warnings": [],
        "meals": [
            {
                "meal_type": "snack",
                "title": "میان‌وعده سیرکننده: ماست و گردو",
                "description": "یک کاسه کوچک ماست کم‌چرب با ۲ عدد گردو و دارچین.",
                "portion_guidance": "یک کاسه کوچک + ۲ عدد گردو",
                "alternatives": ["پنیر و گردو", "میوه با چند بادام"],
                "preparation_notes": "برای کاهش هوس شیرینی، آرام و بدون عجله میل شود.",
            },
            {
                "meal_type": "dinner",
                "title": "شام متعادل: عدسی با سالاد",
                "description": "عدسی گرم با سالاد ساده و کمی نان سبوس‌دار.",
                "portion_guidance": "یک کاسه متوسط عدسی + یک بشقاب سالاد",
                "alternatives": ["سوپ مرغ و سبزیجات", "سوپ جو با نان"],
                "preparation_notes": None,
            },
        ],
    },
    "changed_items": ["snack", "dinner"],
    "reason_for_changes": "کاهش گرسنگی و هوس بدون حذف وعده یا جبران افراطی.",
    "safety_notes": ["از روزه‌داری، حذف وعده، یا ورزش افراطی برای جبران پرهیز شود."],
    "requires_human_review": False,
    "follow_up_question": None,
    "warnings": [],
}


def generate_safe_week_mock(ctx: "NutritionMemoryContext", locale: str) -> dict:
    """Return locale mock week data, then apply allergy/dislike sanitization."""
    from app.services.weekly_plan_personalization_validator import validate_and_sanitize
    mock_map = {"fa": _MOCK_WEEK_FA, "en": _MOCK_WEEK_EN, "ar": _MOCK_WEEK_AR}
    base = mock_map.get(locale, _MOCK_WEEK_FA)
    # Deep copy to avoid mutating the module-level constant
    import copy
    base_copy = copy.deepcopy(base)
    return validate_and_sanitize(base_copy, ctx, locale=locale)


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
        elif task_type == "craving_support":
            content = json.dumps(_MOCK_CRAVING_SUPPORT, ensure_ascii=False)
        elif task_type == "slip_recovery":
            content = json.dumps(_MOCK_SLIP_RECOVERY, ensure_ascii=False)
        elif task_type == "context_guidance":
            content = json.dumps(_MOCK_CONTEXT_GUIDANCE, ensure_ascii=False)
        elif task_type == "adapt_plan":
            content = json.dumps(_MOCK_ADAPT_PLAN, ensure_ascii=False)
        elif task_type == "chat_message":
            content = json.dumps(_MOCK_CHAT, ensure_ascii=False)
        elif task_type == "generate_week_en":
            content = json.dumps(_MOCK_WEEK_EN, ensure_ascii=False)
        elif task_type == "generate_week_ar":
            content = json.dumps(_MOCK_WEEK_AR, ensure_ascii=False)
        elif task_type == "generate_week_fa":
            content = json.dumps(_MOCK_WEEK_FA, ensure_ascii=False)
        elif task_type == "weekly_report":
            content = json.dumps(_MOCK_WEEKLY_REPORT, ensure_ascii=False)
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
            if TASK_GENERATE_WEEK_EN in content:
                return "generate_week_en"
            if TASK_GENERATE_WEEK_AR in content:
                return "generate_week_ar"
            if TASK_GENERATE_WEEK_FA in content:
                return "generate_week_fa"
            if TASK_WEEKLY_REPORT in content:
                return "weekly_report"
            if TASK_GENERATE_PLAN in content:
                return "generate_plan"
            if TASK_ANALYZE_MEAL in content:
                return "analyze_meal"
            if TASK_WHAT_TO_EAT in content:
                return "what_to_eat_now"
            if TASK_CRAVING_SUPPORT in content:
                return "craving_support"
            if TASK_SLIP_RECOVERY in content:
                return "slip_recovery"
            if TASK_CONTEXT_GUIDANCE in content:
                return "context_guidance"
            if TASK_ADAPT_PLAN in content:
                return "adapt_plan"
            if TASK_CHAT in content:
                return "chat_message"
        return "generate_plan"
