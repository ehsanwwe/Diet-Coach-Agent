---
phase: 10-settings-polish-remaining-ui
plan: "01"
subsystem: settings-i18n-backend
tags: [i18n, dictionary, backend, settings, language-preference]
dependency_graph:
  requires: []
  provides:
    - Dictionary.settings namespace (fa/en/ar)
    - PATCH /api/v1/settings/language endpoint
    - UserLanguagePreference upsert service
  affects:
    - frontend/src/dictionaries/fa.ts
    - frontend/src/dictionaries/en.ts
    - frontend/src/dictionaries/ar.ts
    - backend/app/api/v1/router.py
tech_stack:
  added: []
  patterns:
    - Pydantic v2 Literal["fa","en","ar"] enum validation
    - SQLAlchemy 2.x select() upsert pattern
    - FastAPI Depends(get_current_user) auth guard
    - TestClient with session + auth dependency overrides
key_files:
  created:
    - backend/app/schemas/settings.py
    - backend/app/services/settings_service.py
    - backend/app/api/v1/endpoints/settings.py
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_settings.py
  modified:
    - frontend/src/dictionaries/fa.ts
    - frontend/src/dictionaries/en.ts
    - frontend/src/dictionaries/ar.ts
    - backend/app/api/v1/router.py
decisions:
  - "Tests created in backend/tests/ (no pre-existing test directory; this plan created it)"
  - "datetime.now(UTC) used instead of deprecated datetime.utcnow() in settings_service"
  - "get_session imported from app.core.database (not app.api.dependencies) matching existing endpoint pattern"
metrics:
  duration: "13 minutes"
  completed: "2026-06-04"
  tasks_completed: 2
  files_modified: 10
---

# Phase 10 Plan 01: Settings Foundation Summary

**One-liner:** Settings dictionary namespace (12 keys, fa/en/ar) + PATCH /api/v1/settings/language backend endpoint with UserLanguagePreference upsert and 5-test pytest suite.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend Dictionary with settings namespace | `974f266` | fa.ts, en.ts, ar.ts |
| 2 | Backend settings module + pytest | `5e4fa7f` | settings.py (schema/service/endpoint), router.py, tests/ |

## Dictionary Keys Added

Under `settings.*` namespace in `Dictionary` interface and all three locale files:

| Key | fa | en | ar |
|-----|----|----|-----|
| title | تنظیمات | Settings | الإعدادات |
| languageSection | زبان | Language | اللغة |
| profileSection | پروفایل | Profile | الملف الشخصي |
| accountSection | حساب کاربری | Account | الحساب |
| currentLanguage | زبان فعلی | Current language | اللغة الحالية |
| changeLanguage | تغییر زبان | Change language | تغيير اللغة |
| displayName | نام شما | Your name | اسمك |
| phoneNumber | شماره موبایل | Phone number | رقم الهاتف |
| logoutBtn | خروج از حساب | Log out | تسجيل الخروج |
| logoutConfirm | آیا مطمئن هستید...؟ | Are you sure...? | هل أنت متأكد...؟ |
| logoutCancel | ماندن | Stay | البقاء |
| appVersion | نسخه برنامه | App version | إصدار التطبيق |

## Backend Endpoint

**URL:** `PATCH /api/v1/settings/language`

**Request body:**
```json
{"language_code": "fa" | "en" | "ar"}
```

**Response (200):**
```json
{
  "status": "ok",
  "data": {
    "language_code": "en",
    "updated_at": "2026-06-04T14:10:00"
  }
}
```

**Error cases:**
- 401 — no Authorization header (or invalid/expired token)
- 422 — language_code not in ["fa","en","ar"], or field missing

## Test Results

```
cd backend && python -m pytest tests/test_settings.py -x -q
.....
5 passed in 0.07s
```

Tests: `test_update_language_success`, `test_update_language_upsert`, `test_update_language_unauthorized`, `test_update_language_invalid_locale`, `test_update_language_missing_field`

Full suite: `python -m pytest -x -q` → 5 passed, no regressions.

## Verification Results

1. `cd frontend && tsc --noEmit` — exit 0 (all three dictionaries type-check)
2. `cd backend && python -m pytest tests/test_settings.py -x -q` — 5 passed
3. `cd backend && python -m pytest -x -q` — 5 passed (no regressions)
4. `grep "settings:\s*{" fa.ts en.ts ar.ts` — 2 matches in fa.ts (interface + literal), 1 each in en.ts and ar.ts
5. `grep "include_router(settings_router"` in router.py — exactly 1 match

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used `datetime.now(UTC)` instead of deprecated `datetime.utcnow()`**
- **Found during:** Task 2 — pytest emitted a DeprecationWarning
- **Issue:** `datetime.utcnow()` is deprecated in Python 3.12+
- **Fix:** Changed to `datetime.now(UTC)` with explicit UTC import
- **Files modified:** `backend/app/services/settings_service.py`
- **Commit:** `5e4fa7f`

**2. [Rule 3 - Blocking] Created backend/tests/ directory and conftest.py from scratch**
- **Found during:** Task 2 — no tests directory existed in the worktree
- **Issue:** Plan expected `conftest.py` fixtures (`client`, `unauth_client`, `db_session`, `test_user`, `auth_headers`) but no tests directory existed
- **Fix:** Created full conftest.py with in-memory SQLite engine, session-rollback isolation, TestClient with dependency overrides for auth and session
- **Files modified:** `backend/tests/__init__.py`, `backend/tests/conftest.py`
- **Commit:** `5e4fa7f`

**3. [Rule 3 - Blocking] `get_session` imported from `app.core.database` not `app.api.dependencies`**
- **Found during:** Task 2 — plan interface block showed `from app.api.dependencies import get_current_user, get_session` but codebase imports `get_session` from `app.core.database`
- **Fix:** Used `from app.core.database import get_session` in endpoint (mirrors existing onboarding.py pattern)
- **Commit:** `5e4fa7f`

## Known Stubs

None — the endpoint is fully wired; UserLanguagePreference model exists and is persisted correctly.

## Self-Check: PASSED
