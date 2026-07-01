"""
Admin user management endpoints.

GET    /admin/users                             — list all users
GET    /admin/users/{user_id}                   — user detail
GET    /admin/users/{user_id}/export/onboarding — JSON export
GET    /admin/users/{user_id}/export/chat       — JSON export
GET    /admin/users/{user_id}/export/nutrition  — JSON export
GET    /admin/users/{user_id}/export/all        — JSON export
DELETE /admin/users/{user_id}                   — delete user + all data

All endpoints require admin JWT via X-Admin-Token header.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.admin_dependencies import require_admin
from app.core.config import settings
from app.core.database import get_session
from app.core.errors import raise_http_error
from app.models.audit import AuditLog, UserLanguagePreference
from app.models.auth import AuthOTP
from app.models.calendar import NutritionPlanCalendar, NutritionPlanDay, NutritionPlanDayMeal
from app.models.chat import AudioMessage, ChatMessage, ChatSession, MealEntry
from app.models.lifestyle import BehaviorProfile, FoodPreference, LifestyleProfile
from app.models.nutrition import NutritionGoal, NutritionPlan, NutritionPlanMeal, NutritionRiskAssessment
from app.models.profile import Allergy, Medication, UserMedicalFlag, UserProfile
from app.models.progress import DailyCheckIn, ProgressEntry, WeeklyReport
from app.models.user import User
from app.schemas.admin import (
    AdminDeleteResponse,
    AdminExportResponse,
    AdminExportUser,
    AdminUserDetail,
    AdminUserListItem,
)
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["admin-users"])


def _iso(value) -> str | None:
    """Convert date/datetime to ISO string, or None if value is None."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scalar_count(db: Session, stmt) -> int:
    result = db.execute(stmt)
    value = result.scalar()
    return int(value) if value is not None else 0


# ── Helpers: build export data dicts ─────────────────────────────────────────

def _onboarding_data(db: Session, user: User) -> dict:
    profile = db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    ).scalar_one_or_none()

    medical_flags = db.execute(
        select(UserMedicalFlag).where(UserMedicalFlag.user_id == user.id)
    ).scalars().all()

    medications = db.execute(
        select(Medication).where(Medication.user_id == user.id)
    ).scalars().all()

    allergies = db.execute(
        select(Allergy).where(Allergy.user_id == user.id)
    ).scalars().all()

    lifestyle = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user.id)
    ).scalar_one_or_none()

    food_pref = db.execute(
        select(FoodPreference).where(FoodPreference.user_id == user.id)
    ).scalar_one_or_none()

    behavior = db.execute(
        select(BehaviorProfile).where(BehaviorProfile.user_id == user.id)
    ).scalar_one_or_none()

    lang_pref = db.execute(
        select(UserLanguagePreference).where(UserLanguagePreference.user_id == user.id)
    ).scalar_one_or_none()

    return {
        "profile": {
            "full_name": profile.full_name if profile else None,
            "gender": profile.gender if profile else None,
            "birth_date": _iso(profile.birth_date) if profile else None,
            "height_cm": profile.height_cm if profile else None,
            "weight_kg": profile.weight_kg if profile else None,
            "target_weight_kg": profile.target_weight_kg if profile else None,
            "waist_cm": profile.waist_cm if profile else None,
            "wrist_cm": profile.wrist_cm if profile else None,
            "thigh_cm": profile.thigh_cm if profile else None,
        } if profile else None,
        "medical_flags": [
            {
                "condition_code": f.condition_code,
                "has_condition": f.has_condition,
                "notes": f.notes,
            }
            for f in medical_flags
        ],
        "medications": [
            {"name": m.name, "dosage": m.dosage}
            for m in medications
        ],
        "allergies": [
            {"allergen": a.allergen, "severity": a.severity}
            for a in allergies
        ],
        "lifestyle": {
            "sleep_hours": lifestyle.sleep_hours,
            "stress_level": lifestyle.stress_level,
            "work_schedule": lifestyle.work_schedule,
            "activity_level": lifestyle.activity_level,
            "exercise_days_per_week": lifestyle.exercise_days_per_week,
            "cooking_ability": lifestyle.cooking_ability,
            "food_budget": lifestyle.food_budget,
            "eating_out_frequency": lifestyle.eating_out_frequency,
            "travel_frequency": lifestyle.travel_frequency,
        } if lifestyle else None,
        "food_preferences": {
            "likes_iranian_food": food_pref.likes_iranian_food,
            "vegetarian": food_pref.vegetarian,
            "vegan": food_pref.vegan,
            "halal": food_pref.halal,
            "disliked_foods": food_pref.disliked_foods,
            "favorite_foods": food_pref.favorite_foods,
            "breakfast_habit": food_pref.breakfast_habit,
            "rice_frequency": food_pref.rice_frequency,
            "bread_frequency": food_pref.bread_frequency,
            "sweets_frequency": food_pref.sweets_frequency,
            "tea_frequency": food_pref.tea_frequency,
            "restaurant_frequency": food_pref.restaurant_frequency,
        } if food_pref else None,
        "behavior_profile": {
            "emotional_eating": behavior.emotional_eating,
            "night_eating": behavior.night_eating,
            "meal_skipping": behavior.meal_skipping,
            "cravings": behavior.cravings,
            "binge_history": behavior.binge_history,
            "diet_history": behavior.diet_history,
            "previous_failures": behavior.previous_failures,
            "hunger_pattern": behavior.hunger_pattern,
            "motivation_level": behavior.motivation_level,
        } if behavior else None,
        "language_preference": lang_pref.language_code if lang_pref else None,
    }


