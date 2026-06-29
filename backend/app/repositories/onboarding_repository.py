"""
Onboarding repository: all DB access for the onboarding flow.

Uses SQLAlchemy 2.x select() + session.execute() exclusively.
No session.query() — that pattern is deprecated.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.lifestyle import BehaviorProfile, FoodPreference, LifestyleProfile
from app.models.nutrition import NutritionGoal, NutritionRiskAssessment
from app.models.profile import Allergy, Medication, UserMedicalFlag, UserProfile
from app.models.user import User
from app.services.safety_guardrail_service import SafetyAssessment

# Sentinel condition code used to store free-text warning symptoms
WARNING_SYMPTOMS_CODE = "warning_symptoms"


# ─── UserProfile ──────────────────────────────────────────────────────────────

def get_profile(db: Session, user_id: str) -> UserProfile | None:
    result = db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


def upsert_profile(
    db: Session,
    user_id: str,
    *,
    full_name: str,
    gender: str,
    birth_date: date | None,
    height_cm: float,
    weight_kg: float,
    target_weight_kg: float | None,
    waist_cm: float | None,
    wrist_cm: float | None = None,
    thigh_cm: float | None = None,
) -> UserProfile:
    profile = get_profile(db, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    profile.full_name = full_name
    profile.gender = gender
    profile.birth_date = birth_date
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.target_weight_kg = target_weight_kg
    profile.waist_cm = waist_cm
    profile.wrist_cm = wrist_cm
    profile.thigh_cm = thigh_cm

    db.flush()
    return profile


# ─── UserMedicalFlag ──────────────────────────────────────────────────────────

def get_medical_flags(db: Session, user_id: str) -> list[UserMedicalFlag]:
    result = db.execute(
        select(UserMedicalFlag).where(UserMedicalFlag.user_id == user_id)
    )
    return list(result.scalars().all())


def replace_medical_flags(
    db: Session,
    user_id: str,
    flags: dict[str, bool],
) -> list[UserMedicalFlag]:
    """Upsert one UserMedicalFlag row per condition code."""
    existing: dict[str, UserMedicalFlag] = {
        f.condition_code: f for f in get_medical_flags(db, user_id)
    }
    rows: list[UserMedicalFlag] = []
    for code, has_condition in flags.items():
        if code in existing:
            existing[code].has_condition = has_condition
            rows.append(existing[code])
        else:
            flag = UserMedicalFlag(
                user_id=user_id,
                condition_code=code,
                has_condition=has_condition,
            )
            db.add(flag)
            rows.append(flag)
    db.flush()
    return rows


def upsert_warning_symptoms(
    db: Session,
    user_id: str,
    symptoms: list[str],
) -> None:
    """Store warning symptoms list in a sentinel UserMedicalFlag row."""
    result = db.execute(
        select(UserMedicalFlag).where(
            UserMedicalFlag.user_id == user_id,
            UserMedicalFlag.condition_code == WARNING_SYMPTOMS_CODE,
        )
    )
    flag = result.scalar_one_or_none()
    if flag is None:
        flag = UserMedicalFlag(
            user_id=user_id,
            condition_code=WARNING_SYMPTOMS_CODE,
            has_condition=len(symptoms) > 0,
            notes=json.dumps(symptoms, ensure_ascii=False),
        )
        db.add(flag)
    else:
        flag.has_condition = len(symptoms) > 0
        flag.notes = json.dumps(symptoms, ensure_ascii=False)
    db.flush()


def get_warning_symptoms(db: Session, user_id: str) -> list[str]:
    result = db.execute(
        select(UserMedicalFlag).where(
            UserMedicalFlag.user_id == user_id,
            UserMedicalFlag.condition_code == WARNING_SYMPTOMS_CODE,
        )
    )
    flag = result.scalar_one_or_none()
    if flag is None or not flag.notes:
        return []
    try:
        return json.loads(flag.notes)
    except (json.JSONDecodeError, TypeError):
        return []


def medical_data_exists(db: Session, user_id: str) -> bool:
    """True if any medical flag row exists for this user."""
    result = db.execute(
        select(UserMedicalFlag.id).where(UserMedicalFlag.user_id == user_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


# ─── Medication ───────────────────────────────────────────────────────────────

def get_medications(db: Session, user_id: str) -> list[Medication]:
    result = db.execute(select(Medication).where(Medication.user_id == user_id))
    return list(result.scalars().all())


def replace_medications(db: Session, user_id: str, names: list[str]) -> list[Medication]:
    """Delete all current medications and insert the new list."""
    db.execute(delete(Medication).where(Medication.user_id == user_id))
    rows: list[Medication] = []
    for name in names:
        name = name.strip()
        if name:
            med = Medication(user_id=user_id, name=name)
            db.add(med)
            rows.append(med)
    db.flush()
    return rows


# ─── Allergy ──────────────────────────────────────────────────────────────────

def get_allergies(db: Session, user_id: str) -> list[Allergy]:
    result = db.execute(select(Allergy).where(Allergy.user_id == user_id))
    return list(result.scalars().all())


def replace_allergies(db: Session, user_id: str, allergens: list[str]) -> list[Allergy]:
    """Delete all current allergies and insert the new list."""
    db.execute(delete(Allergy).where(Allergy.user_id == user_id))
    rows: list[Allergy] = []
    for allergen in allergens:
        allergen = allergen.strip()
        if allergen:
            allergy = Allergy(user_id=user_id, allergen=allergen)
            db.add(allergy)
            rows.append(allergy)
    db.flush()
    return rows


# ─── LifestyleProfile ─────────────────────────────────────────────────────────

def get_lifestyle(db: Session, user_id: str) -> LifestyleProfile | None:
    result = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


def upsert_lifestyle(
    db: Session,
    user_id: str,
    *,
    sleep_hours: float,
    stress_level: int,
    work_schedule: str,
    activity_level: str,
    exercise_days_per_week: int,
    cooking_ability: int,
    food_budget: str,
    eating_out_frequency: str,
    travel_frequency: str,
) -> LifestyleProfile:
    lp = get_lifestyle(db, user_id)
    if lp is None:
        lp = LifestyleProfile(user_id=user_id)
        db.add(lp)

    lp.sleep_hours = sleep_hours
    lp.stress_level = stress_level
    lp.work_schedule = work_schedule
    lp.activity_level = activity_level
    lp.exercise_days_per_week = exercise_days_per_week
    lp.cooking_ability = cooking_ability
    lp.food_budget = food_budget
    lp.eating_out_frequency = eating_out_frequency
    lp.travel_frequency = travel_frequency

    db.flush()
    return lp


# ─── FoodPreference ───────────────────────────────────────────────────────────

def get_food_preference(db: Session, user_id: str) -> FoodPreference | None:
    result = db.execute(
        select(FoodPreference).where(FoodPreference.user_id == user_id)
    )
    return result.scalar_one_or_none()


def upsert_food_preference(
    db: Session,
    user_id: str,
    *,
    likes_iranian_food: bool,
    vegetarian: bool,
    vegan: bool,
    halal: bool,
    disliked_foods: list[str],
    favorite_foods: list[str],
    breakfast_habit: str,
    rice_frequency: str,
    bread_frequency: str,
    sweets_frequency: str,
    tea_frequency: str,
    restaurant_frequency: str,
) -> FoodPreference:
    fp = get_food_preference(db, user_id)
    if fp is None:
        fp = FoodPreference(user_id=user_id)
        db.add(fp)

    fp.likes_iranian_food = likes_iranian_food
    fp.vegetarian = vegetarian
    fp.vegan = vegan
    fp.halal = halal
    fp.disliked_foods = json.dumps(disliked_foods, ensure_ascii=False)
    fp.favorite_foods = json.dumps(favorite_foods, ensure_ascii=False)
    fp.breakfast_habit = breakfast_habit or None
    fp.rice_frequency = rice_frequency or None
    fp.bread_frequency = bread_frequency or None
    fp.sweets_frequency = sweets_frequency or None
    fp.tea_frequency = tea_frequency or None
    fp.restaurant_frequency = restaurant_frequency or None

    db.flush()
    return fp


# ─── BehaviorProfile ──────────────────────────────────────────────────────────

def get_behavior_profile(db: Session, user_id: str) -> BehaviorProfile | None:
    result = db.execute(
        select(BehaviorProfile).where(BehaviorProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


def upsert_behavior_profile(
    db: Session,
    user_id: str,
    *,
    emotional_eating: bool,
    night_eating: bool,
    meal_skipping: bool,
    cravings: list[str],
    binge_history: bool,
    diet_history: str,
    previous_failures: str,
    hunger_patterns: list[str],
    motivation_level: int,
) -> BehaviorProfile:
    bp = get_behavior_profile(db, user_id)
    if bp is None:
        bp = BehaviorProfile(user_id=user_id)
        db.add(bp)

    bp.emotional_eating = emotional_eating
    bp.night_eating = night_eating
    bp.meal_skipping = meal_skipping
    bp.cravings = json.dumps(cravings, ensure_ascii=False)
    bp.binge_history = binge_history
    bp.diet_history = diet_history or None
    bp.previous_failures = previous_failures or None
    bp.hunger_patterns = json.dumps(hunger_patterns, ensure_ascii=False) if hunger_patterns else None
    bp.hunger_pattern = hunger_patterns[0] if hunger_patterns else None
    bp.motivation_level = motivation_level

    db.flush()
    return bp


# ─── NutritionGoal (onboarding) ───────────────────────────────────────────────

def get_nutrition_goal(db: Session, user_id: str) -> NutritionGoal | None:
    result = db.execute(select(NutritionGoal).where(NutritionGoal.user_id == user_id))
    return result.scalar_one_or_none()


def upsert_onboarding_goals(
    db: Session,
    user_id: str,
    goal_types: list[str],
) -> NutritionGoal:
    goal = get_nutrition_goal(db, user_id)
    if goal is None:
        goal = NutritionGoal(user_id=user_id)
        db.add(goal)
    goal.goal_type = goal_types[0]
    goal.goal_types_json = json.dumps(goal_types, ensure_ascii=False)
    db.flush()
    return goal


# ─── NutritionRiskAssessment ──────────────────────────────────────────────────

def create_risk_assessment(
    db: Session,
    user_id: str,
    assessment: SafetyAssessment,
) -> NutritionRiskAssessment:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = NutritionRiskAssessment(
        user_id=user_id,
        risk_level=assessment.risk_level,
        flags_triggered=json.dumps(assessment.flags_triggered, ensure_ascii=False),
        assessed_at=now,
    )
    db.add(row)
    db.flush()
    return row


def get_latest_risk_assessment(
    db: Session, user_id: str
) -> NutritionRiskAssessment | None:
    result = db.execute(
        select(NutritionRiskAssessment)
        .where(NutritionRiskAssessment.user_id == user_id)
        .order_by(NutritionRiskAssessment.assessed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ─── Food preference merge helpers ───────────────────────────────────────────

def merge_food_dislikes(db: Session, user_id: str, new_dislikes: list[str]) -> None:
    """Merge new_dislikes into FoodPreference.disliked_foods without duplicates.
    Uses normalized comparison so variants (half-space, Arabic chars) are deduplicated.
    Dislikes win: also purges any matching food from favorite_foods."""
    from app.services.preference_extractor import normalize_for_compare

    if not new_dislikes:
        return

    fp = get_food_preference(db, user_id)
    if fp is None:
        fp = FoodPreference(user_id=user_id)
        db.add(fp)

    existing_dislikes: list[str] = []
    if fp.disliked_foods:
        try:
            existing_dislikes = json.loads(fp.disliked_foods)
        except (json.JSONDecodeError, TypeError):
            existing_dislikes = []

    existing_norms = {normalize_for_compare(d) for d in existing_dislikes}
    for food in new_dislikes:
        key = normalize_for_compare(food)
        if key and key not in existing_norms:
            existing_dislikes.append(food)
            existing_norms.add(key)

    fp.disliked_foods = json.dumps(existing_dislikes, ensure_ascii=False)

    # Remove any newly disliked food from favorites (dislikes win)
    existing_likes: list[str] = []
    if fp.favorite_foods:
        try:
            existing_likes = json.loads(fp.favorite_foods)
        except (json.JSONDecodeError, TypeError):
            existing_likes = []
    if existing_likes:
        dislike_norms = {normalize_for_compare(d) for d in existing_dislikes}
        cleaned = [f for f in existing_likes if normalize_for_compare(f) not in dislike_norms]
        if len(cleaned) != len(existing_likes):
            fp.favorite_foods = json.dumps(cleaned, ensure_ascii=False)

    db.flush()


def merge_food_likes(db: Session, user_id: str, new_likes: list[str]) -> None:
    """Merge new_likes into FoodPreference.favorite_foods. Skips foods already disliked."""
    from app.services.preference_extractor import normalize_for_compare

    if not new_likes:
        return

    fp = get_food_preference(db, user_id)
    if fp is None:
        fp = FoodPreference(user_id=user_id)
        db.add(fp)

    existing_dislikes: list[str] = []
    if fp.disliked_foods:
        try:
            existing_dislikes = json.loads(fp.disliked_foods)
        except (json.JSONDecodeError, TypeError):
            existing_dislikes = []
    dislike_norms = {normalize_for_compare(d) for d in existing_dislikes}

    existing_likes: list[str] = []
    if fp.favorite_foods:
        try:
            existing_likes = json.loads(fp.favorite_foods)
        except (json.JSONDecodeError, TypeError):
            existing_likes = []

    existing_norms = {normalize_for_compare(f) for f in existing_likes}
    for food in new_likes:
        key = normalize_for_compare(food)
        if key and key not in existing_norms and key not in dislike_norms:
            existing_likes.append(food)
            existing_norms.add(key)

    fp.favorite_foods = json.dumps(existing_likes, ensure_ascii=False)
    db.flush()


# ─── User ─────────────────────────────────────────────────────────────────────

def set_user_onboarded(db: Session, user: User) -> None:
    user.is_onboarded = True
    db.flush()
