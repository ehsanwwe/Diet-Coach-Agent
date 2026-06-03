# Phase 9: Progress & Reports — Research

**Researched:** 2026-06-03
**Domain:** Behavior-centric progress tracking — daily check-in API, progress summary, weekly report generation, sparkline chart rendering, behavior-wins dashboard
**Confidence:** HIGH (all findings grounded in existing codebase + verified library docs)

---

## Summary

Phase 9 builds on a fully operational backend (Phases 1–8) with three existing ORM models already defined — `DailyCheckIn`, `ProgressEntry`, and `WeeklyReport` in `backend/app/models/progress.py`. No new data models are needed; this phase is exclusively about wiring the repository layer, service layer, three endpoints, one frontend screen, and dictionary keys.

The backend follows a strict pattern visible in Phases 7–8: raw Pydantic model returns on nutrition-like endpoints, `SuccessResponse[T]` wrapper on chat-like endpoints. For the progress endpoints (check-in submission, summary retrieval, weekly report), the raw-model pattern matches the nutrition service style more closely — no `SuccessResponse` wrapper needed. The service layer (a new `progress_service.py`) should mirror the shape of `nutrition_service.py`: pure functions that accept `(db: Session, user: User)`, returning typed Pydantic response objects.

The frontend needs one new route (`/[lang]/progress/page.tsx`), three new library functions in `src/lib/progress.ts`, three new types in `src/types/progress.ts`, and new dictionary keys in the `progress` namespace added to `fa.ts`/`en.ts`/`ar.ts`. The sparkline chart is the only visually novel element — it must be rendered without an external charting library. The existing project has no chart dependency (`package.json` confirms: no recharts, no chart.js, no d3). An inline SVG path calculation from an array of weight readings is the correct approach (< 30 lines of code, zero dependencies).

**Primary recommendation:** Implement the three progress endpoints as raw Pydantic model returns (matching nutrition endpoint style), use inline SVG sparklines on the frontend, and keep the weekly report generation as a pure Python aggregation function inside `progress_service.py` — no AI call needed for the report. The `WeeklyReport.report_data` JSON field stores the serialized report payload.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROG-01 | User can submit daily check-in: weight, hunger, sleep duration, stress level, activity, adherence notes (`POST /api/v1/progress/check-in`) | `DailyCheckIn` model already has all required columns; needs repository upsert (one record per user per day) + service + endpoint |
| PROG-02 | Progress summary (recent check-ins, trends) is retrievable (`GET /api/v1/progress/summary`) | Requires `progress_repository.get_recent_checkins()` + service aggregation computing 7-day trends; response shape designed here |
| PROG-03 | Weekly report generated with: weight trend, adherence trend, hunger pattern, sleep/stress relation, food quality, suggested next-week focus (`GET /api/v1/progress/weekly-report`) | `WeeklyReport` model stores serialized JSON; service generates report on-demand (or returns cached); pure Python aggregation, no AI call required |
| PROG-04 | Progress dashboard shows behavior wins — not only weight (protein, fiber, water, sleep, movement, logging consistency) | Frontend dashboard layout decision; backend summary endpoint must expose logging streak + recent trends; behavior_wins computed from check-in history |
| PROG-05 | Weight trend shown as sparkline or simple chart (not just a number) | Inline SVG approach: compute min/max/path from `weight_kg[]` array; no charting library; 20–30 lines of TypeScript math |
| UI-12 | Progress and weekly report screen | Single route `/[lang]/progress/page.tsx`; authenticated; empty state when no check-ins; tab or section switch between summary + weekly report |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

- **Database**: SQLite only — sync SQLAlchemy 2.x with `select()` + `session.execute()`
- **Response style**: Raw Pydantic model on nutrition-style endpoints (no `SuccessResponse` wrapper). `SuccessResponse[T]` used on chat-style endpoints. Progress endpoints follow nutrition style.
- **ORM patterns**: `lazy="raise"` on all relationships; `render_as_batch=True` in Alembic. No new migrations needed (progress models already migrated).
- **Frontend**: Next.js 16 App Router, TypeScript strict mode (`strict: true`), no `any` types
- **Styling**: Tailwind v4 CSS logical properties only — `ps-`, `pe-`, `ms-`, `me-`; never `pl-`, `pr-`, `ml-`, `mr-`
- **i18n**: All UI strings from dictionaries (`fa.ts` shape defines `Dictionary` interface); no hard-coded text in components
- **Charts/audio**: No external charting library; use inline SVG or native browser APIs
- **AI**: Progress report generation must NOT call AI — pure aggregation. The `NutritionAgentService` is already used by nutrition endpoints; progress endpoints are independent.
- **Continuation files**: After every meaningful commit: update `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md`

