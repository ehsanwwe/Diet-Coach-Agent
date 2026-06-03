"""
ORM model package.

Import concrete models here so Alembic autogenerate can discover them.
Future groups are imported opportunistically because plans 01-04+ add those
files after this model group.
"""
from __future__ import annotations

# Group 1 - User core
from app.models.audit import AuditLog, UserLanguagePreference
from app.models.auth import AuthOTP, TokenBlocklist
from app.models.user import User

# Group 2 - Profile
from app.models.profile import (
    Allergy,
    MedicalCondition,
    Medication,
    UserMedicalFlag,
    UserProfile,
)

try:
    from app.models.lifestyle import (
        BehaviorProfile,
        FoodPreference,
        LifestyleProfile,
    )
except ModuleNotFoundError:
    pass

try:
    from app.models.nutrition import (
        NutritionGoal,
        NutritionPlan,
        NutritionPlanMeal,
        NutritionRiskAssessment,
    )
except ModuleNotFoundError:
    pass

try:
    from app.models.chat import (
        AudioMessage,
        ChatMessage,
        ChatSession,
        MealEntry,
    )
except ModuleNotFoundError:
    pass

try:
    from app.models.progress import (
        DailyCheckIn,
        ProgressEntry,
        WeeklyReport,
    )
except ModuleNotFoundError:
    pass

__all__ = [
    "Allergy",
    "AuditLog",
    "AuthOTP",
    "MedicalCondition",
    "Medication",
    "TokenBlocklist",
    "User",
    "UserLanguagePreference",
    "UserMedicalFlag",
    "UserProfile",
]
