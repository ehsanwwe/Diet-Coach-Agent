# Diet Coach Agent

## What This Is

An AI-powered multilingual nutrition and health companion that guides users through personalized meal planning, daily behavior coaching, and adaptive diet management. Built for Persian-speaking users first (RTL, culturally-aware), with full English and Arabic support. The app functions as a daily wellness partner — not a one-time diet calculator — with safety guardrails for medical conditions.

## Core Value

A daily AI nutrition companion that users trust to guide every meal decision safely, respectfully, and practically — rooted in Iranian food culture and clinical guardrails.

## Requirements

### Validated

**Phase 10 — Settings, Polish & Remaining UI (validated 2026-06-04):**
- Settings screen with Language, Profile (phone read-only), Account (logout with inline confirmation) sections — UI-13
- Language selector screen writing `NEXT_LOCALE` cookie + fire-and-forget backend persist via `PATCH /api/v1/settings/language` — UI-14
- Settings tab enabled in AppBottomNav with active path highlighting — UI-17
- `app-container` wrapper on every authenticated screen page (was missing on onboarding) — UI-16
- Canonical `err.message === 'UNAUTHORIZED'` catch pattern adopted uniformly across all client components — UI-20
- Loading spinner + empty state + error card standardized in CompanionChat, PlanSummary, NutritionDashboard — UI-18, UI-19
- Backend settings module: `PATCH /api/v1/settings/language` with 5-test pytest coverage — UI-13, UI-14

### Active

**Infrastructure**
- [ ] Monorepo with `backend/` and `frontend/` directories
- [ ] Backend: Python, FastAPI, SQLite, SQLAlchemy 2.x, Alembic, Pydantic v2, Uvicorn
- [ ] Frontend: Next.js, TypeScript, App Router, Tailwind CSS, mobile-first centered layout
- [ ] Git: SQLite file excluded, env files excluded, audio/upload dirs excluded
- [ ] Environment-based config (`.env.example` for both backend and frontend)
- [ ] Docker Compose optional but structured for it

