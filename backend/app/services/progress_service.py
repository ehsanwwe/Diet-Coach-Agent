"""Progress service: aggregation, behavior wins, suggested focus. Pure Python — no AI call."""
from __future__ import annotations
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.progress import DailyCheckIn
from app.repositories import progress_repository
from app.schemas.progress import (
    BehaviorWin,
    CheckInRequest,
    CheckInResponse,
    ProgressSummaryResponse,
    WeeklyReportData,
    WeeklyReportResponse,
    WeightTrend,
)

_EMPTY_SUMMARY_MSG = "هنوز هیچ ثبتی ندارید. اولین ثبت وضعیت را همین‌جا انجام دهید."
_EMPTY_WEEKLY_MSG = "هنوز داده کافی برای گزارش هفتگی ندارید. پس از ۳ روز ثبت، گزارش آماده می‌شود."


# ─── 1. POST /progress/check-in ──────────────────────────────────────────────

def submit_check_in(db: Session, user: User, body: CheckInRequest) -> CheckInResponse:
    checkin = progress_repository.upsert_checkin(
        db,
        user.id,
        check_date=body.check_date,
        weight_kg=body.weight_kg,
        hunger_level=body.hunger_level,
        sleep_hours=body.sleep_hours,
        stress_level=body.stress_level,
        activity_minutes=body.activity_minutes,
        adherence_notes=body.adherence_notes,
    )
    db.commit()
    db.refresh(checkin)
    return CheckInResponse.model_validate(checkin)


# ─── 2. GET /progress/summary ────────────────────────────────────────────────

def get_summary(db: Session, user: User) -> ProgressSummaryResponse:
    checkins_newest_first = progress_repository.get_recent_checkins(db, user.id, days=14)
    if not checkins_newest_first:
        return ProgressSummaryResponse(
            has_data=False,
            empty_state_message=_EMPTY_SUMMARY_MSG,
        )

    checkins_oldest_first = list(reversed(checkins_newest_first))
    weights = [c.weight_kg for c in checkins_oldest_first if c.weight_kg is not None]
    latest_weight = weights[-1] if weights else None

    weight_trend: WeightTrend | None = None
    if len(weights) >= 2:
        weight_trend = WeightTrend(
            first=weights[0],
            last=weights[-1],
            delta=round(weights[-1] - weights[0], 2),
        )

    streak = _compute_logging_streak(checkins_newest_first)
    wins = _compute_behavior_wins(checkins_newest_first[:7], streak)

    recent = [CheckInResponse.model_validate(c) for c in checkins_newest_first]

    return ProgressSummaryResponse(
        has_data=True,
        recent_checkins=recent,
        weight_series=weights,
        latest_weight_kg=latest_weight,
        weight_trend=weight_trend,
        behavior_wins=wins,
        logging_streak=streak,
        empty_state_message=None,
    )


# ─── 3. GET /progress/weekly-report ──────────────────────────────────────────

