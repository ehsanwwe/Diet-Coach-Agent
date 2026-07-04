"""Process-local progress jobs for week-plan generation (no database migration)."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import logging
from threading import Lock
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.user import User
from app.services import calendar_service

_jobs: dict[str, dict] = {}
_lock = Lock()
logger = logging.getLogger(__name__)


def _message(locale: str, key: str, day: int | None = None) -> str:
    messages = {
        "fa": {
            "preparing_profile": "در حال آماده‌سازی اطلاعات شما...",
            "requesting_week_plan": "در حال درخواست برنامه کامل ۷ روزه...",
            "reviewing_plan": "در حال بررسی کیفیت برنامه...",
            "repairing_plan_1": "در حال اصلاح برنامه با توجه به محدودیت‌ها...",
            "repairing_plan_2": "در حال اصلاح نهایی برنامه...",
            "saving_day": f"در حال ذخیره روز {day or 1} از ۷...",
            "completed": "برنامه غذایی شما آماده شد.",
            "failed": "ساخت برنامه غذایی ناموفق بود. دوباره تلاش کنید.",
        },
        "en": {
            "preparing_profile": "Preparing your profile...", "requesting_week_plan": "Requesting your complete 7-day plan...",
            "reviewing_plan": "Reviewing plan quality...", "repairing_plan_1": "Repairing the plan for your restrictions...",
            "repairing_plan_2": "Applying final plan repairs...", "saving_day": f"Saving day {day or 1} of 7...",
            "completed": "Your meal plan is ready.",
            "failed": "Meal plan generation failed. Please retry.",
        },
        "ar": {
            "preparing_profile": "جارٍ إعداد معلوماتك...", "requesting_week_plan": "جارٍ طلب خطة كاملة لمدة 7 أيام...",
            "reviewing_plan": "جارٍ مراجعة جودة الخطة...", "repairing_plan_1": "جارٍ تعديل الخطة وفق قيودك...",
            "repairing_plan_2": "جارٍ إجراء التعديلات النهائية...", "saving_day": f"جارٍ حفظ اليوم {day or 1} من 7...",
            "completed": "خطة وجباتك جاهزة.",
            "failed": "فشل إنشاء خطة الوجبات. يرجى المحاولة مجدداً.",
        },
    }
    return messages.get(locale, messages["en"]).get(key, key)


def create(user_id: str, locale: str, start_date: date | None, force: bool) -> dict:
    job_id = str(uuid4())
    job = {
        "job_id": job_id, "user_id": user_id, "locale": locale, "start_date": start_date,
        "force": force, "status": "queued", "stage": "preparing_profile",
        "current_day_index": None, "total_days": 7, "message": _message(locale, "preparing_profile"),
        "error": None, "result": None, "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        _jobs[job_id] = job
    return public(job)


def public(job: dict) -> dict:
    return {key: deepcopy(value) for key, value in job.items() if key not in {"user_id", "start_date", "force"}}


def get(job_id: str, user_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return public(job) if job and job["user_id"] == user_id else None


def _update(job_id: str, **values) -> None:
    with _lock:
        _jobs[job_id].update(values, updated_at=datetime.now(timezone.utc).isoformat())


def run(job_id: str) -> None:
    with _lock:
        job = dict(_jobs[job_id])
    _update(job_id, status="running")
    db = SessionLocal()
    try:
        user = db.get(User, job["user_id"])
        if user is None:
            raise RuntimeError("User no longer exists")

        def progress(stage: str, key: str, day: int | None) -> None:
            _update(job_id, stage=stage, current_day_index=day, message=_message(job["locale"], key, day))

        result = calendar_service.generate_week(
            db, user, job["locale"], job["start_date"], job["force"], progress=progress,
        )
        _update(
            job_id, status="completed", stage="completed", current_day_index=7,
            message=_message(job["locale"], "completed"), result=result.model_dump(mode="json"),
        )
    except Exception:
        logger.exception("Week-plan generation job %s failed", job_id)
        db.rollback()
        _update(
            job_id, status="failed", stage="failed",
            message=_message(job["locale"], "failed"), error=_message(job["locale"], "failed"),
        )
    finally:
        db.close()