**Authentication**
- [ ] Phone OTP login flow (`request-otp` → `verify-otp`)
- [ ] Default OTP `123456` in development
- [ ] JWT/session-based auth with secure persistence
- [ ] Auth guards on protected frontend routes
- [ ] Prepared for real SMS provider plug-in
- [ ] Endpoints: `POST /api/v1/auth/request-otp`, `POST /api/v1/auth/verify-otp`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`

**Onboarding**
- [ ] 7-step animated multi-step registration flow
- [ ] Step 1: Basic profile (name, gender, DOB/age, height, weight, target weight, waist)
- [ ] Step 2: Main goal (12 options including weight loss, PCOS, pregnancy route, sports, etc.)
- [ ] Step 3: Medical safety screening (diabetes, kidney, liver, thyroid, BP, PCOS, eating disorder, bariatric, medications, allergies, red-flag symptoms)
- [ ] Step 4: Lifestyle (sleep, stress, work schedule, activity, exercise days, cooking ability, budget, eating out, travel)
- [ ] Step 5: Food preferences (Iranian foods, veg/vegan, halal, dislikes, favorites, breakfast, rice/bread, sweets, tea, restaurants)
- [ ] Step 6: Behavior and habit profile (emotional eating, night eating, meal skipping, cravings, binge episodes, diet history, failures, hunger pattern, motivation)
- [ ] Step 7: Final video gate + habit chat (video placeholder, chat disabled until video watched, text + voice input)
- [ ] Direction-aware slide animations (RTL natural for Persian/Arabic, LTR for English)
- [ ] Onboarding APIs for each step
- [ ] `POST /api/v1/onboarding/complete`

**Onboarding Chat (Voice + Text)**
- [ ] Final onboarding chat textarea (disabled until video ends or "Mark as watched" in dev)
- [ ] Text chat support
- [ ] Voice recording with MediaRecorder API
- [ ] Audio visualizer/waveform using Web Audio API AnalyserNode
- [ ] Recording controls: start, pause/stop, cancel, send
- [ ] Audio preview before send
- [ ] Multipart audio upload to backend
- [ ] `POST /api/v1/onboarding/chat/text`, `POST /api/v1/onboarding/chat/audio`, `GET /api/v1/onboarding/chat/history`
- [ ] STT/transcription architecture prepared (status: `pending` or `not_configured` for now)

**Nutrition Profile & AI Agent**
- [ ] Dynamic NutritionProfile per user (anthropometrics, goals, medical flags, lifestyle, preferences, behavior patterns, risk level, plan, progress)
- [ ] Risk level field: `low` / `medium` / `high` / `clinical_review_required`
- [ ] Nutrition problem detection (low protein, irregular meals, night eating, emotional eating, etc.)
- [ ] Medical safety guardrail service — triggers `clinical_review_required` for: diabetes+medication, kidney disease, pregnancy, eating disorder, bariatric surgery, serious symptoms
- [ ] AI provider abstraction layer (`AIProvider`, `NutritionAgentService`, `PromptBuilder`, `SafetyGuardrailService`, `NutritionMemoryService`)
- [ ] Deterministic mock AI responses when no provider configured
- [ ] Persian food intelligence (rice, stews, kebab, ash, adasi, omelet, yogurt, doogh, tea, sweets, fast food)
- [ ] Endpoints: `GET /api/v1/nutrition/profile`, `GET /api/v1/nutrition/plan`, `POST /api/v1/nutrition/plan/generate`, `POST /api/v1/nutrition/meal/analyze`, `POST /api/v1/nutrition/what-to-eat-now`, `POST /api/v1/nutrition/adapt-plan`

**Chat Companion**
- [ ] Daily companion chat (text first, audio architecture prepared)
- [ ] Chat history per user
- [ ] `POST /api/v1/chat/message`, `GET /api/v1/chat/history`

**Progress & Reports**
- [ ] Daily check-in (weight, hunger, sleep, stress, activity, adherence)
- [ ] Weekly report (weight trend, adherence, cravings, sleep/stress relation, food quality)
- [ ] Progress dashboard (not weight-only: behavior wins, fiber, protein, water, logging consistency)
- [ ] `POST /api/v1/progress/check-in`, `GET /api/v1/progress/summary`, `GET /api/v1/progress/weekly-report`

**i18n, RTL/LTR**
- [ ] Persian default language (`fa`) with complete dictionary
- [ ] English (`en`) and Arabic (`ar`) initial translations
- [ ] Dynamic document direction (RTL for fa/ar, LTR for en)
- [ ] CSS logical properties throughout (no hard-coded left/right)
- [ ] Direction-aware icon utility (chevrons, back/next arrows mirror in RTL)
- [ ] Direction-aware page transition animations

**Frontend Screens (16 total)**
- [ ] Splash/landing
- [ ] Phone OTP login
- [ ] OTP verification
- [ ] Multi-step onboarding (7 steps)
- [ ] Final onboarding video + habit chat
- [ ] Home dashboard
- [ ] Daily check-in
- [ ] Diet plan
- [ ] Chat companion
- [ ] Meal analysis
- [ ] "What should I eat now?"
- [ ] Progress and weekly report
- [ ] Settings
- [ ] Language selector
- [ ] Medical safety notice / review required state

**Data Models (Alembic-managed)**
- [ ] User, AuthOTP, UserProfile, MedicalCondition, UserMedicalFlag
- [ ] Medication, Allergy, LifestyleProfile, FoodPreference, BehaviorProfile
- [ ] NutritionGoal, NutritionRiskAssessment, NutritionPlan, NutritionPlanMeal
- [ ] MealEntry, ChatSession (with summary + message_count), ChatMessage, AudioMessage
- [ ] DailyCheckIn, ProgressEntry, WeeklyReport, UserLanguagePreference, AuditLog

**PWA**
- [ ] Web app manifest (name, icons, theme color, display: standalone)
- [ ] Service worker with offline fallback
- [ ] Install prompt at appropriate moment (post-onboarding or first meaningful use)
- [ ] App-like mobile UI when installed (no browser chrome)

**OpenClaw AI Integration**
- [ ] `OpenClawProvider` implementing `AIProvider` using OpenAI-compatible `/chat/completions`
- [ ] All 10 `OPENCLAW_*` env vars: `BASE_URL`, `API_KEY`, `MODEL`, `CHAT_COMPLETIONS_PATH`, `TIMEOUT_SECONDS`, `MAX_RETRIES`, `TEMPERATURE`, `MAX_TOKENS`, `CONTEXT_MAX_MESSAGES`, `CONTEXT_SUMMARY_ENABLED`
- [ ] Every AI endpoint (chat, plan gen, meal analysis, what-to-eat-now, adapt-plan, onboarding chat) routes through OpenClawProvider when configured; falls back to MockAIProvider when not
- [ ] Rolling conversation summaries via `OPENCLAW_CONTEXT_SUMMARY_ENABLED`
- [ ] Structured `NutritionMemoryContext` injected into every AI system prompt prefix

**UI Style System**
- [ ] Muted, pale, soft aesthetic — no saturated colors, no gym palette
- [ ] App-like layout — bottom nav, full-bleed screens, no Bootstrap card grids, no admin borders
- [ ] Soft rounded corners (≥ 16px), subtle shadows — health app feel
- [ ] Comfortable typography (≥ 15px body, ≥ 1.6 line height)

**Continuation Files (updated after every commit)**
- [ ] `PROJECT_STATE.md` — current phase, last completed, in-progress, blockers
- [ ] `NEXT_STEPS.md` — exact next action, file to touch, command to run
- [ ] `DECISIONS.md` — architectural decisions with rationale (append-only)
- [ ] `CHANGELOG.md` — Keep a Changelog format, updated every commit

**Env Files**
- [ ] Root `.env.example`
- [ ] `backend/.env.example` (all 10 `OPENCLAW_*` vars + all backend vars)
- [ ] `frontend/.env.example`

### Out of Scope

- Real SMS provider integration — prepared but not wired (OTP=123456 in dev)
- OpenAI/Claude SDK direct integration — OpenClaw covers OpenAI-compatible real AI in v1
- STT/transcription — architecture prepared, status=pending
- Image-based meal analysis — text-first, architecture prepared
- Human nutritionist panel — models/routes scaffolded, not built
- Payment/subscription — not in v1
- Push notifications — not in v1
- Wearable integration — not in v1
- Native mobile app — PWA-ready web only

## Context

- Target primary users: Persian-speaking adults seeking professional-grade nutrition guidance
- Cultural context: Iranian food culture, halal considerations, RTL-native UI
- Medical safety is a first-class concern — the app must never replace a physician/dietitian
- Development language: Python (backend) + TypeScript (frontend)
- OTP auth simulates real flow but accepts `123456` in dev; real SMS provider can be plugged in later
- The product should feel like a premium health companion, not a gym app or a clinical form

## Constraints

- **Database**: SQLite only for now — no PostgreSQL yet
- **Auth**: Phone OTP only — no email/password, no OAuth
- **Language**: Persian is default; app must feel native to Persian speakers
- **AI**: OpenClawProvider when `OPENCLAW_BASE_URL` is set; MockAIProvider fallback — app must work end-to-end without OpenClaw configured
- **OpenClaw config**: All 10 `OPENCLAW_*` vars from backend environment only — never hard-coded, never from frontend
- **Audio**: Browser MediaRecorder API — no native mobile SDKs
- **Migrations**: All schema changes via Alembic — SQLite file never committed
- **Backend structure**: Must follow `backend/app/` modular structure as specified
- **Frontend structure**: Must follow `frontend/src/` modular structure as specified

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite (not PostgreSQL) | Simplicity for v1; Alembic migrations ensure easy upgrade path | — Pending |
| Phone OTP (not email/password) | Persian market norm; lower friction for target users | — Pending |
| Persian as default language | Primary target market; RTL-first is easier than retrofitting | — Pending |
| Dictionary-based i18n (not next-intl/i18next) | Full control, no vendor lock-in, simpler for team | — Pending |
| AI provider abstraction from day 1 | Avoids tight coupling to any one provider; mock first | — Pending |
| Mobile-first centered layout for desktop | Health apps are primarily mobile; desktop gets same centered view | — Pending |
| MediaRecorder API for audio (not external SDK) | No dependency, works in modern browsers, sufficient for MVP | — Pending |
| PWA (not native app) | Web-first; PWA gives install prompt and app-like feel without App Store dependency | — Pending |
| OpenClaw as v1 real AI provider | OpenAI-compatible interface; env-var-only config; falls back to mock — enables real AI without SDK lock-in | — Pending |
| Rolling conversation summaries | Long OpenClaw conversations exceed context limits; summaries stored in ChatSession and re-injected | — Pending |
| Continuation files updated every commit | After `/clear` context is lost; PROJECT_STATE.md / NEXT_STEPS.md / DECISIONS.md / CHANGELOG.md are the persistent resume trail | — Pending |
| UI style: muted/pale/app-like | Target users are health-conscious adults; clinical-calm aesthetic builds trust vs. aggressive gym app look | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-03 after PWA, OpenClaw, UI style, conversation memory, and continuation file requirements added*