---

## Standard Stack

### Core (already installed — no new dependencies needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | API routing | Already installed; progress router added to `router.py` |
| SQLAlchemy 2.x | 2.0+ | ORM / queries | All repositories use `select()` + `session.execute()` |
| Pydantic v2 | 2.0+ | Response schemas | `model_config = ConfigDict(from_attributes=True)` for ORM model deserialization |
| Next.js 16 | 16.x | Frontend routing | `app/[lang]/progress/page.tsx` pattern already established |
| Tailwind CSS v4 | 4.x | Styling | Logical property classes (`ps-`, `pe-`, etc.) already in use |
| TypeScript 5.x | 5.x | Type safety | Strict mode; all new types in `src/types/progress.ts` |

### Supporting (already installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `framer-motion` | 12.x | Card enter animation | Use for check-in form step feel, consistent with onboarding pattern |
| `lucide-react` | 1.x | Icons | Use for check-in form icons (scale, moon, activity, etc.) |
| `clsx` + `tailwind-merge` | present | Conditional classes | `cn()` utility already established in `src/lib/cn.ts` |

### No New Dependencies

The sparkline is the only visual element that might tempt an external library. Recharts, Chart.js, and Nivo are NOT needed — the sparkline is a single SVG path over 7–14 data points, achievable in ~25 lines of TypeScript. Adding a charting library would add 300–800 KB to the bundle for a single small visualization.

**No `npm install` required for this phase.**

---

## Architecture Patterns

### Recommended Project Structure (new files only)

```
backend/app/
├── api/v1/endpoints/
│   └── progress.py          # NEW — 3 endpoints
├── repositories/
│   └── progress_repository.py  # NEW — DB queries for DailyCheckIn, WeeklyReport
├── schemas/
│   └── progress.py          # NEW — request/response Pydantic models
├── services/
│   └── progress_service.py  # NEW — business logic, aggregation

frontend/src/
├── app/[lang]/progress/
│   └── page.tsx             # NEW — authenticated progress screen
├── components/progress/
│   ├── CheckInForm.tsx       # NEW — daily check-in input form
│   ├── ProgressSummary.tsx   # NEW — behavior wins + sparkline
│   ├── WeeklyReport.tsx      # NEW — weekly report card
│   └── WeightSparkline.tsx   # NEW — inline SVG sparkline component
├── lib/
│   └── progress.ts          # NEW — API client functions (3 functions)
├── types/
│   └── progress.ts          # NEW — TypeScript types for API shapes
└── dictionaries/
    ├── fa.ts                 # MODIFIED — add `progress` namespace
    ├── en.ts                 # MODIFIED — add `progress` namespace
    └── ar.ts                 # MODIFIED — add `progress` namespace
```

### Pattern 1: Progress Repository

```python
# backend/app/repositories/progress_repository.py
# Follows the same pattern as nutrition_repository.py — functions, not a class

from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.progress import DailyCheckIn, WeeklyReport
import json

def upsert_checkin(db: Session, user_id: str, *, check_date, **fields) -> DailyCheckIn:
    result = db.execute(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user_id, DailyCheckIn.check_date == check_date)
    )
    checkin = result.scalar_one_or_none()
    if checkin is None:
        checkin = DailyCheckIn(user_id=user_id, check_date=check_date)
        db.add(checkin)
    for key, val in fields.items():
        setattr(checkin, key, val)
    db.flush()
    return checkin

def get_recent_checkins(db: Session, user_id: str, days: int = 14) -> list[DailyCheckIn]:
    result = db.execute(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user_id)
        .order_by(desc(DailyCheckIn.check_date))
        .limit(days)
    )
    return list(result.scalars().all())

def get_or_create_weekly_report(db: Session, user_id: str, week_start, week_end) -> WeeklyReport | None:
    result = db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user_id, WeeklyReport.week_start == week_start)
        .order_by(desc(WeeklyReport.generated_at))
        .limit(1)
    )
    return result.scalar_one_or_none()

def save_weekly_report(db: Session, user_id: str, *, week_start, week_end, report_data: dict) -> WeeklyReport:
    from datetime import datetime, timezone
    existing = get_or_create_weekly_report(db, user_id, week_start, week_end)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if existing is None:
        existing = WeeklyReport(user_id=user_id, week_start=week_start, week_end=week_end)
        db.add(existing)
    existing.report_data = json.dumps(report_data, ensure_ascii=False)
    existing.generated_at = now
    db.flush()
    return existing
```

