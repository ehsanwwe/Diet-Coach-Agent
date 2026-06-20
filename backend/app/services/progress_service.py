"""Progress service: aggregation, behavior wins, suggested focus. Pure Python — no AI call."""
from __future__ import annotations
import json
from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.chat import MealEntry
from app.models.user import User
from app.models.progress import DailyCheckIn
from app.repositories import calendar_repository, onboarding_repository, progress_repository
from app.schemas.progress import (
    BehaviorWin,
    CheckInRequest,
    CheckInResponse,
    DataCompleteness,
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
        waist_cm=body.waist_cm,
        hunger_level=body.hunger_level,
        hunger_level_1_10=body.hunger_level_1_10,
        sleep_hours=body.sleep_hours,
        sleep_quality=body.sleep_quality,
        energy_level=body.energy_level,
        stress_level=body.stress_level,
        activity_minutes=body.activity_minutes,
        cravings=body.cravings,
        craving_type=body.craving_type,
        eating_location=body.eating_location,
        planned_eating_out=body.planned_eating_out,
        adherence_level=body.adherence_level,
        symptoms=body.symptoms,
        adherence_notes=body.adherence_notes,
    )
    db.commit()
    db.refresh(checkin)
    return _checkin_response(checkin)


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

    recent = [_checkin_response(c) for c in checkins_newest_first]
    energy_values = [c.energy_level for c in checkins_newest_first[:7] if c.energy_level is not None]
    hunger_10_values = [
        c.hunger_level_1_10 for c in checkins_newest_first[:7] if c.hunger_level_1_10 is not None
    ]

    return ProgressSummaryResponse(
        has_data=True,
        recent_checkins=recent,
        weight_series=weights,
        latest_weight_kg=latest_weight,
        weight_trend=weight_trend,
        avg_energy_level=_avg(energy_values),
        avg_hunger_level_1_10=_avg(hunger_10_values),
        craving_summary=_summarize_text_values([c.cravings for c in checkins_newest_first[:7]]),
        eating_location_summary=_summarize_counts([c.eating_location for c in checkins_newest_first[:7]]),
        symptom_summary=_summarize_text_values([c.symptoms for c in checkins_newest_first[:7]]),
        adaptation_hint=any(_needs_adaptation(c) for c in checkins_newest_first[:7]),
        human_review_recommended=any(_has_red_flag_symptoms(c.symptoms) for c in checkins_newest_first[:7]),
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

    progress_entries = progress_repository.get_progress_entries_between(
        db,
        user.id,
        week_start,
        week_end,
        entry_types=["weight", "weight_kg", "waist", "waist_cm"],
    )
    meals = _get_meals_between(db, user.id, week_start, week_end)
    locale = calendar_repository.resolve_locale(None, calendar_repository.get_user_language(db, user.id))
    risk = onboarding_repository.get_latest_risk_assessment(db, user.id)
    medical_flags = onboarding_repository.get_medical_flags(db, user.id)
    data = _compute_weekly_report(
        checkins,
        week_start=week_start,
        week_end=week_end,
        progress_entries=progress_entries,
        meals=meals,
        locale=locale,
        risk_level=risk.risk_level if risk else "low",
        active_medical_flags=[
            f.condition_code
            for f in medical_flags
            if f.has_condition and f.condition_code != onboarding_repository.WARNING_SYMPTOMS_CODE
        ],
    )
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


def _avg(values: list[float | int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _trend(values: list[float]) -> WeightTrend | None:
    if len(values) < 2:
        return None
    return WeightTrend(first=values[0], last=values[-1], delta=round(values[-1] - values[0], 2))


def _has_red_flag_symptoms(symptoms: str | None) -> bool:
    if not symptoms:
        return False
    text = symptoms.lower()
    return any(
        term in text
        for term in (
            "chest pain",
            "blood in stool",
            "faint",
            "fainting",
            "severe dizziness",
            "shortness of breath",
            "درد قفسه",
            "خون در مدفوع",
            "غش",
            "سرگیجه شدید",
            "تنگی نفس",
        )
    )


def _needs_adaptation(c: DailyCheckIn) -> bool:
    return any(
        (
            c.sleep_hours is not None and c.sleep_hours < 6,
            c.sleep_quality is not None and c.sleep_quality <= 2,
            c.energy_level is not None and c.energy_level <= 2,
            c.stress_level is not None and c.stress_level >= 4,
            c.hunger_level_1_10 is not None and c.hunger_level_1_10 >= 8,
            c.hunger_level is not None and c.hunger_level >= 4,
            bool(c.cravings),
            bool(c.planned_eating_out),
            c.adherence_level is not None and c.adherence_level <= 2,
            bool(c.symptoms),
        )
    )


def _checkin_response(c: DailyCheckIn) -> CheckInResponse:
    safety_notes = ["red_flag_symptoms_reported"] if _has_red_flag_symptoms(c.symptoms) else []
    return CheckInResponse.model_validate(c).model_copy(
        update={
            "adaptation_hint": _needs_adaptation(c),
            "human_review_recommended": bool(safety_notes),
            "safety_notes": safety_notes,
        }
    )


def _summarize_counts(values: list[str | None]) -> str | None:
    clean = [v.strip() for v in values if v and v.strip()]
    if not clean:
        return None
    counts = Counter(clean)
    return ", ".join(f"{key}={count}" for key, count in counts.most_common(3))


def _summarize_text_values(values: list[str | None]) -> str | None:
    clean = [v.strip() for v in values if v and v.strip()]
    if not clean:
        return None
    return " | ".join(clean[-3:])


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


def _get_meals_between(db: Session, user_id: str, week_start: date, week_end: date) -> list[MealEntry]:
    start_dt = datetime.combine(week_start, time.min)
    end_dt = datetime.combine(week_end + timedelta(days=1), time.min)
    result = db.execute(
        select(MealEntry)
        .where(
            MealEntry.user_id == user_id,
            MealEntry.logged_at >= start_dt,
            MealEntry.logged_at < end_dt,
        )
        .order_by(desc(MealEntry.logged_at))
        .limit(30)
    )
    return list(result.scalars().all())


def _compute_weekly_report(
    checkins_oldest_first: list[DailyCheckIn],
    *,
    week_start: date,
    week_end: date,
    progress_entries: list[Any],
    meals: list[MealEntry],
    locale: str,
    risk_level: str,
    active_medical_flags: list[str],
) -> WeeklyReportData:
    weights = [c.weight_kg for c in checkins_oldest_first if c.weight_kg is not None]
    if not weights:
        weights = [
            e.value_numeric
            for e in progress_entries
            if e.entry_type in {"weight", "weight_kg"} and e.value_numeric is not None
        ]
    waists = [c.waist_cm for c in checkins_oldest_first if c.waist_cm is not None]
    if not waists:
        waists = [
            e.value_numeric
            for e in progress_entries
            if e.entry_type in {"waist", "waist_cm"} and e.value_numeric is not None
        ]
    hungers = [c.hunger_level for c in checkins_oldest_first if c.hunger_level is not None]
    hungers_10 = [c.hunger_level_1_10 for c in checkins_oldest_first if c.hunger_level_1_10 is not None]
    sleeps = [c.sleep_hours for c in checkins_oldest_first if c.sleep_hours is not None]
    sleep_quality = [c.sleep_quality for c in checkins_oldest_first if c.sleep_quality is not None]
    energy = [c.energy_level for c in checkins_oldest_first if c.energy_level is not None]
    stresses = [c.stress_level for c in checkins_oldest_first if c.stress_level is not None]
    activities = [c.activity_minutes for c in checkins_oldest_first if c.activity_minutes is not None]
    adherence = [c.adherence_level for c in checkins_oldest_first if c.adherence_level is not None]

    avg_hunger = _avg(hungers)
    avg_hunger_10 = _avg(hungers_10)
    avg_sleep = _avg(sleeps)
    avg_sleep_quality = _avg(sleep_quality)
    avg_energy = _avg(energy)
    avg_stress = _avg(stresses)
    avg_adherence = _avg(adherence)
    total_activity = sum(activities)
    logging_days = len(checkins_oldest_first)
    adherence_pct = round(logging_days / 7 * 100)
    confidence_level = "high" if logging_days >= 5 else "medium" if logging_days >= 3 else "low"

    data_completeness = DataCompleteness(
        checkin_days=logging_days,
        expected_days=7,
        checkin_pct=adherence_pct,
        weight_points=len(weights),
        waist_points=len(waists),
        meal_entries=len(meals),
        has_sleep_data=bool(sleeps),
        has_stress_data=bool(stresses),
        has_hunger_data=bool(hungers or hungers_10),
        has_adherence_data=bool(adherence),
    )

    craving_patterns = _weekly_craving_patterns(checkins_oldest_first)
    risky_time_windows = _weekly_risky_time_windows(checkins_oldest_first, meals)
    risky_meals = _weekly_risky_meals(meals)
    eating_out_count = sum(1 for c in checkins_oldest_first if c.planned_eating_out)
    eating_out_pattern = _eating_out_pattern(eating_out_count, checkins_oldest_first, locale)
    red_flag_count = sum(1 for c in checkins_oldest_first if _has_red_flag_symptoms(c.symptoms))
    requires_human_review = risk_level in {"high", "clinical_review_required"} or red_flag_count > 0
    safety_notes = _weekly_safety_notes(
        risk_level=risk_level,
        active_medical_flags=active_medical_flags,
        red_flag_count=red_flag_count,
        locale=locale,
    )
    adherence_summary = _adherence_summary(avg_adherence, adherence_pct, locale)
    sleep_food_relationship = _sleep_food_relationship(avg_sleep, craving_patterns, locale)
    stress_food_relationship = _stress_food_relationship(avg_stress, craving_patterns, adherence, locale)
    protein_quality = _meal_quality_summary(meals, "protein_quality", locale)
    fiber_quality = _meal_quality_summary(meals, "fiber_vegetable_quality", locale)
    simple_sugar_quality = _meal_quality_summary(meals, "simple_sugar_quality", locale)
    hydration_quality = _hydration_quality(checkins_oldest_first, locale)
    behavior_pattern_summary = _behavior_pattern_summary(
        craving_patterns,
        eating_out_pattern,
        sleep_food_relationship,
        stress_food_relationship,
        locale,
    )
    strengths = _three_strengths(logging_days, avg_sleep, avg_stress, total_activity, craving_patterns, meals, locale)
    adjustments = _two_small_adjustments(
        avg_sleep,
        avg_stress,
        avg_hunger_10,
        avg_hunger,
        eating_out_count,
        protein_quality,
        fiber_quality,
        simple_sugar_quality,
        locale,
    )
    next_goal = _next_week_small_goal(adjustments, logging_days, locale)
    monitoring_notes = _monitoring_notes(data_completeness, red_flag_count, locale)
    summary = _weekly_summary(logging_days, confidence_level, behavior_pattern_summary, locale)

    sleep_stress_note: str | None = None
    if avg_sleep is not None and avg_stress is not None and avg_sleep < 6 and avg_stress > 3:
        sleep_stress_note = _t(locale, "sleep_stress_note")

    return WeeklyReportData(
        summary=summary,
        date_range={"start": week_start, "end": week_end},
        weight_trend=_trend(weights),
        waist_trend=_trend(waists),
        weight_series=weights,
        waist_series=waists,
        avg_hunger=avg_hunger,
        avg_hunger_level_1_10=avg_hunger_10,
        avg_sleep=avg_sleep,
        avg_sleep_quality=avg_sleep_quality,
        avg_energy_level=avg_energy,
        avg_stress=avg_stress,
        avg_adherence_level=avg_adherence,
        total_activity_minutes=total_activity,
        logging_days=logging_days,
        adherence_pct=adherence_pct,
        adherence_summary=adherence_summary,
        risky_meals=risky_meals,
        risky_time_windows=risky_time_windows,
        craving_patterns=craving_patterns,
        craving_summary=_summarize_text_values([c.cravings for c in checkins_oldest_first]),
        eating_location_summary=_summarize_counts([c.eating_location for c in checkins_oldest_first]),
        eating_out_pattern=eating_out_pattern,
        symptom_summary=_summarize_text_values([c.symptoms for c in checkins_oldest_first]),
        protein_quality=protein_quality,
        fiber_quality=fiber_quality,
        hydration_quality=hydration_quality,
        simple_sugar_quality=simple_sugar_quality,
        sleep_food_relationship=sleep_food_relationship,
        stress_food_relationship=stress_food_relationship,
        behavior_pattern_summary=behavior_pattern_summary,
        three_strengths=strengths,
        two_small_adjustments=adjustments,
        next_week_small_goal=next_goal,
        monitoring_notes=monitoring_notes,
        safety_notes=safety_notes,
        requires_human_review=requires_human_review,
        generated_from_data_points={
            "checkins": len(checkins_oldest_first),
            "progress_entries": len(progress_entries),
            "meals": len(meals),
            "red_flag_symptom_days": red_flag_count,
        },
        data_completeness=data_completeness,
        confidence_level=confidence_level,
        adaptation_hint=any(_needs_adaptation(c) for c in checkins_oldest_first),
        human_review_recommended=requires_human_review,
        sleep_stress_note=sleep_stress_note,
        suggested_focus=_suggest_focus(avg_hunger, avg_sleep, avg_stress, total_activity, logging_days),
    )


_TEXT = {
    "fa": {
        "summary_empty": "این هفته چند داده ثبت شده و گزارش با احتیاط تفسیر می‌شود.",
        "summary": "گزارش این هفته بر اساس داده‌های ثبت‌شده ساخته شده و روی الگوهای قابل اقدام تمرکز دارد.",
        "sleep_stress_note": "خواب کوتاه همراه با استرس بالاتر دیده می‌شود؛ هفته بعد یک بهبود کوچک در خواب می‌تواند کمک‌کننده باشد.",
        "no_data": "داده کافی برای قضاوت دقیق وجود ندارد.",
        "steady_logging": "ثبت منظم‌تر داده‌ها تصویر دقیق‌تری از بدن و رفتار غذایی می‌دهد.",
        "activity_strength": "تحرک این هفته ثبت شده و می‌تواند پایه خوبی برای ادامه باشد.",
        "sleep_strength": "خواب این هفته نسبتاً پایدار بوده است.",
        "stress_strength": "سطح استرس ثبت‌شده این هفته خیلی بالا نبوده است.",
        "meal_strength": "ثبت وعده‌ها کمک می‌کند کیفیت پروتئین، فیبر و قند ساده بهتر دیده شود.",
        "craving_strength": "هوس‌ها ثبت شده‌اند و همین داده برای شناخت الگو مفید است.",
        "protein_unknown": "برای ارزیابی پروتئین، وعده‌های تحلیل‌شده بیشتری لازم است.",
        "fiber_unknown": "برای ارزیابی فیبر و سبزیجات، وعده‌های تحلیل‌شده بیشتری لازم است.",
        "sugar_unknown": "برای ارزیابی قند ساده، وعده‌های تحلیل‌شده بیشتری لازم است.",
        "hydration_unknown": "آب و مایعات به شکل مستقیم در چک‌این ثبت نمی‌شود؛ فعلاً فقط قابل پایش است.",
        "sleep_food": "در روزهای خواب کمتر، هوس یا گرسنگی می‌تواند پررنگ‌تر شود؛ این را هفته بعد پایش کنید.",
        "stress_food": "استرس بالاتر می‌تواند انتخاب‌های فوری یا هوس را بیشتر کند؛ یک مکث کوتاه قبل از خوردن کمک می‌کند.",
        "human_review": "به دلیل ریسک سلامت یا علائم هشدار، بهتر است گزارش با پزشک یا متخصص تغذیه مرور شود.",
        "ed_review": "با سابقه اختلال خوردن، از توصیه‌های محدودکننده و تمرکز شدید روی وزن پرهیز شود.",
        "red_flag": "علائم هشدار گزارش شده‌اند؛ پیگیری انسانی توصیه می‌شود.",
    },
    "en": {
        "summary_empty": "This week has limited data, so the report is interpreted cautiously.",
        "summary": "This weekly report focuses on actionable patterns from the data you logged.",
        "sleep_stress_note": "Short sleep and higher stress appeared together; a small sleep improvement is a useful next focus.",
        "no_data": "There is not enough data for a precise judgment.",
        "steady_logging": "More consistent logging will make body and eating patterns easier to interpret.",
        "activity_strength": "Activity was logged this week and can be a useful base to build on.",
        "sleep_strength": "Sleep looked relatively steady this week.",
        "stress_strength": "Logged stress was not very high this week.",
        "meal_strength": "Meal logging helps clarify protein, fiber, and simple sugar quality.",
        "craving_strength": "Cravings were logged, which is useful pattern data.",
        "protein_unknown": "More analyzed meals are needed to assess protein quality.",
        "fiber_unknown": "More analyzed meals are needed to assess fiber and vegetable quality.",
        "sugar_unknown": "More analyzed meals are needed to assess simple sugar quality.",
        "hydration_unknown": "Hydration is not directly tracked in check-ins yet; monitor it next week.",
        "sleep_food": "On shorter-sleep days, cravings or hunger may become stronger; monitor this next week.",
        "stress_food": "Higher stress may increase quick choices or cravings; a short pause before eating can help.",
        "human_review": "Because of health risk or warning symptoms, review this report with a clinician or dietitian.",
        "ed_review": "With eating-disorder history, avoid restrictive advice and strong weight focus.",
        "red_flag": "Warning symptoms were reported; human follow-up is recommended.",
    },
    "ar": {
        "summary_empty": "بيانات هذا الأسبوع محدودة، لذلك يتم تفسير التقرير بحذر.",
        "summary": "يركز تقرير هذا الأسبوع على أنماط عملية من البيانات المسجلة.",
        "sleep_stress_note": "ظهر نوم قصير مع توتر أعلى؛ تحسين بسيط في النوم قد يساعد الأسبوع القادم.",
        "no_data": "لا توجد بيانات كافية لحكم دقيق.",
        "steady_logging": "التسجيل المنتظم يجعل فهم الجسم والسلوك الغذائي أدق.",
        "activity_strength": "تم تسجيل نشاط هذا الأسبوع ويمكن البناء عليه.",
        "sleep_strength": "كان النوم مستقراً نسبياً هذا الأسبوع.",
        "stress_strength": "التوتر المسجل لم يكن مرتفعاً جداً هذا الأسبوع.",
        "meal_strength": "تسجيل الوجبات يساعد على فهم البروتين والألياف والسكر البسيط.",
        "craving_strength": "تم تسجيل الرغبات، وهذا مفيد لفهم النمط.",
        "protein_unknown": "نحتاج وجبات محللة أكثر لتقييم جودة البروتين.",
        "fiber_unknown": "نحتاج وجبات محللة أكثر لتقييم الألياف والخضار.",
        "sugar_unknown": "نحتاج وجبات محللة أكثر لتقييم السكر البسيط.",
        "hydration_unknown": "الترطيب غير مسجل مباشرة حالياً؛ راقبه الأسبوع القادم.",
        "sleep_food": "في أيام النوم الأقصر قد تزيد الرغبة أو الجوع؛ راقب ذلك الأسبوع القادم.",
        "stress_food": "التوتر الأعلى قد يزيد الخيارات السريعة أو الرغبات؛ توقف قصير قبل الأكل قد يساعد.",
        "human_review": "بسبب مخاطر صحية أو أعراض إنذار، يفضل مراجعة التقرير مع مختص.",
        "ed_review": "مع تاريخ اضطراب أكل، يجب تجنب النصائح التقييدية والتركيز الشديد على الوزن.",
        "red_flag": "تم الإبلاغ عن أعراض إنذار؛ يوصى بمتابعة بشرية.",
    },
}


def _t(locale: str, key: str) -> str:
    return _TEXT.get(locale, _TEXT["fa"]).get(key, _TEXT["fa"][key])


def _decode_json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _weekly_craving_patterns(checkins: list[DailyCheckIn]) -> list[str]:
    values = [c.craving_type or c.cravings for c in checkins if c.craving_type or c.cravings]
    if not values:
        return []
    counts = Counter(v.strip() for v in values if v and v.strip())
    return [f"{key} ({count})" for key, count in counts.most_common(3)]


def _weekly_risky_time_windows(checkins: list[DailyCheckIn], meals: list[MealEntry]) -> list[str]:
    windows: Counter[str] = Counter()
    for c in checkins:
        if c.cravings or (c.hunger_level_1_10 is not None and c.hunger_level_1_10 >= 8):
            windows["days_with_cravings_or_high_hunger"] += 1
        if c.stress_level is not None and c.stress_level >= 4:
            windows["high_stress_days"] += 1
        if c.sleep_hours is not None and c.sleep_hours < 6:
            windows["short_sleep_days"] += 1
    for meal in meals:
        meal_time = meal.meal_time or "unknown_meal_time"
        data = _decode_json_dict(meal.analysis_result)
        score = data.get("quality_score")
        if isinstance(score, (int, float)) and score <= 4:
            windows[meal_time] += 1
    return [f"{key}={count}" for key, count in windows.most_common(4)]


def _weekly_risky_meals(meals: list[MealEntry]) -> list[str]:
    risky = []
    for meal in meals:
        data = _decode_json_dict(meal.analysis_result)
        score = data.get("quality_score")
        if isinstance(score, (int, float)) and score <= 4:
            risky.append(meal.meal_time or meal.description[:40])
    return list(dict.fromkeys(risky))[:5]


def _eating_out_pattern(eating_out_count: int, checkins: list[DailyCheckIn], locale: str) -> str | None:
    locations = [c.eating_location for c in checkins if c.eating_location]
    parts = []
    if eating_out_count:
        parts.append(f"planned_eating_out_days={eating_out_count}")
    if locations:
        parts.append("locations: " + ", ".join(f"{k}={v}" for k, v in Counter(locations).most_common(3)))
    return "; ".join(parts) if parts else None


def _adherence_summary(avg_adherence: float | None, adherence_pct: int, locale: str) -> str:
    if avg_adherence is not None:
        return f"avg_adherence={avg_adherence}/5; logging_coverage={adherence_pct}%"
    return f"logging_coverage={adherence_pct}%"


def _meal_quality_summary(meals: list[MealEntry], key: str, locale: str) -> str:
    values = []
    for meal in meals:
        value = _decode_json_dict(meal.analysis_result).get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    if values:
        return " | ".join(values[:3])
    unknown_key = {
        "protein_quality": "protein_unknown",
        "fiber_vegetable_quality": "fiber_unknown",
        "simple_sugar_quality": "sugar_unknown",
    }.get(key, "no_data")
    return _t(locale, unknown_key)


def _hydration_quality(checkins: list[DailyCheckIn], locale: str) -> str:
    notes = [c.adherence_notes.lower() for c in checkins if c.adherence_notes]
    water_mentions = [n for n in notes if "water" in n or "آب" in n or "ماء" in n]
    if water_mentions:
        return "hydration mentioned in adherence notes"
    return _t(locale, "hydration_unknown")


def _sleep_food_relationship(avg_sleep: float | None, craving_patterns: list[str], locale: str) -> str | None:
    if avg_sleep is not None and avg_sleep < 6.5 and craving_patterns:
        return _t(locale, "sleep_food")
    if avg_sleep is not None:
        return f"avg_sleep={avg_sleep}h"
    return None


def _stress_food_relationship(
    avg_stress: float | None,
    craving_patterns: list[str],
    adherence: list[int],
    locale: str,
) -> str | None:
    low_adherence = adherence and (sum(adherence) / len(adherence)) <= 2.5
    if avg_stress is not None and avg_stress >= 4 and (craving_patterns or low_adherence):
        return _t(locale, "stress_food")
    if avg_stress is not None:
        return f"avg_stress={avg_stress}/5"
    return None


def _behavior_pattern_summary(
    craving_patterns: list[str],
    eating_out_pattern: str | None,
    sleep_food_relationship: str | None,
    stress_food_relationship: str | None,
    locale: str,
) -> str:
    parts = []
    if craving_patterns:
        parts.append("cravings: " + ", ".join(craving_patterns))
    if eating_out_pattern:
        parts.append(eating_out_pattern)
    if sleep_food_relationship:
        parts.append(sleep_food_relationship)
    if stress_food_relationship:
        parts.append(stress_food_relationship)
    return "; ".join(parts) if parts else _t(locale, "no_data")


def _three_strengths(
    logging_days: int,
    avg_sleep: float | None,
    avg_stress: float | None,
    total_activity: int,
    craving_patterns: list[str],
    meals: list[MealEntry],
    locale: str,
) -> list[str]:
    strengths = []
    if logging_days >= 3:
        strengths.append(_t(locale, "steady_logging"))
    if total_activity >= 100:
        strengths.append(_t(locale, "activity_strength"))
    if avg_sleep is not None and avg_sleep >= 7:
        strengths.append(_t(locale, "sleep_strength"))
    if avg_stress is not None and avg_stress <= 3:
        strengths.append(_t(locale, "stress_strength"))
    if meals:
        strengths.append(_t(locale, "meal_strength"))
    if craving_patterns:
        strengths.append(_t(locale, "craving_strength"))
    fallback = [
        _t(locale, "steady_logging"),
        _t(locale, "meal_strength"),
        _t(locale, "activity_strength"),
    ]
    for item in fallback:
        if item not in strengths:
            strengths.append(item)
        if len(strengths) >= 3:
            break
    return strengths[:3]


def _two_small_adjustments(
    avg_sleep: float | None,
    avg_stress: float | None,
    avg_hunger_10: float | None,
    avg_hunger: float | None,
    eating_out_count: int,
    protein_quality: str,
    fiber_quality: str,
    simple_sugar_quality: str,
    locale: str,
) -> list[str]:
    text = {
        "sleep": {
            "fa": "۳۰ دقیقه زودتر آماده خواب شوید.",
            "en": "Start your wind-down 30 minutes earlier.",
            "ar": "ابدأ الاستعداد للنوم قبل 30 دقيقة.",
        },
        "stress": {
            "fa": "قبل از میان‌وعده‌های استرسی، دو دقیقه مکث و نفس عمیق اضافه کنید.",
            "en": "Add a two-minute pause before stress snacks.",
            "ar": "أضف توقفاً قصيراً لدقيقتين قبل وجبات التوتر الخفيفة.",
        },
        "hunger": {
            "fa": "در وعده قبلی یک منبع پروتئین یا فیبر کوچک اضافه کنید.",
            "en": "Add one small protein or fiber source to the previous meal.",
            "ar": "أضف مصدراً صغيراً للبروتين أو الألياف في الوجبة السابقة.",
        },
        "out": {
            "fa": "برای غذای بیرون، اول پروتئین و سالاد/سبزی را مشخص کنید.",
            "en": "For eating out, choose protein and salad/vegetables first.",
            "ar": "عند الأكل خارج المنزل، اختر البروتين والخضار أولاً.",
        },
        "protein": {
            "fa": "حداقل یک وعده را برای ارزیابی پروتئین ثبت کنید.",
            "en": "Log at least one meal so protein quality can be assessed.",
            "ar": "سجل وجبة واحدة على الأقل لتقييم جودة البروتين.",
        },
        "fiber": {
            "fa": "کنار یک وعده روزانه یک سهم سبزی یا حبوبات اضافه کنید.",
            "en": "Add one serving of vegetables or legumes to one daily meal.",
            "ar": "أضف حصة خضار أو بقوليات إلى وجبة يومية واحدة.",
        },
        "sugar": {
            "fa": "شیرینی را کنار وعده متعادل‌تر و با مقدار مشخص نگه دارید.",
            "en": "Keep sweets portioned and paired with a balanced meal.",
            "ar": "اجعل الحلويات بكمية محددة ومع وجبة متوازنة.",
        },
        "same": {
            "fa": "همین روند را با ثبت منظم‌تر ادامه دهید.",
            "en": "Continue the same pattern with steadier logging.",
            "ar": "استمر على نفس المسار مع تسجيل أكثر انتظاماً.",
        },
        "water": {
            "fa": "یک لیوان آب بیشتر در بخش ثابت روز اضافه کنید.",
            "en": "Add one extra glass of water at a consistent time.",
            "ar": "أضف كوب ماء إضافياً في وقت ثابت من اليوم.",
        },
    }
    lang = locale if locale in {"fa", "en", "ar"} else "fa"
    adjustments: list[str] = []
    if avg_sleep is not None and avg_sleep < 6.5:
        adjustments.append(text["sleep"][lang])
    if avg_stress is not None and avg_stress >= 4:
        adjustments.append(text["stress"][lang])
    if (avg_hunger_10 is not None and avg_hunger_10 >= 7) or (avg_hunger is not None and avg_hunger >= 4):
        adjustments.append(text["hunger"][lang])
    if eating_out_count:
        adjustments.append(text["out"][lang])
    if "unknown" in protein_quality.lower() or "لازم" in protein_quality:
        adjustments.append(text["protein"][lang])
    if "unknown" in fiber_quality.lower() or "لازم" in fiber_quality:
        adjustments.append(text["fiber"][lang])
    if "unknown" not in simple_sugar_quality.lower() and simple_sugar_quality:
        adjustments.append(text["sugar"][lang])
    fallback = [text["same"][lang], text["water"][lang]]
    for item in fallback:
        if item not in adjustments:
            adjustments.append(item)
        if len(adjustments) >= 2:
            break
    return adjustments[:2]


def _next_week_small_goal(adjustments: list[str], logging_days: int, locale: str) -> str:
    if logging_days < 5:
        goals = {
            "fa": "هفته بعد حداقل ۵ چک‌این کوتاه ثبت کنید.",
            "en": "Log at least 5 short check-ins next week.",
            "ar": "سجل 5 متابعات قصيرة على الأقل في الأسبوع القادم.",
        }
        return goals.get(locale, goals["fa"])
    return adjustments[0]


def _monitoring_notes(data: DataCompleteness, red_flag_count: int, locale: str) -> str:
    parts = [f"checkins={data.checkin_days}/7", f"meals={data.meal_entries}"]
    if data.waist_points:
        parts.append(f"waist_points={data.waist_points}")
    if red_flag_count:
        parts.append(f"red_flag_symptom_days={red_flag_count}")
    return "; ".join(parts)


def _weekly_summary(logging_days: int, confidence_level: str, behavior_pattern_summary: str, locale: str) -> str:
    prefix = _t(locale, "summary") if logging_days >= 3 else _t(locale, "summary_empty")
    return f"{prefix} confidence={confidence_level}; {behavior_pattern_summary}"


def _weekly_safety_notes(
    *,
    risk_level: str,
    active_medical_flags: list[str],
    red_flag_count: int,
    locale: str,
) -> list[str]:
    notes = []
    if risk_level in {"high", "clinical_review_required"}:
        notes.append(_t(locale, "human_review"))
    if "eating_disorder_history" in active_medical_flags:
        notes.append(_t(locale, "ed_review"))
    if red_flag_count:
        notes.append(_t(locale, "red_flag"))
    return list(dict.fromkeys(notes))


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
