"""Progress repository: SQLAlchemy 2.x data access for DailyCheckIn, WeeklyReport."""
from __future__ import annotations
import json
from datetime import date, datetime, time, timezone
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.progress import DailyCheckIn, ProgressEntry, WeeklyReport


def upsert_checkin(
    db: Session,
    user_id: str,
    *,
    check_date: date,
    weight_kg: float | None = None,
    waist_cm: float | None = None,
    hunger_level: int | None = None,
    hunger_level_1_10: int | None = None,
    sleep_hours: float | None = None,
    sleep_quality: int | None = None,
    energy_level: int | None = None,
    stress_level: int | None = None,
    activity_minutes: int | None = None,
    cravings: str | None = None,
    craving_type: str | None = None,
    eating_location: str | None = None,
    planned_eating_out: bool | None = None,
    adherence_level: int | None = None,
    symptoms: str | None = None,
    adherence_notes: str | None = None,
) -> DailyCheckIn:
    """Insert a new check-in or update the existing one for (user_id, check_date)."""
    result = db.execute(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_date == check_date,
        )
    )
    checkin = result.scalar_one_or_none()
    if checkin is None:
        checkin = DailyCheckIn(user_id=user_id, check_date=check_date)
        db.add(checkin)
    # Always set — None overwrites prior value. This matches PUT semantics on a single resource per day.
    checkin.weight_kg = weight_kg
    checkin.waist_cm = waist_cm
    checkin.hunger_level = hunger_level
    checkin.hunger_level_1_10 = hunger_level_1_10
    checkin.sleep_hours = sleep_hours
    checkin.sleep_quality = sleep_quality
    checkin.energy_level = energy_level
    checkin.stress_level = stress_level
    checkin.activity_minutes = activity_minutes
    checkin.cravings = cravings
    checkin.craving_type = craving_type
    checkin.eating_location = eating_location
    checkin.planned_eating_out = planned_eating_out
    checkin.adherence_level = adherence_level
    checkin.symptoms = symptoms
    checkin.adherence_notes = adherence_notes
    db.flush()
    return checkin


def get_recent_checkins(db: Session, user_id: str, days: int = 14) -> list[DailyCheckIn]:
    """Return up to `days` most-recent check-ins, newest first."""
    result = db.execute(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user_id)
        .order_by(desc(DailyCheckIn.check_date))
        .limit(days)
    )
    return list(result.scalars().all())


def get_checkins_between(
    db: Session, user_id: str, week_start: date, week_end: date
) -> list[DailyCheckIn]:
    """Return check-ins within [week_start, week_end] inclusive, oldest first."""
    result = db.execute(
        select(DailyCheckIn)
        .where(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_date >= week_start,
            DailyCheckIn.check_date <= week_end,
        )
        .order_by(DailyCheckIn.check_date.asc())
    )
    return list(result.scalars().all())


def get_progress_entries_between(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date,
    entry_types: list[str] | None = None,
) -> list[ProgressEntry]:
    """Return generic progress entries within [start_date, end_date], oldest first."""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    stmt = (
        select(ProgressEntry)
        .where(
            ProgressEntry.user_id == user_id,
            ProgressEntry.recorded_at >= start_dt,
            ProgressEntry.recorded_at <= end_dt,
        )
        .order_by(ProgressEntry.recorded_at.asc())
    )
    if entry_types:
        stmt = stmt.where(ProgressEntry.entry_type.in_(entry_types))
    result = db.execute(stmt)
    return list(result.scalars().all())


def get_or_create_weekly_report(
    db: Session, user_id: str, week_start: date
) -> WeeklyReport | None:
    result = db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user_id, WeeklyReport.week_start == week_start)
        .order_by(desc(WeeklyReport.generated_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_latest_weekly_report(db: Session, user_id: str) -> WeeklyReport | None:
    result = db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user_id)
        .order_by(desc(WeeklyReport.generated_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def save_weekly_report(
    db: Session,
    user_id: str,
    *,
    week_start: date,
    week_end: date,
    report_data: dict,
) -> WeeklyReport:
    existing = get_or_create_weekly_report(db, user_id, week_start)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if existing is None:
        existing = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            report_data="",
            generated_at=now,
        )
        db.add(existing)
    existing.week_end = week_end
    existing.report_data = json.dumps(report_data, ensure_ascii=False)
    existing.generated_at = now
    db.flush()
    return existing