### Pattern 2: Progress Service — Aggregation Logic

The weekly report is a pure Python aggregation. No AI call. Computed from the last 7 `DailyCheckIn` records:

```python
# backend/app/services/progress_service.py
# Key aggregation function for weekly report

def _compute_weekly_report(checkins: list) -> dict:
    if not checkins:
        return {"empty": True, "message": "هنوز داده‌ای برای گزارش وجود ندارد."}

    weights = [c.weight_kg for c in checkins if c.weight_kg is not None]
    hungers = [c.hunger_level for c in checkins if c.hunger_level is not None]
    sleeps = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
    stresses = [c.stress_level for c in checkins if c.stress_level is not None]
    activities = [c.activity_minutes for c in checkins if c.activity_minutes is not None]

    weight_trend = None
    if len(weights) >= 2:
        delta = weights[-1] - weights[0]  # positive = gained, negative = lost
        weight_trend = {"first": weights[0], "last": weights[-1], "delta": round(delta, 2)}

    avg_hunger = round(sum(hungers) / len(hungers), 1) if hungers else None
    avg_sleep = round(sum(sleeps) / len(sleeps), 1) if sleeps else None
    avg_stress = round(sum(stresses) / len(stresses), 1) if stresses else None
    total_activity = sum(activities)
    logging_days = len(checkins)

    # Sleep/stress correlation flag
    sleep_stress_note = None
    if avg_sleep is not None and avg_stress is not None:
        if avg_sleep < 6 and avg_stress > 3:
            sleep_stress_note = "خواب کم و استرس بالا — بهبود خواب اولویت هفته بعد باشد."

    # Suggested next-week focus (rule-based)
    focus = _suggest_focus(avg_hunger, avg_sleep, avg_stress, total_activity, logging_days)

    return {
        "weight_trend": weight_trend,
        "weight_series": weights,  # for sparkline
        "avg_hunger": avg_hunger,
        "avg_sleep": avg_sleep,
        "avg_stress": avg_stress,
        "total_activity_minutes": total_activity,
        "logging_days": logging_days,
        "adherence_pct": round(logging_days / 7 * 100),
        "sleep_stress_note": sleep_stress_note,
        "suggested_focus": focus,
    }

def _suggest_focus(avg_hunger, avg_sleep, avg_stress, total_activity, logging_days) -> str:
    """Rule-based focus suggestion — no AI call."""
    if logging_days < 3:
        return "ثبت روزانه را منظم‌تر کنید — داده بیشتر، راهنمایی بهتر."
    if avg_sleep and avg_sleep < 6.5:
        return "بهبود کیفیت خواب اولویت اصلی: هدف ۷–۸ ساعت خواب شبانه."
    if avg_stress and avg_stress >= 4:
        return "مدیریت استرس: تنفس عمیق یا پیاده‌روی کوتاه بعد از ناهار."
    if total_activity < 100:
        return "افزایش تحرک: ۳۰ دقیقه پیاده‌روی روزانه شروع خوبی است."
    if avg_hunger and avg_hunger > 3:
        return "تنظیم وعده‌ها برای کاهش گرسنگی: وعده‌های کوچک‌تر و مکرر."
    return "ادامه مسیر فعلی — روند شما مثبت است!"
```

### Pattern 3: Endpoint Pattern (matches nutrition style)

