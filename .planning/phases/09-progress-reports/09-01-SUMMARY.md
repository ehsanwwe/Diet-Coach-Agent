---
phase: 09-progress-reports
plan: "01"
subsystem: backend
tags: [progress, check-in, weekly-report, behavior-wins, pytest, fastapi, sqlalchemy]
dependency_graph:
  requires: [backend/app/models/progress.py, backend/app/api/dependencies.py, backend/app/core/database.py, backend/app/core/errors.py]
  provides: [POST /api/v1/progress/check-in, GET /api/v1/progress/summary, GET /api/v1/progress/weekly-report]
  affects: [frontend progress screen (Plan 03), weekly report UI]
tech_stack:
  added: []
  patterns: [SQLAlchemy 2.x upsert via flush, Pydantic v2 model_validate from ORM, rule-based focus suggestion, behavior wins chip pattern]
key_files:
  created:
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_progress.py
    - backend/app/schemas/progress.py
    - backend/app/repositories/progress_repository.py
    - backend/app/services/progress_service.py
    - backend/app/api/v1/endpoints/progress.py
  modified:
    - backend/app/api/v1/router.py
decisions:
  - Weekly window is Monday-to-Sunday (ISO week) computed from date.today()
  - Upsert strategy: PUT semantics — all fields overwritten with supplied values including None
  - Behavior wins: 5 tracked (sleep, activity, logging, low_stress, low_hunger) + 3 future-tracked (protein, fiber, hydration)
  - suggested_focus uses rule-based cascade: logging < 3 days → sleep < 6.5h → stress >= 4 → activity < 100min → hunger > 3
  - conftest uses StaticPool for in-memory SQLite to ensure single connection across fixtures
metrics:
  duration: "6m"
  completed: "2026-06-04"
  tasks: 3
  files: 8
requirements:
  - PROG-01
  - PROG-02
  - PROG-03
---

# Phase 9 Plan 01: Progress Backend Layer Summary

**One-liner:** Three FastAPI progress endpoints (check-in, summary, weekly-report) with SQLAlchemy 2.x upsert, behavior wins aggregation, and 7/7 pytest tests passing.

## What Was Built

### Endpoints Created

| Endpoint | Method | Status | Response Shape |
|----------|--------|--------|----------------|
| `/api/v1/progress/check-in` | POST | 201 | `CheckInResponse` (id, check_date, weight_kg, hunger_level, sleep_hours, stress_level, activity_minutes, adherence_notes, created_at) |
| `/api/v1/progress/summary` | GET | 200 | `ProgressSummaryResponse` (has_data, recent_checkins, weight_series, latest_weight_kg, weight_trend, behavior_wins[8], logging_streak, empty_state_message) |
| `/api/v1/progress/weekly-report` | GET | 200 | `WeeklyReportResponse` (has_report, week_start, week_end, report: WeeklyReportData, empty_state_message) |

All three endpoints require a valid Bearer token (returns 401 on missing/invalid token).

### Behavior Wins Architecture

8 chips always returned, split into:
- **5 tracked**: sleep (>= 7.0h avg), activity (>= 30 min avg), logging (streak >= 3 days), low_stress (<= 2.5 avg), low_hunger (<= 2.5 avg)
- **3 future-tracked**: protein, fiber, hydration (tracked=False, achieved=False in v1)

### Weekly Report Logic

- Week window: Monday to Sunday of current week (ISO weeks)
- `adherence_pct` = `logging_days / 7 * 100` (rounded)
- `suggested_focus` uses rule cascade: fewer logging days → sleep → stress → activity → hunger → positive fallback
- Report is persisted to `WeeklyReport` table on every successful generation (upsert by week_start)

### Summary Calculation

- Fetches 14 most-recent check-ins
- `latest_weight_kg` = most recent weight in the oldest-to-newest ordering
- `weight_series` = chronological list (oldest first)
- `logging_streak` = consecutive days ending today or yesterday

## Test Coverage