def _chat_data(db: Session, user: User) -> dict:
    sessions = db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at)
    ).scalars().all()

    result = []
    for session in sessions:
        messages = db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
        ).scalars().all()

        audio_msgs = db.execute(
            select(AudioMessage)
            .where(AudioMessage.session_id == session.id)
            .order_by(AudioMessage.created_at)
        ).scalars().all()

        result.append({
            "session_id": session.id,
            "session_type": session.session_type,
            "message_count": session.message_count,
            "summary": session.summary,
            "created_at": _iso(session.created_at),
            "updated_at": _iso(session.updated_at),
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "status": m.status,
                    "created_at": _iso(m.created_at),
                }
                for m in messages
            ],
            "audio_messages": [
                {
                    "id": a.id,
                    "transcription_status": a.transcription_status,
                    "transcription_text": a.transcription_text,
                    "mime_type": a.mime_type,
                    "duration_seconds": a.duration_seconds,
                    "created_at": _iso(a.created_at),
                }
                for a in audio_msgs
            ],
        })

    meal_entries = db.execute(
        select(MealEntry)
        .where(MealEntry.user_id == user.id)
        .order_by(MealEntry.logged_at)
    ).scalars().all()

    return {
        "chat_sessions": result,
        "meal_entries": [
            {
                "id": e.id,
                "meal_time": e.meal_time,
                "description": e.description,
                "analysis_result": e.analysis_result,
                "logged_at": _iso(e.logged_at),
                "created_at": _iso(e.created_at),
            }
            for e in meal_entries
        ],
    }