```python
# backend/app/api/v1/endpoints/progress.py
# Raw Pydantic model returns — no SuccessResponse wrapper (matches nutrition.py)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.progress import CheckInRequest, CheckInResponse, ProgressSummaryResponse, WeeklyReportResponse
from app.services import progress_service

router = APIRouter(tags=["progress"])

@router.post("/check-in", response_model=CheckInResponse, status_code=201)
def submit_check_in(
    body: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CheckInResponse:
    try:
        return progress_service.submit_check_in(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Check-in failed: {exc}", status_code=500)

@router.get("/summary", response_model=ProgressSummaryResponse)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> ProgressSummaryResponse:
    try:
        return progress_service.get_summary(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Summary failed: {exc}", status_code=500)

@router.get("/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> WeeklyReportResponse:
    try:
        return progress_service.get_weekly_report(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Weekly report failed: {exc}", status_code=500)
```

### Pattern 4: Pydantic Schemas for Progress

```python
# backend/app/schemas/progress.py
# All fields optional except check_date to support partial check-ins

from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class CheckInRequest(BaseModel):
    check_date: date
    weight_kg: float | None = Field(None, ge=20, le=300)
    hunger_level: int | None = Field(None, ge=1, le=5)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    stress_level: int | None = Field(None, ge=1, le=5)
    activity_minutes: int | None = Field(None, ge=0, le=1440)
    adherence_notes: str | None = None

class CheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    check_date: date
    weight_kg: float | None
    hunger_level: int | None
    sleep_hours: float | None
    stress_level: int | None
    activity_minutes: int | None
    adherence_notes: str | None
    created_at: datetime

class BehaviorWin(BaseModel):
    label: str          # Persian label e.g. "خواب منظم"
    achieved: bool
    value: str | None   # e.g. "7.2 ساعت"

class ProgressSummaryResponse(BaseModel):
    has_data: bool
    recent_checkins: list[CheckInResponse]
    weight_series: list[float]      # ordered oldest-to-newest for sparkline
    latest_weight_kg: float | None
    behavior_wins: list[BehaviorWin]
    logging_streak: int             # consecutive days with check-ins
    empty_state_message: str | None

class WeeklyReportData(BaseModel):
    weight_trend: dict | None       # {first, last, delta}
    weight_series: list[float]      # for sparkline
    avg_hunger: float | None
    avg_sleep: float | None
    avg_stress: float | None
    total_activity_minutes: int
    logging_days: int
    adherence_pct: int
    sleep_stress_note: str | None
    suggested_focus: str

class WeeklyReportResponse(BaseModel):
    has_report: bool
    week_start: date | None
    week_end: date | None
    report: WeeklyReportData | None
    empty_state_message: str | None
```

### Pattern 5: Sparkline SVG (Frontend — No Library)

```typescript
// src/components/progress/WeightSparkline.tsx
// Inline SVG path from weight_series array — zero dependencies

interface Props {
  weights: number[]
  width?: number
  height?: number
}

export function WeightSparkline({ weights, width = 120, height = 40 }: Props) {
  if (weights.length < 2) return null

  const min = Math.min(...weights)
  const max = Math.max(...weights)
  const range = max - min || 1

  const points = weights.map((w, i) => {
    const x = (i / (weights.length - 1)) * width
    const y = height - ((w - min) / range) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const d = `M ${points.join(' L ')}`

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <path d={d} fill="none" stroke="var(--color-brand)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
```

### Pattern 6: Dictionary Namespace Addition

The `Dictionary` interface in `fa.ts` must receive a new `progress` key. All three dictionary files must be updated consistently:

