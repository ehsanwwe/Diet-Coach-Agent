# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 1 COMPLETE → Phase 2 next
**Overall progress:** Phase 1 of 10 complete (10%)

## What Exists Now

### Backend (`backend/`)
- `pyproject.toml` — all dependencies declared (FastAPI, SQLAlchemy 2.x, Alembic, PyJWT, pydantic-settings)
- `app/core/config.py` — pydantic-settings BaseSettings, SECRET_KEY validation, all 10 OPENCLAW_* vars
- `app/core/database.py` — SQLAlchemy 2.x sync engine, get_session(), DeclarativeBase
- `app/core/errors.py` — consistent error response helpers (AppError, error_response, raise_http_error)
- `app/models/` — ALL 22 ORM models defined with lazy="raise" on all relationships
  - Group 1: User, AuthOTP, TokenBlocklist, AuditLog, UserLanguagePreference
  - Group 2: UserProfile, MedicalCondition, UserMedicalFlag, Medication, Allergy
  - Group 3: LifestyleProfile, FoodPreference, BehaviorProfile
  - Group 4: NutritionGoal, NutritionRiskAssessment, NutritionPlan, NutritionPlanMeal
  - Group 5: ChatSession, ChatMessage, AudioMessage, MealEntry
  - Group 6: DailyCheckIn, ProgressEntry, WeeklyReport
- `alembic/` — Alembic configured with render_as_batch=True + compare_type=True
- `alembic/versions/0001_initial_schema.py` — initial migration for all 22 tables
- `app/main.py` — FastAPI app factory, CORS from env, global error handlers
- `app/api/v1/router.py` — v1 router, health endpoint at /api/v1/health
- `app/schemas/common.py` — ErrorResponse, SuccessResponse, PaginatedResponse (Pydantic v2)
- `backend/.env.example` — all env vars documented including all 10 OPENCLAW_* vars
- `backend/README.md` — setup guide with migration commands and technology notes

### Frontend (`frontend/`)
- Next.js 16 skeleton with App Router `src/app/[lang]/` structure
- Tailwind CSS v4 with `@tailwindcss/postcss` PostCSS plugin
- TypeScript strict mode enabled
- `frontend/.env.example` — frontend env vars documented
- `frontend/README.md` — setup guide

### Root
- `.gitignore` — SQLite, env files, uploads, caches all excluded
- `.env.example` — cross-service env vars, links to service examples
- `backend/README.md`, `frontend/README.md` — setup guides

## Critical Safeguards Verified
- `lazy="raise"` on ALL ORM relationships (no silent N+1 possible)
- `render_as_batch=True` in BOTH alembic/env.py context.configure() calls
- `SECRET_KEY` validation at startup — server refuses to start without it
- No hard-coded CORS origins — loaded from `CORS_ORIGINS` env var

## Known Issues / Blockers
- Phase 7 AI Layer: Persian food nutrition accuracy needs validation
- Phase 6 Voice: iOS Safari MediaRecorder behavior needs real-device testing

## How to Resume (Cold Start)
1. Read this file + NEXT_STEPS.md
2. `cd backend && SECRET_KEY=... alembic upgrade head` to verify DB
3. `cd backend && SECRET_KEY=... uvicorn app.main:app` to verify server
4. Start Phase 2: `/gsd:plan-phase 2` or `/gsd:execute-phase 2`

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | Not started |
| 3 — Authentication | Not started |
| 4 — Onboarding Backend | Not started |
| 5 — Onboarding Frontend | Not started |
| 6 — Voice & Audio | Not started |
| 7 — Nutrition Backend & AI Layer | Not started |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

---
*Last updated: 2026-06-03*