def _nutrition_data(db: Session, user: User) -> dict:
    goal = db.execute(
        select(NutritionGoal).where(NutritionGoal.user_id == user.id)
    ).scalar_one_or_none()

    risk_assessments = db.execute(
        select(NutritionRiskAssessment)
        .where(NutritionRiskAssessment.user_id == user.id)
        .order_by(NutritionRiskAssessment.assessed_at.desc())
    ).scalars().all()

    plans = db.execute(
        select(NutritionPlan)
        .where(NutritionPlan.user_id == user.id)
        .order_by(NutritionPlan.created_at.desc())
    ).scalars().all()

    plans_data = []
    for plan in plans:
        meals = db.execute(
            select(NutritionPlanMeal)
            .where(NutritionPlanMeal.plan_id == plan.id)
            .order_by(NutritionPlanMeal.order_index)
        ).scalars().all()
        plans_data.append({
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "status": plan.status,
            "generated_by": plan.generated_by,
            "plan_metadata": plan.plan_metadata,
            "created_at": _iso(plan.created_at),
            "meals": [
                {
                    "meal_time": m.meal_time,
                    "name": m.name,
                    "description": m.description,
                    "calories_estimate": m.calories_estimate,
                    "protein_g": m.protein_g,
                    "carbs_g": m.carbs_g,
                    "fat_g": m.fat_g,
                    "notes": m.notes,
                }
                for m in meals
            ],
        })

    calendars = db.execute(
        select(NutritionPlanCalendar)
        .where(NutritionPlanCalendar.user_id == user.id)
        .order_by(NutritionPlanCalendar.created_at.desc())
    ).scalars().all()

    calendars_data = []
    for cal in calendars:
        days = db.execute(
            select(NutritionPlanDay)
            .where(NutritionPlanDay.calendar_id == cal.id)
            .order_by(NutritionPlanDay.plan_date)
        ).scalars().all()
        days_data = []
        for day in days:
            day_meals = db.execute(
                select(NutritionPlanDayMeal)
                .where(NutritionPlanDayMeal.plan_day_id == day.id)
                .order_by(NutritionPlanDayMeal.meal_order)
            ).scalars().all()
            days_data.append({
                "plan_date": _iso(day.plan_date),
                "locale": day.locale,
                "title": day.title,
                "summary": day.summary,
                "daily_calories": day.daily_calories,
                "daily_macros": day.daily_macros,
                "meals": [
                    {
                        "meal_type": dm.meal_type,
                        "title": dm.title,
                        "description": dm.description,
                        "calories_estimate": dm.calories_estimate,
                        "protein_g": dm.protein_g,
                        "carbs_g": dm.carbs_g,
                        "fat_g": dm.fat_g,
                        "food_items": dm.food_items,
                    }
                    for dm in day_meals
                ],
            })
        calendars_data.append({
            "id": cal.id,
            "locale": cal.locale,
            "status": cal.status,
            "start_date": _iso(cal.start_date),
            "end_date": _iso(cal.end_date),
            "created_at": _iso(cal.created_at),
            "days": days_data,
        })

    daily_checkins = db.execute(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user.id)
        .order_by(DailyCheckIn.check_date.desc())
    ).scalars().all()

    progress_entries = db.execute(
        select(ProgressEntry)
        .where(ProgressEntry.user_id == user.id)
        .order_by(ProgressEntry.recorded_at.desc())
    ).scalars().all()

    weekly_reports = db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user.id)
        .order_by(WeeklyReport.week_start.desc())
    ).scalars().all()

    return {
        "nutrition_goal": {
            "goal_type": goal.goal_type,
            "goal_types_json": goal.goal_types_json,
            "target_calories": goal.target_calories,
            "notes": goal.notes,
            "created_at": _iso(goal.created_at),
        } if goal else None,
        "risk_assessments": [
            {
                "risk_level": r.risk_level,
                "flags_triggered": r.flags_triggered,
                "assessed_at": _iso(r.assessed_at),
            }
            for r in risk_assessments
        ],
        "nutrition_plans": plans_data,
        "calendars": calendars_data,
        "daily_checkins": [
            {
                "check_date": _iso(c.check_date),
                "weight_kg": c.weight_kg,
                "waist_cm": c.waist_cm,
                "hunger_level": c.hunger_level,
                "sleep_hours": c.sleep_hours,
                "energy_level": c.energy_level,
                "stress_level": c.stress_level,
                "activity_minutes": c.activity_minutes,
                "adherence_level": c.adherence_level,
            }
            for c in daily_checkins
        ],
        "progress_entries": [
            {
                "entry_type": p.entry_type,
                "value_numeric": p.value_numeric,
                "value_text": p.value_text,
                "recorded_at": _iso(p.recorded_at),
            }
            for p in progress_entries
        ],
        "weekly_reports": [
            {
                "week_start": _iso(r.week_start),
                "week_end": _iso(r.week_end),
                "report_data": r.report_data,
                "generated_at": _iso(r.generated_at),
            }
            for r in weekly_reports
        ],
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[list[AdminUserListItem]])
def list_users(
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> SuccessResponse[list[AdminUserListItem]]:
    """Return a summary list of all registered users."""
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()

    items: list[AdminUserListItem] = []
    for user in users:
        profile = db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        ).scalar_one_or_none()

        lang_pref = db.execute(
            select(UserLanguagePreference).where(UserLanguagePreference.user_id == user.id)
        ).scalar_one_or_none()

        has_plan = db.execute(
            select(func.count(NutritionPlan.id)).where(NutritionPlan.user_id == user.id)
        ).scalar() or 0

        msg_count = db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.user_id == user.id)
        ).scalar() or 0

        latest_activity = db.execute(
            select(func.max(ChatSession.updated_at))
            .where(ChatSession.user_id == user.id)
        ).scalar()

        items.append(
            AdminUserListItem(
                id=user.id,
                phone=user.phone,
                full_name=profile.full_name if profile else None,
                language=lang_pref.language_code if lang_pref else None,
                is_onboarded=user.is_onboarded,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                has_nutrition_plan=bool(has_plan),
                chat_message_count=int(msg_count),
                latest_activity=latest_activity,
            )
        )
    return SuccessResponse(data=items)