```typescript
// Addition to Dictionary interface in fa.ts
progress: {
  // Page title
  title: string
  subtitle: string
  // Tab labels
  tabSummary: string
  tabWeekly: string
  // Check-in form
  checkInTitle: string
  checkInSubtitle: string
  checkInDate: string
  checkInWeight: string
  checkInWeightUnit: string
  checkInHunger: string
  checkInSleep: string
  checkInSleepUnit: string
  checkInStress: string
  checkInActivity: string
  checkInActivityUnit: string
  checkInNotes: string
  checkInNotesPlaceholder: string
  checkInSubmit: string
  checkInSubmitting: string
  checkInSuccess: string
  checkInAlreadyToday: string
  // Summary
  summaryTitle: string
  latestWeight: string
  weightTrend: string
  behaviourWinsTitle: string
  loggingStreak: string
  loggingStreakDays: string
  // Behavior win labels
  winSleep: string
  winActivity: string
  winLogging: string
  winHydration: string
  winLowStress: string
  winLowHunger: string
  // Weekly report
  weeklyTitle: string
  weeklyPeriod: string
  weeklyAdherence: string
  weeklyAvgSleep: string
  weeklyAvgStress: string
  weeklyAvgHunger: string
  weeklyTotalActivity: string
  weeklyWeightDelta: string
  weeklySleepStressNote: string
  weeklyFocusTitle: string
  weeklyFocus: string
  weeklyLoggingDays: string
  // Empty states
  emptyTitle: string
  emptyDesc: string
  emptyCheckinCta: string
  emptyWeeklyTitle: string
  emptyWeeklyDesc: string
  // Errors
  errSubmitFailed: string
  errLoadFailed: string
  // Units
  unitKg: string
  unitHours: string
  unitMinutes: string
  unitPercent: string
}
```

### Pattern 7: Frontend Page Structure

```typescript
// src/app/[lang]/progress/page.tsx — matches the exact shape of dashboard/page.tsx

import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import ProgressScreen from '@/components/progress/ProgressScreen'

type Props = { params: Promise<{ lang: string }> }

export default async function ProgressPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)
  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <ProgressScreen dict={dict} locale={locale} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
```

### Anti-Patterns to Avoid

- **Rechart/Chart.js import**: The sparkline is 25 lines of SVG math. Never add a charting library for a 7-point line chart.
- **AI call inside weekly report**: The weekly report is rule-based aggregation. Calling `NutritionAgentService` here adds latency, cost, and a failure mode. The `suggested_focus` string is computed by `_suggest_focus()` — a deterministic function.
- **Upsert vs. insert on check-in**: The `upsert_checkin()` pattern is correct — if a user submits twice on the same day, update the existing record. Do not reject or create duplicates.
- **`check_date` as string**: The `DailyCheckIn.check_date` is a SQLAlchemy `Date` column. In Pydantic, map it as `date` (not `str`). FastAPI handles ISO-8601 parsing automatically.
- **`lazy="raise"` trap**: The `DailyCheckIn.user` relationship uses `lazy="raise"`. Never access `checkin.user` in a service function — it will raise `MissingGreenlet`. Always query by `user_id` directly.
- **SuccessResponse wrapper confusion**: Nutrition endpoints return raw Pydantic models. Chat endpoints return `SuccessResponse[T]`. Progress endpoints follow the nutrition pattern — raw models. Do not wrap in `SuccessResponse`.
- **Physical Tailwind classes**: `pl-`, `pr-`, `ml-`, `mr-` are forbidden. Use `ps-`, `pe-`, `ms-`, `me-` exclusively.
- **`any` TypeScript type**: The `WeeklyReportData.weight_trend` field is typed as `dict` on the backend. On the frontend, define a `WeightTrend` interface with `{ first: number; last: number; delta: number }` rather than using `Record<string, unknown>`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SVG sparkline | React charting library (recharts, chart.js) | Inline SVG `<path>` calculation | Libraries add 300–800 KB for a 7-point line. 25 lines of math is sufficient. |
| Trend computation | External statistics library | Simple Python arithmetic | Min/max/average/delta requires no dependency. Python's built-in `statistics` module (no install) handles edge cases. |
| Week boundary calculation | Custom calendar logic | Python `datetime` + `timedelta` | `date.today() - timedelta(days=date.today().weekday())` gives Monday of current week correctly. |
| Input validation (ranges) | Manual if/else range checks | Pydantic `Field(ge=..., le=...)` | Already used by all schemas in the codebase — hunger 1–5, stress 1–5, weight 20–300 kg, sleep 0–24 hours. |
| Auth guard | New auth component | `AuthGuard` (`src/components/auth/AuthGuard.tsx`) | Already implemented and tested across all post-auth screens. |

**Key insight:** This phase is data plumbing + one SVG component. The only genuinely novel element is the sparkline; everything else follows patterns already established in Phases 7 and 8.

---

## Common Pitfalls

