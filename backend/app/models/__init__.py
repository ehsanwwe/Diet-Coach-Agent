"""
ORM model package.

Import concrete models here so Alembic autogenerate can discover them.
"""
from __future__ import annotations

# Group 5 - Chat, audio, and meals
from app.models.chat import AudioMessage, ChatMessage, ChatSession, MealEntry

# Group 1 - User core
from app.models.audit import AuditLog, UserLanguagePreference
from app.models.auth import AuthOTP, TokenBlocklist
from app.models.user import User

# Group 3 - Lifestyle
from app.models.lifestyle import BehaviorProfile, FoodPreference, LifestyleProfile

# Group 4 - Nutrition
from app.models.nutrition import (
    NutritionGoal,
    NutritionPlan,
    NutritionPlanMeal,
    NutritionRiskAssessment,
)

# Group 2 - Profile
from app.models.profile import (
    Allergy,
    MedicalCondition,
    Medication,
    UserMedicalFlag,
    UserProfile,
)

# Group 6 - Progress
from app.models.progress import DailyCheckIn, ProgressEntry, WeeklyReport

__all__ = [
    "Allergy",
    "AuditLog",
    "AudioMessage",
    "AuthOTP",
    "BehaviorProfile",
    "ChatMessage",
    "ChatSession",
    "DailyCheckIn",
    "FoodPreference",
    "LifestyleProfile",
    "MealEntry",
    "MedicalCondition",
    "Medication",
    "NutritionGoal",
    "NutritionPlan",
    "NutritionPlanMeal",
    "NutritionRiskAssessment",
    "ProgressEntry",
    "TokenBlocklist",
    "User",
    "UserLanguagePreference",
    "UserMedicalFlag",
    "UserProfile",
    "WeeklyReport",
]