@router.get("/{user_id}", response_model=SuccessResponse[AdminUserDetail])
def get_user(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> SuccessResponse[AdminUserDetail]:
    """Return detailed info for a single user."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)

    profile = db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    ).scalar_one_or_none()

    lang_pref = db.execute(
        select(UserLanguagePreference).where(UserLanguagePreference.user_id == user.id)
    ).scalar_one_or_none()

    goal = db.execute(
        select(NutritionGoal).where(NutritionGoal.user_id == user.id)
    ).scalar_one_or_none()

    latest_risk = db.execute(
        select(NutritionRiskAssessment)
        .where(NutritionRiskAssessment.user_id == user.id)
        .order_by(NutritionRiskAssessment.assessed_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    session_count = db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
    ).scalar() or 0

    msg_count = db.execute(
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user.id)
    ).scalar() or 0

    plan_count = db.execute(
        select(func.count(NutritionPlan.id)).where(NutritionPlan.user_id == user.id)
    ).scalar() or 0

    return SuccessResponse(
        data=AdminUserDetail(
            id=user.id,
            phone=user.phone,
            is_active=user.is_active,
            is_onboarded=user.is_onboarded,
            created_at=user.created_at,
            updated_at=user.updated_at,
            full_name=profile.full_name if profile else None,
            gender=profile.gender if profile else None,
            birth_date=_iso(profile.birth_date) if profile else None,
            height_cm=profile.height_cm if profile else None,
            weight_kg=profile.weight_kg if profile else None,
            target_weight_kg=profile.target_weight_kg if profile else None,
            language=lang_pref.language_code if lang_pref else None,
            goal_type=goal.goal_type if goal else None,
            risk_level=latest_risk.risk_level if latest_risk else None,
            chat_session_count=int(session_count),
            chat_message_count=int(msg_count),
            nutrition_plan_count=int(plan_count),
        )
    )


def _export_response(export_type: str, user: User, data: dict) -> JSONResponse:
    payload = AdminExportResponse(
        export_type=export_type,
        exported_at=_now_iso(),
        user=AdminExportUser(
            id=user.id,
            phone=user.phone,
            created_at=_iso(user.created_at),  # type: ignore[arg-type]
        ),
        data=data,
    )
    filename = f"user-{user.id}-{export_type}-export.json"
    return JSONResponse(
        content=payload.model_dump(),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{user_id}/export/onboarding")
def export_onboarding(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> JSONResponse:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)
    return _export_response("onboarding", user, _onboarding_data(db, user))


@router.get("/{user_id}/export/chat")
def export_chat(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> JSONResponse:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)
    return _export_response("chat", user, _chat_data(db, user))


@router.get("/{user_id}/export/nutrition")
def export_nutrition(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> JSONResponse:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)
    return _export_response("nutrition", user, _nutrition_data(db, user))


@router.get("/{user_id}/export/all")
def export_all(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> JSONResponse:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)
    data = {
        "onboarding": _onboarding_data(db, user),
        "chat": _chat_data(db, user),
        "nutrition": _nutrition_data(db, user),
    }
    return _export_response("all", user, data)


@router.delete("/{user_id}", response_model=SuccessResponse[AdminDeleteResponse])
def delete_user(
    user_id: str,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> SuccessResponse[AdminDeleteResponse]:
    """
    Completely delete a user and all associated data.

    Steps:
    1. Verify user exists.
    2. Collect record counts for the response.
    3. Collect audio file paths before deletion.
    4. Delete the User row — SQLite CASCADE removes all related records.
    5. Commit DB transaction.
    6. Delete audio files from filesystem (best-effort, after commit).
    """
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise_http_error("User not found", status_code=404)

    # Collect counts before deletion
    counts: dict[str, int] = {}

    def _count(model, col):
        return int(db.execute(select(func.count(col)).where(col == user_id)).scalar() or 0)

    counts["otps"] = _count(AuthOTP, AuthOTP.user_id)
    counts["audit_logs"] = _count(AuditLog, AuditLog.user_id)
    counts["profiles"] = _count(UserProfile, UserProfile.user_id)
    counts["medical_flags"] = _count(UserMedicalFlag, UserMedicalFlag.user_id)
    counts["medications"] = _count(Medication, Medication.user_id)
    counts["allergies"] = _count(Allergy, Allergy.user_id)
    counts["lifestyle_profiles"] = _count(LifestyleProfile, LifestyleProfile.user_id)
    counts["food_preferences"] = _count(FoodPreference, FoodPreference.user_id)
    counts["behavior_profiles"] = _count(BehaviorProfile, BehaviorProfile.user_id)
    counts["nutrition_goals"] = _count(NutritionGoal, NutritionGoal.user_id)
    counts["risk_assessments"] = _count(NutritionRiskAssessment, NutritionRiskAssessment.user_id)
    counts["nutrition_plans"] = _count(NutritionPlan, NutritionPlan.user_id)
    counts["nutrition_plan_calendars"] = _count(NutritionPlanCalendar, NutritionPlanCalendar.user_id)

    session_ids_result = db.execute(
        select(ChatSession.id).where(ChatSession.user_id == user_id)
    ).scalars().all()
    session_ids = list(session_ids_result)

    if session_ids:
        counts["chat_sessions"] = len(session_ids)
        counts["chat_messages"] = int(
            db.execute(
                select(func.count(ChatMessage.id))
                .where(ChatMessage.session_id.in_(session_ids))
            ).scalar() or 0
        )
        counts["audio_messages"] = int(
            db.execute(
                select(func.count(AudioMessage.id))
                .where(AudioMessage.session_id.in_(session_ids))
            ).scalar() or 0
        )
    else:
        counts["chat_sessions"] = 0
        counts["chat_messages"] = 0
        counts["audio_messages"] = 0

    counts["meal_entries"] = _count(MealEntry, MealEntry.user_id)
    counts["daily_checkins"] = _count(DailyCheckIn, DailyCheckIn.user_id)
    counts["progress_entries"] = _count(ProgressEntry, ProgressEntry.user_id)
    counts["weekly_reports"] = _count(WeeklyReport, WeeklyReport.user_id)

    # Collect audio file paths for post-commit cleanup
    audio_file_paths: list[str] = []
    if session_ids:
        audio_rows = db.execute(
            select(AudioMessage.file_path)
            .where(AudioMessage.session_id.in_(session_ids))
        ).scalars().all()
        audio_file_paths = [p for p in audio_rows if p]

    # Delete user — CASCADE handles all related DB records
    db.delete(user)
    # get_session commits on success / rollbacks on exception

    # Post-commit: delete audio files from filesystem (best-effort)
    if audio_file_paths:
        audio_root = Path(settings.AUDIO_STORAGE_PATH).resolve()
        for file_path in audio_file_paths:
            try:
                candidate = Path(file_path)
                # Safety: only delete files inside the configured audio storage root
                resolved = candidate.resolve() if candidate.is_absolute() else (audio_root / candidate).resolve()
                if resolved.is_relative_to(audio_root) and resolved.is_file():
                    resolved.unlink()
            except Exception:
                pass  # Never let file cleanup block the response

    return SuccessResponse(
        data=AdminDeleteResponse(
            deleted=True,
            user_id=user_id,
            deleted_records=counts,
        )
    )