### Pitfall 1: `lazy="raise"` on `DailyCheckIn.user`
**What goes wrong:** Code accesses `checkin.user.name` or any attribute through the relationship, raising `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called`.
**Why it happens:** All ORM relationships use `lazy="raise"` per BE-04. Relationship traversal is forbidden outside an explicit `.options(joinedload(...))` query.
**How to avoid:** Never access `checkin.user` in service code. The user is already passed as a parameter. Use `user_id` for foreign key values.
**Warning signs:** Any attribute access via a `.` chain across a relationship boundary in service code.

### Pitfall 2: One check-in per user per day — not enforced at DB level
**What goes wrong:** A user submits the check-in form twice on the same day, creating two records. The sparkline then shows incorrect weight data points.
**Why it happens:** There is no UNIQUE constraint on `(user_id, check_date)` in the current `DailyCheckIn` model. The ROADMAP comment says "One record per user per day is enforced at app layer."
**How to avoid:** `upsert_checkin()` must query for an existing record before inserting. The repository function must be `upsert`, not `insert`.
**Warning signs:** Multiple rows with the same `user_id` + `check_date` appearing in the DB.

### Pitfall 3: `check_date` timezone confusion
**What goes wrong:** A user submits at 11 PM local time; the server interprets it as the next UTC day. Progress streak breaks.
**Why it happens:** `datetime.utcnow().date()` returns UTC date. If the user is in UTC+3:30 (Iran timezone), submitting at 11:30 PM local = 8 PM UTC = same date. But submitting at 11:30 PM local = next UTC date at e.g. UTC+12 timezones.
**How to avoid:** Accept `check_date` as a client-provided `date` field in the request body (already specified in `CheckInRequest`). The client knows the user's local date. Never derive `check_date` from `datetime.utcnow()` on the server.
**Warning signs:** Users complaining they can't check in "for today."

### Pitfall 4: Empty `weight_series` causing sparkline divide-by-zero
**What goes wrong:** `WeightSparkline` receives `weights = []` or `weights = [75]` (single point). The range calculation `max - min = 0` causes division by zero or renders a flat line with NaN coordinates.
**Why it happens:** New users have few check-ins; not all check-ins include weight.
**How to avoid:** Guard in both the service (`weight_series` only includes non-null values) and in the `WeightSparkline` component (`if (weights.length < 2) return null`). The `range = max - min || 1` fallback handles zero-range.
**Warning signs:** NaN in SVG `d` attribute; browser console warnings about invalid SVG path data.

### Pitfall 5: Bottom nav `progress` tab still `disabled: true`
**What goes wrong:** The progress screen is built but the nav tab remains disabled (`disabled: true` in `AppBottomNav.tsx`). Users can't navigate to it from the bottom nav.
**Why it happens:** `AppBottomNav.tsx` hardcodes `disabled: true` for the progress tab (confirmed in the source at line 72). This was a placeholder pending Phase 9.
**How to avoid:** In the plan, explicitly include a task to update `AppBottomNav.tsx` — remove `disabled: true`, set `active: isActive('progress')` for the progress tab entry.
**Warning signs:** Clicking the progress nav item does nothing.

### Pitfall 6: Dictionary interface not updated in all three files
**What goes wrong:** `fa.ts` gets the new `progress` keys but `en.ts` and `ar.ts` are not updated. TypeScript strict mode raises a type error because `Dictionary` interface is defined once (in `fa.ts`) and all files must implement it.
**Why it happens:** Three files to update; easy to forget two.
**How to avoid:** The plan must include a single task that updates all three dictionary files simultaneously. Run `npm run type-check` to catch the error.
**Warning signs:** TypeScript error: `Property 'progress' is missing in type...`

---

## Code Examples

### Verified Pattern: SQLAlchemy 2.x query with date ordering

All existing repositories in the codebase use this exact pattern. From `nutrition_repository.py`:

```python
# Source: backend/app/repositories/nutrition_repository.py (existing codebase)
result = db.execute(
    select(NutritionPlan)
    .where(NutritionPlan.user_id == user_id, NutritionPlan.status == "active")
    .order_by(NutritionPlan.created_at.desc())
    .limit(1)
)
return result.scalar_one_or_none()
```