| Test | Assertion | Status |
|------|-----------|--------|
| `test_submit_check_in` | 201, response fields match, 1 DB row | PASSED |
| `test_checkin_upsert` | 2 posts same date → 1 row, latest weight wins | PASSED |
| `test_unauthenticated_returns_401` | no auth header → 401 | PASSED |
| `test_progress_summary` | has_data=True, 3 weights, 8 wins, 5 tracked | PASSED |
| `test_progress_summary_empty` | has_data=False, empty_state_message in Persian | PASSED |
| `test_weekly_report` | 7 checkins → logging_days=7, adherence_pct=100, avg values correct | PASSED |
| `test_weekly_report_empty` | has_report=False, week boundaries still returned | PASSED |

**Result: 7/7 tests pass. 0 skips.**

## Key Decisions Made

1. **Upsert is full PUT semantics**: All fields (including None) overwrite previous values. This is the simplest correct behavior for "update today's check-in". Partial-update (PATCH) can be added later.

2. **Weekly window is ISO Monday-to-Sunday**: `today - timedelta(days=today.weekday())` gives Monday. Consistent across all locales.

3. **StaticPool in conftest**: Prevents SQLite in-memory from creating a new DB on each connection. Required for TestClient to see the same data as direct session queries.

4. **No AI calls in progress service**: All aggregation is rule-based Python. No `ai_provider` imports, no `agent_service`. Pure statistics.

5. **Relationship traversal avoided**: Service never accesses `checkin.user` or `user.daily_checkins`. Only scalar columns used, preventing `lazy="raise"` errors.

## Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `backend/tests/__init__.py` | Created | Package marker for pytest discovery |
| `backend/tests/conftest.py` | Created | Fixtures: engine, db_session, test_user, client, auth_headers, unauth_client |
| `backend/tests/test_progress.py` | Created | 7 tests for all three endpoints |
| `backend/app/schemas/progress.py` | Created | Pydantic v2 schemas: CheckInRequest/Response, BehaviorWin, WeightTrend, ProgressSummaryResponse, WeeklyReportData/Response |
| `backend/app/repositories/progress_repository.py` | Created | upsert_checkin, get_recent_checkins, get_checkins_between, get_or_create_weekly_report, save_weekly_report |
| `backend/app/services/progress_service.py` | Created | submit_check_in, get_summary, get_weekly_report, behavior wins helpers, suggest_focus |
| `backend/app/api/v1/endpoints/progress.py` | Created | Three FastAPI route handlers with AppError/Exception handling |
| `backend/app/api/v1/router.py` | Modified | Added progress_router import and include_router at /progress |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | c357d53 | test(09-01): add pytest scaffold for progress endpoints |
| Task 2 | 92d810a | feat(09-01): implement progress backend layer (schemas, repo, service, endpoints) |
| Task 3 | bec433d | test(09-01): implement 7 progress endpoint tests (GREEN phase) |

## Deviations from Plan

None — plan executed exactly as written. The conftest uses `StaticPool` (from the main repo's implementation) which was a minor enhancement over the plan's example (which did not specify a pool class). This is a correctness fix, not a deviation.

## Known Stubs

None. All endpoints are fully wired with real data. No hardcoded empty values flow to API responses; empty states use computed logic with Persian messages.

## Self-Check: PASSED

- `backend/tests/__init__.py` exists: FOUND
- `backend/tests/conftest.py` exists with `def client(`, `def test_user(`, `app.dependency_overrides[get_session]`: FOUND
- `backend/tests/test_progress.py` exists with 7 `def test_` functions: FOUND
- `backend/app/schemas/progress.py` exists with all 7 exported classes: FOUND
- `backend/app/repositories/progress_repository.py` exists with all 4 functions: FOUND
- `backend/app/services/progress_service.py` exists with all 5 functions: FOUND
- `backend/app/api/v1/endpoints/progress.py` exists with router and 3 routes: FOUND
- `backend/app/api/v1/router.py` modified with progress_router: FOUND
- Commit c357d53 exists: FOUND
- Commit 92d810a exists: FOUND
- Commit bec433d exists: FOUND
- 7/7 tests pass: VERIFIED
- All 3 routes registered at /api/v1/progress/*: VERIFIED
- No SQLAlchemy 1.x patterns: VERIFIED
- No AI imports in progress_service: VERIFIED