def get_weekly_report(db: Session, user: User) -> WeeklyReportResponse:
    today = date.today()
    # Monday of the current week
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    checkins = progress_repository.get_checkins_between(db, user.id, week_start, week_end)
    if not checkins:
        return WeeklyReportResponse(
            has_report=False,
            week_start=week_start,
            week_end=week_end,
            empty_state_message=_EMPTY_WEEKLY_MSG,
        )

    data = _compute_weekly_report(checkins)
    # Persist (overwrite if already exists for this week)
    progress_repository.save_weekly_report(
        db,
        user.id,
        week_start=week_start,
        week_end=week_end,
        report_data=json.loads(data.model_dump_json()),
    )
    db.commit()

    return WeeklyReportResponse(
        has_report=True,
        week_start=week_start,
        week_end=week_end,
        report=data,
        empty_state_message=None,
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _compute_logging_streak(checkins_newest_first: list[DailyCheckIn]) -> int:
    """Count consecutive days ending today (or yesterday) with a check-in."""
    if not checkins_newest_first:
        return 0
    today = date.today()
    dates = {c.check_date for c in checkins_newest_first}
    # Allow streak to start from today or yesterday (user may not have checked in yet today)
    cursor = today if today in dates else (today - timedelta(days=1))
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _compute_behavior_wins(checkins_recent_7: list[DailyCheckIn], streak: int) -> list[BehaviorWin]:
    """Compute behavior win chips from the last 7 check-ins."""
    sleeps = [c.sleep_hours for c in checkins_recent_7 if c.sleep_hours is not None]
    activities = [c.activity_minutes for c in checkins_recent_7 if c.activity_minutes is not None]
    stresses = [c.stress_level for c in checkins_recent_7 if c.stress_level is not None]
    hungers = [c.hunger_level for c in checkins_recent_7 if c.hunger_level is not None]

    avg_sleep = sum(sleeps) / len(sleeps) if sleeps else None
    avg_activity = sum(activities) / len(activities) if activities else None
    avg_stress = sum(stresses) / len(stresses) if stresses else None
    avg_hunger = sum(hungers) / len(hungers) if hungers else None

    wins: list[BehaviorWin] = []
    wins.append(BehaviorWin(
        key="sleep", label_key="winSleep",
        achieved=avg_sleep is not None and avg_sleep >= 7.0,
        value=f"{avg_sleep:.1f}" if avg_sleep is not None else None,
        tracked=True,
    ))
    wins.append(BehaviorWin(
        key="activity", label_key="winActivity",
        achieved=avg_activity is not None and avg_activity >= 30,
        value=f"{int(avg_activity)}" if avg_activity is not None else None,
        tracked=True,
    ))
    wins.append(BehaviorWin(
        key="logging", label_key="winLogging",
        achieved=streak >= 3,
        value=str(streak),
        tracked=True,
    ))
    wins.append(BehaviorWin(
        key="low_stress", label_key="winLowStress",
        achieved=avg_stress is not None and avg_stress <= 2.5,
        value=f"{avg_stress:.1f}" if avg_stress is not None else None,
        tracked=True,
    ))
    wins.append(BehaviorWin(
        key="low_hunger", label_key="winLowHunger",
        achieved=avg_hunger is not None and avg_hunger <= 2.5,
        value=f"{avg_hunger:.1f}" if avg_hunger is not None else None,
        tracked=True,
    ))
    # Not-yet-tracked in v1 — surface as informational chips
    wins.append(BehaviorWin(key="protein", label_key="winProtein", achieved=False, value=None, tracked=False))
    wins.append(BehaviorWin(key="fiber", label_key="winFiber", achieved=False, value=None, tracked=False))
    wins.append(BehaviorWin(key="hydration", label_key="winHydration", achieved=False, value=None, tracked=False))
    return wins


def _compute_weekly_report(checkins_oldest_first: list[DailyCheckIn]) -> WeeklyReportData:
    weights = [c.weight_kg for c in checkins_oldest_first if c.weight_kg is not None]
    hungers = [c.hunger_level for c in checkins_oldest_first if c.hunger_level is not None]
    sleeps = [c.sleep_hours for c in checkins_oldest_first if c.sleep_hours is not None]
    stresses = [c.stress_level for c in checkins_oldest_first if c.stress_level is not None]
    activities = [c.activity_minutes for c in checkins_oldest_first if c.activity_minutes is not None]

    weight_trend: WeightTrend | None = None
    if len(weights) >= 2:
        weight_trend = WeightTrend(first=weights[0], last=weights[-1], delta=round(weights[-1] - weights[0], 2))

    avg_hunger = round(sum(hungers) / len(hungers), 1) if hungers else None
    avg_sleep = round(sum(sleeps) / len(sleeps), 1) if sleeps else None
    avg_stress = round(sum(stresses) / len(stresses), 1) if stresses else None
    total_activity = sum(activities)
    logging_days = len(checkins_oldest_first)
    adherence_pct = round(logging_days / 7 * 100)

    sleep_stress_note: str | None = None
    if avg_sleep is not None and avg_stress is not None and avg_sleep < 6 and avg_stress > 3:
        sleep_stress_note = "خواب کم و استرس بالا — بهبود خواب اولویت هفته بعد باشد."

    return WeeklyReportData(
        weight_trend=weight_trend,
        weight_series=weights,
        avg_hunger=avg_hunger,
        avg_sleep=avg_sleep,
        avg_stress=avg_stress,
        total_activity_minutes=total_activity,
        logging_days=logging_days,
        adherence_pct=adherence_pct,
        sleep_stress_note=sleep_stress_note,
        suggested_focus=_suggest_focus(avg_hunger, avg_sleep, avg_stress, total_activity, logging_days),
    )


def _suggest_focus(
    avg_hunger: float | None,
    avg_sleep: float | None,
    avg_stress: float | None,
    total_activity: int,
    logging_days: int,
) -> str:
    if logging_days < 3:
        return "ثبت روزانه را منظم‌تر کنید — داده بیشتر، راهنمایی بهتر."
    if avg_sleep is not None and avg_sleep < 6.5:
        return "بهبود کیفیت خواب اولویت اصلی: هدف ۷–۸ ساعت خواب شبانه."
    if avg_stress is not None and avg_stress >= 4:
        return "مدیریت استرس: تنفس عمیق یا پیاده‌روی کوتاه بعد از ناهار."
    if total_activity < 100:
        return "افزایش تحرک: ۳۰ دقیقه پیاده‌روی روزانه شروع خوبی است."
    if avg_hunger is not None and avg_hunger > 3:
        return "تنظیم وعده‌ها برای کاهش گرسنگی: وعده‌های کوچک‌تر و مکرر."
    return "ادامه مسیر فعلی — روند شما مثبت است!"
