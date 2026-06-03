# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 7 COMPLETE → Phase 8 next
**Overall progress:** Phase 7 of 10 complete (70%)

## What Exists Now

### Backend (`backend/`) — Phases 1, 3, 4, 6, 7 COMPLETE

#### Phase 1–4, 6 (unchanged)
- Full ORM models, Alembic migrations, FastAPI shell
- Auth: OTP login, JWT, logout, /me
- Onboarding: GET /status, POST /profile /medical /lifestyle /preferences /behavior /complete
- Safety guardrail service (risk_level, clinical_review_required)
- Onboarding Chat: text + audio + history endpoints

#### Phase 7 — Nutrition Backend & AI Layer (NEW)
- **AI Provider Abstraction:**
  - `backend/app/services/ai_provider.py` — AIProvider ABC, AIProviderResult, `get_ai_provider()` factory
  - `backend/app/services/mock_ai_provider.py` — deterministic Persian-friendly mock for all 4 task types
  - `backend/app/services/openclaw_provider.py` — httpx-based OpenAI-compatible provider with retries
- **Prompt & Context Layer:**
  - `backend/app/services/prompt_builder.py` — builds system+user prompts for generate_plan, analyze_meal, what_to_eat_now, adapt_plan
  - `backend/app/services/conversation_context_manager.py` — trims messages to OPENCLAW_CONTEXT_MAX_MESSAGES
  - `backend/app/services/nutrition_memory_service.py` — collects NutritionMemoryContext from all DB tables
- **Orchestration:**
  - `backend/app/services/nutrition_agent_service.py` — AI pipeline with JSON fallback + mock fallback
  - `backend/app/services/nutrition_service.py` — business logic for all 6 endpoints + safety guardrails
- **Data Layer:**
  - `backend/app/schemas/nutrition.py` — Pydantic v2 schemas for all 6 endpoints
  - `backend/app/repositories/nutrition_repository.py` — NutritionGoal, NutritionPlan, NutritionPlanMeal, MealEntry DB ops
  - `backend/alembic/versions/0003_add_nutrition_plan_metadata.py` — adds `plan_metadata` Text column to `nutrition_plans`
  - `backend/app/models/nutrition.py` — updated with `plan_metadata` field
- **API Endpoints (all authenticated):**
  - `GET  /api/v1/nutrition/profile` — user's full nutrition profile summary
  - `GET  /api/v1/nutrition/plan` — current active plan (or empty state)
  - `POST /api/v1/nutrition/plan/generate` — generate adaptive nutrition plan
  - `POST /api/v1/nutrition/meal/analyze` — analyze meal quality + log entry
  - `POST /api/v1/nutrition/what-to-eat-now` — suggest Persian-culture food options
  - `POST /api/v1/nutrition/adapt-plan` — adapt plan based on user feedback
- **Config:**
  - `AI_PROVIDER` env var added (default: "mock")
  - `backend/.env.example` updated with AI_PROVIDER + recommended OpenClaw values

### Safety Behavior
- `clinical_review_required` users: get wellness guidance only (no aggressive plan)
- `risk_level=high` users: wellness reminder appended to all warnings
- No body-shaming language in prompts
- No medical prescriptions in AI output
- No doctor-replacement claims (reminder included in system prompts)

### Provider Behavior
- `AI_PROVIDER=mock` (default) → MockAIProvider — always works, no external calls
- `AI_PROVIDER=openclaw` + `OPENCLAW_BASE_URL` set → OpenClawProvider
- OpenClawProvider fails → falls back to MockAIProvider, marks `is_mock=True`
- Unparseable AI JSON → falls back to mock data, marks `is_mock=True`

### Frontend (`frontend/`) — Phases 2, 3, 5, 6 COMPLETE
- No Phase 8 frontend implemented yet.

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | **COMPLETE** |
| 4 — Onboarding Backend | **COMPLETE** |
| 5 — Onboarding Frontend | **COMPLETE** |
| 6 — Voice & Audio | **COMPLETE** |
| 7 — Nutrition Backend & AI Layer | **COMPLETE** |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

## How to Resume (Cold Start)
1. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm run dev` → open http://localhost:3000
3. Login: POST /api/v1/auth/request-otp → verify-otp with OTP 123456
4. Test nutrition: POST /api/v1/nutrition/plan/generate with Bearer token
5. Mock mode: AI_PROVIDER=mock in .env → works without OpenClaw