Apply the same pattern for `DailyCheckIn`:

```python
result = db.execute(
    select(DailyCheckIn)
    .where(DailyCheckIn.user_id == user_id)
    .order_by(desc(DailyCheckIn.check_date))
    .limit(14)
)
return list(result.scalars().all())
```

### Verified Pattern: Upsert via query-then-set

From `nutrition_repository.py`'s `upsert_nutrition_goal`:

```python
# Source: backend/app/repositories/nutrition_repository.py (existing codebase)
goal = get_nutrition_goal(db, user_id)
if goal is None:
    goal = NutritionGoal(user_id=user_id)
    db.add(goal)
goal.goal_type = goal_type
db.flush()
return goal
```

### Verified Pattern: JSON serialization for report_data field

`WeeklyReport.report_data` is a `Text` column storing JSON. Pattern mirrors `NutritionPlan.plan_metadata`:

```python
# Source: backend/app/repositories/nutrition_repository.py (existing codebase)
plan.plan_metadata = json.dumps(plan_metadata, ensure_ascii=False) if plan_metadata else None
# Reading:
return json.loads(plan.plan_metadata)
```

### Verified Pattern: Frontend lib client pattern

Matches existing `src/lib/nutrition.ts` style:

```typescript
// src/lib/progress.ts — mirrors lib/nutrition.ts exactly
import { getToken } from './storage'
import type { CheckInRequest, CheckInResponse, ProgressSummaryResponse, WeeklyReportResponse } from '@/types/progress'

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const BASE = '/api/v1/progress'

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) throw new Error('UNAUTHORIZED')
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Request failed')
  }
  return res.json() as Promise<T>
}

export async function submitCheckIn(body: CheckInRequest): Promise<CheckInResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/check-in`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  return handleResponse<CheckInResponse>(res)
}

export async function getProgressSummary(): Promise<ProgressSummaryResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/summary`, { headers: { ...authHeaders() } })
  return handleResponse<ProgressSummaryResponse>(res)
}

export async function getWeeklyReport(): Promise<WeeklyReportResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/weekly-report`, { headers: { ...authHeaders() } })
  return handleResponse<WeeklyReportResponse>(res)
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `session.query(Model).filter_by(...)` | `select(Model).where(...)` + `session.execute()` | SQLAlchemy 2.0 (2023) | v1 style forbidden; all repos use v2 style |
| Tailwind `pl-4 pr-4` | Tailwind v4 `ps-4 pe-4` (logical) | Tailwind v4 (2025) | RTL automatic; physical classes produce wrong layout in RTL |
| Pydantic `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` | Pydantic v2 (2023) | v1 patterns removed; must use v2 ConfigDict |
| Charting library for sparklines | Inline SVG path calculation | Always the right approach for small data | Bundle size; this project has no charting library installed |

**Deprecated/outdated in this project:**
- `session.query()` ORM style: forbidden per BE-02, INFRA SQLAlchemy 2.x mandate
- `class Config:` in Pydantic models: all models use `model_config = ConfigDict()`
- `validator` decorator: replaced by `@field_validator` in Pydantic v2

---

## Open Questions

1. **Should the weekly report be cached after generation?**
   - What we know: `WeeklyReport` model has `generated_at` timestamp; `save_weekly_report()` can update an existing record.
   - What's unclear: Whether to re-generate on every `GET /weekly-report` call or cache until the week ends.
   - Recommendation: Re-generate on every call for simplicity (no stale report issue). If the last 7 check-ins haven't changed since last generation, the output will be identical. SQLite is fast enough for this aggregation.

2. **What counts as a "behavior win" on the summary screen (PROG-04)?**
   - What we know: The requirement says "protein, fiber, water, sleep, movement, logging consistency." The `DailyCheckIn` model has `sleep_hours` and `activity_minutes` but no protein/fiber/water fields.
   - What's unclear: Protein, fiber, and water targets come from the nutrition plan guidelines, not from check-ins. Cross-referencing daily targets would require reading `NutritionPlan` metadata.
   - Recommendation: For Phase 9, compute behavior wins from available check-in data only: sleep (threshold ≥ 7h = win), activity (threshold ≥ 30min = win), logging_streak (≥ 3 days = win), low_stress (≤ 2 = win), low_hunger (≤ 2 = win). Protein/fiber/water wins require meal tracking data not yet available in v1 — skip them or show as "not yet tracked." Document this decision.

3. **Should `check_date` default to today if not provided?**
   - What we know: The client knows the user's local date. The server only knows UTC.
   - Recommendation: Make `check_date` required in `CheckInRequest` (not optional with server-side default). This avoids timezone issues entirely. Client sends today's local date as ISO-8601.

---

## Environment Availability

Step 2.6: SKIPPED — This phase makes no external dependencies beyond the existing project stack (Python 3.12, FastAPI, SQLAlchemy, Node.js, Next.js). All required tools are already verified as installed and operational in prior phases.

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.23.x |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd backend && python -m pytest tests/test_progress.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROG-01 | POST /progress/check-in creates DailyCheckIn record | unit (service) | `pytest tests/test_progress.py::test_submit_check_in -x` | Wave 0 |
| PROG-01 | Submitting twice on same day updates, not duplicates | unit (service) | `pytest tests/test_progress.py::test_checkin_upsert -x` | Wave 0 |
| PROG-02 | GET /progress/summary returns weight_series + behavior_wins | unit (service) | `pytest tests/test_progress.py::test_progress_summary -x` | Wave 0 |
| PROG-03 | GET /progress/weekly-report with 7 check-ins returns report | unit (service) | `pytest tests/test_progress.py::test_weekly_report -x` | Wave 0 |
| PROG-03 | GET /progress/weekly-report with 0 check-ins returns empty state | unit (service) | `pytest tests/test_progress.py::test_weekly_report_empty -x` | Wave 0 |
| PROG-04 | behavior_wins list contains sleep/activity/logging entries | unit (service) | `pytest tests/test_progress.py::test_behavior_wins -x` | Wave 0 |
| PROG-05 | weight_series in summary contains only non-null weights | unit (service) | `pytest tests/test_progress.py::test_weight_series_no_nulls -x` | Wave 0 |
| UI-12 | Bottom nav progress tab enabled and routes to /progress | manual / visual | — | manual |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_progress.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_progress.py` — covers PROG-01 through PROG-05
- [ ] `backend/tests/conftest.py` — likely needed; check if already exists (not seen in codebase scan)

*(Check `backend/tests/` before Wave 0 — no tests directory exists yet; conftest.py will need to be created)*

---

## Sources

### Primary (HIGH confidence)
- Existing codebase — `backend/app/models/progress.py` — DailyCheckIn, ProgressEntry, WeeklyReport models verified
- Existing codebase — `backend/app/repositories/nutrition_repository.py` — upsert pattern, SQLAlchemy 2.x style confirmed
- Existing codebase — `backend/app/api/v1/endpoints/nutrition.py` + `chat.py` — response pattern (raw vs. SuccessResponse) confirmed
- Existing codebase — `frontend/src/dictionaries/fa.ts` — Dictionary interface shape and existing namespaces confirmed
- Existing codebase — `frontend/src/components/layout/AppBottomNav.tsx` — progress tab `disabled: true` confirmed at line 72
- Existing codebase — `frontend/src/lib/nutrition.ts` — frontend lib client pattern confirmed
- `.planning/REQUIREMENTS.md` — PROG-01 through PROG-05 and UI-12 requirements verbatim

### Secondary (MEDIUM confidence)
- Tailwind CSS v4 logical properties — confirmed via `frontend/src/app/globals.css` (project already uses `ps-`, `pe-`)
- Python `datetime`/`timedelta` for week boundary calculation — standard library, no external source needed
- SVG path construction for sparklines — W3C SVG specification, widely documented

### Tertiary (LOW confidence)
- None — all findings are grounded in codebase inspection or standard Python/TypeScript practices

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — entire stack verified from existing installed packages and codebase
- Architecture: HIGH — patterns copied from Phases 7–8 existing code
- Pitfalls: HIGH — lazy="raise" trap and upsert trap verified directly in model and repository source
- Sparkline approach: HIGH — package.json confirms no charting library; SVG math is trivial

**Research date:** 2026-06-03
**Valid until:** 2026-07-03 (stable stack; no fast-moving dependencies)
