# Requirements: Diet Coach Agent

**Defined:** 2026-06-03
**Core Value:** A daily AI nutrition companion that users trust to guide every meal decision safely, respectfully, and practically — rooted in Iranian food culture and clinical guardrails.

## v1 Requirements

### Infrastructure

- [ ] **INFRA-01**: Monorepo contains exactly `backend/` and `frontend/` directories; no app source files in root
- [ ] **INFRA-02**: `.gitignore` excludes SQLite files (`*.db`, `*.sqlite`, `*.sqlite3`), env files, audio/upload dirs, caches, and `.planning/` internal dirs
- [ ] **INFRA-03**: `backend/.env.example` documents all required and optional environment variables including all 10 `OPENCLAW_*` variables
- [ ] **INFRA-04**: `frontend/.env.example` documents all required frontend environment variables
- [ ] **INFRA-05**: Backend runs with `uvicorn app.main:app` from `backend/` directory
- [ ] **INFRA-06**: Frontend runs with `npm run dev` from `frontend/` directory
- [ ] **INFRA-07**: `backend/README.md` documents setup, migration commands, and environment variables
- [ ] **INFRA-08**: `frontend/README.md` documents setup and development commands
- [ ] **INFRA-09**: Root `.env.example` at repository root documents cross-service environment variables and links to `backend/.env.example` and `frontend/.env.example`

### Backend Foundation

- [ ] **BE-01**: FastAPI app factory with CORS configured from environment variables
- [ ] **BE-02**: SQLite database with SQLAlchemy 2.x (sync, 2.0-style only) and `Session` via `Depends(get_session)`
- [ ] **BE-03**: Alembic migrations with `render_as_batch=True` in `env.py` (required for SQLite DDL changes)
- [ ] **BE-04**: All ORM relationships use `lazy="raise"` to prevent silent N+1 errors
- [ ] **BE-05**: Database creates automatically via Alembic on startup or via documented `alembic upgrade head` command
- [ ] **BE-06**: Pydantic v2 schemas for all request/response models
- [ ] **BE-07**: `pydantic-settings` for typed environment config in `backend/app/core/config.py`
- [ ] **BE-08**: Consistent error response format across all endpoints (status, message, detail)
- [ ] **BE-09**: All API routes versioned under `/api/v1/`
- [ ] **BE-10**: OpenAPI docs enabled at `/docs`
- [ ] **BE-11**: Modular structure: `core/`, `api/v1/`, `models/`, `schemas/`, `services/`, `repositories/`
- [ ] **BE-12**: `SECRET_KEY` validated at startup (app refuses to start if absent or default)

### Authentication

- [ ] **AUTH-01**: User can request OTP by providing phone number (`POST /api/v1/auth/request-otp`)
- [ ] **AUTH-02**: OTP `123456` is accepted in development mode (configurable via env)
- [ ] **AUTH-03**: User can verify OTP and receive JWT access token (`POST /api/v1/auth/verify-otp`)
- [ ] **AUTH-04**: New user is created automatically on first successful OTP verification
- [ ] **AUTH-05**: Authenticated user can retrieve their own profile (`GET /api/v1/auth/me`)
- [ ] **AUTH-06**: User can logout, invalidating their token server-side (`POST /api/v1/auth/logout`)
- [ ] **AUTH-07**: JWT tokens use `jti` claim; server-side revocation table prevents replay after logout
- [ ] **AUTH-08**: Auth dependencies (`Depends(get_current_user)`) protect all non-public endpoints
- [ ] **AUTH-09**: Phone number is validated for reasonable format before OTP is sent
- [ ] **AUTH-10**: OTP architecture is structured so a real SMS provider (e.g., Kavenegar) can be plugged in via env var

### Onboarding

- [ ] **OB-01**: Onboarding status endpoint returns current step and completion state (`GET /api/v1/onboarding/status`)
- [ ] **OB-02**: Step 1 — basic profile saved: name, gender, birth date / age, height, current weight, target weight, waist circumference (`POST /api/v1/onboarding/profile`)
- [ ] **OB-03**: Step 2–3 — main goal and medical conditions saved with medical flag detection (`POST /api/v1/onboarding/medical`)
- [ ] **OB-04**: Step 4 — lifestyle data saved: sleep, stress, work schedule, activity, exercise days, cooking ability, budget, eating out, travel (`POST /api/v1/onboarding/lifestyle`)
- [ ] **OB-05**: Step 5–6 — food preferences and behavior profile saved (`POST /api/v1/onboarding/preferences`, `POST /api/v1/onboarding/behavior`)
- [ ] **OB-06**: Onboarding marked complete and NutritionProfile created (`POST /api/v1/onboarding/complete`)
- [ ] **OB-07**: Onboarding data survives browser close / app background; partially-saved steps are resumable from last completed step
- [ ] **OB-08**: Frontend multi-step wizard is animated with direction-aware slide transitions (next = natural for RTL; back = reverse)
- [ ] **OB-09**: Animation direction is governed by a `direction: "forward" | "backward"` field in Zustand store — not inferred from URL
- [ ] **OB-10**: Step 7 final page shows a video placeholder component at the top
- [ ] **OB-11**: Chat textarea below the video is disabled until video playback ends (or "Mark as watched" button clicked in dev mode only)
- [ ] **OB-12**: All 7 onboarding steps use React Hook Form + Zod validation
- [ ] **OB-13**: Medical safety screening step (step 3) correctly populates `UserMedicalFlag` records and triggers risk assessment

### Voice & Audio

- [ ] **AUDIO-01**: Final onboarding chat page supports text input and voice recording
- [ ] **AUDIO-02**: Voice recording uses browser MediaRecorder API (no external audio library)
- [ ] **AUDIO-03**: MIME type is detected via `isTypeSupported()` and passed to MediaRecorder constructor (handles `audio/mp4` on iOS, `audio/webm;codecs=opus` on Chrome)
- [ ] **AUDIO-04**: Audio waveform visualizer renders during recording using Web Audio API `AnalyserNode`
- [ ] **AUDIO-05**: Recording controls: start, stop, cancel, preview, send
- [ ] **AUDIO-06**: Elapsed recording time is displayed during recording
- [ ] **AUDIO-07**: Recorded audio can be previewed before sending
- [ ] **AUDIO-08**: Audio file uploaded to backend via multipart/form-data (`POST /api/v1/onboarding/chat/audio`)
- [ ] **AUDIO-09**: Backend saves audio file to local storage directory (excluded from git)
- [ ] **AUDIO-10**: Backend creates `AudioMessage` record with `transcription_status: "pending"` or `"not_configured"`
- [ ] **AUDIO-11**: STT/transcription architecture is structured so a real provider (Whisper, Azure, etc.) can be plugged in via env var
- [ ] **AUDIO-12**: Unsupported browser state is handled gracefully (text-only fallback shown)
- [ ] **AUDIO-13**: Microphone permission request is handled with user-friendly messaging

### Nutrition Profile & Safety

- [ ] **NUTR-01**: `NutritionProfile` created on onboarding completion with all profile data
- [ ] **NUTR-02**: `risk_level` field computed: `low` / `medium` / `high` / `clinical_review_required`
- [ ] **NUTR-03**: `SafetyGuardrailService` implemented as a FastAPI `Depends()` dependency (not manual calls)
- [ ] **NUTR-04**: `clinical_review_required` triggered for: diabetes + medication/insulin, kidney disease, pregnancy, eating disorder history, bariatric surgery history, rapid unexplained weight loss, serious symptoms (chest pain, fainting, blood in stool)
- [ ] **NUTR-05**: High-risk users see a respectful, clearly-worded clinical review screen (not an error)
- [ ] **NUTR-06**: Nutrition profile API returns structured profile data (`GET /api/v1/nutrition/profile`)
- [ ] **NUTR-07**: Nutrition plan generated on demand and stored (`POST /api/v1/nutrition/plan/generate`)
- [ ] **NUTR-08**: Current nutrition plan retrievable (`GET /api/v1/nutrition/plan`)
- [ ] **NUTR-09**: Text-based meal analysis evaluates quality beyond calories: protein, fiber, sugar, balance, hydration, portion (`POST /api/v1/nutrition/meal/analyze`)
- [ ] **NUTR-10**: "What should I eat now?" endpoint accepts available ingredients and returns 2–3 practical options aligned with user goal (`POST /api/v1/nutrition/what-to-eat-now`)
- [ ] **NUTR-11**: Nutrition plan can be adapted based on reported progress, hunger, sleep, stress, activity (`POST /api/v1/nutrition/adapt-plan`)
- [ ] **NUTR-12**: Persian food intelligence: the system understands common Iranian foods (rice, stews, kebab, ash, adasi, omelet, yogurt, doogh, tea, sweets, fast food) in responses

### AI Agent

- [ ] **AI-01**: `AIProvider` abstract base class defined with a consistent interface
- [ ] **AI-02**: `MockAIProvider` returns deterministic, contextually-appropriate Persian nutrition responses (minimum 20 variant responses seeded by goal type)
- [ ] **AI-03**: Active AI provider resolved from environment variable; `MockAIProvider` used when no provider configured
- [ ] **AI-04**: `NutritionAgentService` orchestrates prompt building, safety check, and AI call
- [ ] **AI-05**: `NutritionMemoryService` injects medical flags and risk level into every AI system prompt (not left to conversation history)
- [ ] **AI-06**: `PromptBuilder` constructs prompts with: system rules + medical flags prefix (position-protected, never truncated) + conversation history (pruned from oldest end)
- [ ] **AI-07**: AI responses never contain body-shaming, extreme diet advice, or claims that replace physician guidance
- [ ] **AI-08**: Mock responses feel realistic and contextually aligned — not obvious placeholders

### Chat Companion

- [ ] **CHAT-01**: User can send text messages to AI nutrition companion (`POST /api/v1/chat/message`)
- [ ] **CHAT-02**: Chat history is retrievable per user (`GET /api/v1/chat/history`)
- [ ] **CHAT-03**: Every chat endpoint independently applies `SafetyGuardrailService` (not delegated to plan endpoints)
- [ ] **CHAT-04**: Chat UI shows message history in threaded style
- [ ] **CHAT-05**: Chat UI supports sending messages (text) with smooth send UX
- [ ] **CHAT-06**: Audio input in main chat is architecturally prepared (UI placeholder present, backend endpoint ready)

### Progress & Reports

- [ ] **PROG-01**: User can submit daily check-in: weight, hunger, sleep duration, stress level, activity, adherence notes (`POST /api/v1/progress/check-in`)
- [ ] **PROG-02**: Progress summary (recent check-ins, trends) is retrievable (`GET /api/v1/progress/summary`)
- [ ] **PROG-03**: Weekly report generated with: weight trend, adherence trend, hunger pattern, sleep/stress relation, food quality, suggested next-week focus (`GET /api/v1/progress/weekly-report`)
- [ ] **PROG-04**: Progress dashboard shows behavior wins — not only weight (protein, fiber, water, sleep, movement, logging consistency)
- [ ] **PROG-05**: Weight trend shown as sparkline or simple chart (not just a number)

### Internationalization & RTL/LTR

- [ ] **I18N-01**: Persian (`fa`) is the default language with a complete dictionary covering all UI text (labels, buttons, errors, placeholders, onboarding text, chat text, nutrition sections, settings)
- [ ] **I18N-02**: English (`en`) dictionary created with reasonable initial translations
- [ ] **I18N-03**: Arabic (`ar`) dictionary created with reasonable initial translations
- [ ] **I18N-04**: Document direction set dynamically on `<html>` based on selected language (RTL for fa/ar, LTR for en)
- [ ] **I18N-05**: Locale is readable server-side (from cookie or URL segment) before page renders — no RTL direction flicker on load
- [ ] **I18N-06**: All CSS uses Tailwind v4 logical properties (`ps-`, `pe-`, `ms-`, `me-`) — never `pl-`, `pr-`, `ml-`, `mr-` directly
- [ ] **I18N-07**: Direction-aware icon utility: chevrons, back/next arrows, and step-nav icons mirror correctly in RTL without per-component hacks
- [ ] **I18N-08**: Page transition animations are direction-aware (RTL slide-next = slide from left; LTR slide-next = slide from right)
- [ ] **I18N-09**: Language selector screen with clear current selection and live preview
- [ ] **I18N-10**: No hard-coded Persian or English text in components — all user-facing strings from dictionaries

### Frontend Screens & UI

- [ ] **UI-01**: Splash / landing screen with app name and entry CTA
- [ ] **UI-02**: Phone OTP login screen (phone number input, request OTP)
- [ ] **UI-03**: OTP verification screen (6-digit code input, resend option)
- [ ] **UI-04**: Multi-step onboarding screens (steps 1–6, animated transitions)
- [ ] **UI-05**: Final onboarding screen (step 7: video placeholder + habit chat with voice recorder)
- [ ] **UI-06**: Home dashboard (nutrition summary, quick actions, daily goal progress)
- [ ] **UI-07**: Daily check-in screen
- [ ] **UI-08**: Diet plan screen (current plan meals by time of day)
- [ ] **UI-09**: Chat companion screen (conversation history + message input)
- [ ] **UI-10**: Meal analysis screen (enter meal text, view analysis result)
- [ ] **UI-11**: "What should I eat now?" screen (ingredients input, suggestion output)
- [ ] **UI-12**: Progress and weekly report screen
- [ ] **UI-13**: Settings screen (language, profile, account)
- [ ] **UI-14**: Language selector screen
- [ ] **UI-15**: Medical safety / clinical review required state screen (respectful, with path forward)
- [ ] **UI-16**: Mobile-first layout; desktop shows the same mobile view centered with appropriate max-width
- [ ] **UI-17**: Bottom mobile navigation after onboarding is complete
- [ ] **UI-18**: Loading states for all async operations
- [ ] **UI-19**: Empty states for lists/dashboards with no data yet
- [ ] **UI-20**: Error states with user-friendly messages (no raw API errors shown to user)

### Data Models

- [ ] **DATA-01**: `User`, `AuthOTP` models with Alembic migration
- [ ] **DATA-02**: `UserProfile`, `MedicalCondition`, `UserMedicalFlag`, `Medication`, `Allergy` models
- [ ] **DATA-03**: `LifestyleProfile`, `FoodPreference`, `BehaviorProfile` models
- [ ] **DATA-04**: `NutritionGoal`, `NutritionRiskAssessment`, `NutritionPlan`, `NutritionPlanMeal` models
- [ ] **DATA-05**: `MealEntry`, `ChatSession`, `ChatMessage`, `AudioMessage` models
- [ ] **DATA-06**: `DailyCheckIn`, `ProgressEntry`, `WeeklyReport` models
- [ ] **DATA-07**: `UserLanguagePreference`, `AuditLog` models
- [ ] **DATA-08**: All models have `created_at` and `updated_at` timestamps
- [ ] **DATA-09**: All migrations are clean, reversible, and tested on a fresh database

### Progressive Web App (PWA)

- [ ] **PWA-01**: Web app manifest (`manifest.json`) with name, short name, icons (192×192, 512×512, maskable), theme color, background color, `display: standalone`
- [ ] **PWA-02**: Service worker with network-first strategy for API calls and cache-first for static assets; offline fallback page shown when network unavailable
- [ ] **PWA-03**: Install prompt shown at an appropriate moment (after onboarding completion or first meaningful interaction) — not on first load
- [ ] **PWA-04**: Installed PWA launches without browser chrome on mobile; status bar color matches app theme
- [ ] **PWA-05**: All screens work in standalone PWA mode; no broken layout due to missing browser navigation

### OpenClaw AI Integration

- [ ] **OC-01**: `OpenClawProvider` implements `AIProvider` interface using OpenAI-compatible `/chat/completions` endpoint
- [ ] **OC-02**: OpenClaw configuration loaded exclusively from 10 backend environment variables: `OPENCLAW_BASE_URL`, `OPENCLAW_API_KEY`, `OPENCLAW_MODEL`, `OPENCLAW_CHAT_COMPLETIONS_PATH`, `OPENCLAW_TIMEOUT_SECONDS`, `OPENCLAW_MAX_RETRIES`, `OPENCLAW_TEMPERATURE`, `OPENCLAW_MAX_TOKENS`, `OPENCLAW_CONTEXT_MAX_MESSAGES`, `OPENCLAW_CONTEXT_SUMMARY_ENABLED`
- [ ] **OC-03**: All AI endpoints — chat companion, nutrition plan generation, meal analysis, what-to-eat-now, plan adaptation, onboarding assistant chat, habit coaching — route through `OpenClawProvider` when `OPENCLAW_BASE_URL` is set
- [ ] **OC-04**: When `OPENCLAW_BASE_URL` is absent, app falls back to `MockAIProvider` with no crash and no user-facing error
- [ ] **OC-05**: Conversation context respects `OPENCLAW_CONTEXT_MAX_MESSAGES`; oldest messages pruned from history when limit is reached
- [ ] **OC-06**: Timeout and retry logic implemented per `OPENCLAW_TIMEOUT_SECONDS` and `OPENCLAW_MAX_RETRIES`; network errors surface as friendly messages, not raw exceptions
- [ ] **OC-07**: `OPENCLAW_TEMPERATURE` and `OPENCLAW_MAX_TOKENS` passed in every OpenClaw request body
- [ ] **OC-08**: OpenClaw request/response is logged at DEBUG level (not INFO) to avoid leaking user content in production logs

### Conversation Persistence & Nutrition Memory

- [ ] **MEM-01**: `NutritionMemoryContext` struct serialized per user: medical flags, risk level, current plan summary, recent 7-day check-in trends, top 3 behavior patterns — injected into every AI system prompt prefix
- [ ] **MEM-02**: Rolling conversation summary generated when message count exceeds `OPENCLAW_CONTEXT_MAX_MESSAGES` and `OPENCLAW_CONTEXT_SUMMARY_ENABLED=true`
- [ ] **MEM-03**: Rolling summary stored in `ChatSession.summary` field; injected at the top of system prompt context in subsequent sessions — long conversations resume without losing nutrition context
- [ ] **MEM-04**: `ChatSession` model tracks `summary`, `summary_generated_at`, `message_count`; `NutritionMemoryService.build_context()` is the single point of truth for prompt context assembly

### UI Style System

- [ ] **UI-STYLE-01**: Visual aesthetic is muted, pale, and soft — no saturated colors, no aggressive fitness/gym palette; primary palette uses desaturated tones with high readability
- [ ] **UI-STYLE-02**: Layout is app-like, not website-like — no horizontal nav bars at top, no Bootstrap-style card grids, no admin-panel borders or table layouts; uses bottom navigation and full-bleed screens
- [ ] **UI-STYLE-03**: Components use subtle shadows and soft rounded corners (≥ 16px radius on cards) — no hard-bordered boxes, no flat Bootstrap-style panels
- [ ] **UI-STYLE-04**: Typography uses comfortable line height (≥ 1.6), appropriate font size for mobile (≥ 15px body), spacious padding — health app feel, not form-heavy admin tool

### Continuation & Context Files

- [ ] **CONT-01**: Root `PROJECT_STATE.md` maintained with: current phase, last completed feature/commit, what's in progress, known blockers — updated after every meaningful commit so work can resume after `/clear`
- [ ] **CONT-02**: Root `NEXT_STEPS.md` updated after every commit with: exact next action, which file to touch first, which command to run — enables cold-start resumption
- [ ] **CONT-03**: Root `DECISIONS.md` documents every architectural and product decision: what was decided, why, what alternatives were rejected — append-only log
- [ ] **CONT-04**: Root `CHANGELOG.md` updated with every meaningful commit: date, what changed, why — follows Keep a Changelog format

---

## v2 Requirements

### Real Providers (SMS / AI / STT)

- **PROV-01**: Real SMS provider (Kavenegar or similar) integrated for production OTP
- **PROV-02**: Real AI provider (OpenAI, Claude API, etc.) integrated behind `AIProvider` abstraction
- **PROV-03**: Real STT provider (Whisper, Azure Speech, etc.) integrated for audio transcription
- **PROV-04**: STT results surfaced in chat conversation after async processing

### Enhanced Features

- **ENH-01**: Image-based meal analysis (camera or gallery upload)
- **ENH-02**: Restaurant and party guidance mode ("I'm at a restaurant, what should I order?")
- **ENH-03**: Habit coaching conversations (emotional eating, cravings, night snacking, post-slip recovery)
- **ENH-04**: Weekly insight summary pushed to user (email or in-app)
- **ENH-05**: Ramadan / fasting mode with adjusted meal timing and hydration guidance
- **ENH-06**: Persian food nutrition database as seeded fixture (beyond AI knowledge)

### Infrastructure

- **INFRA-V2-01**: Human nutritionist panel (view user profiles and chat history for professional review)
- **INFRA-V2-02**: Background task queue (Celery + Redis) for STT and AI tasks under load
- **INFRA-V2-03**: PostgreSQL migration path (Alembic env already supports this)
- **INFRA-V2-04**: Push notifications (in-app or PWA push)
- **INFRA-V2-05**: Payment / subscription system
- **INFRA-V2-06**: Wearable device integration (steps, sleep data)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Email/password login | Phone OTP only — Persian market norm, lower friction for target users |
| OAuth (Google, GitHub) | Not needed for phone-OTP-only auth in v1 |
| Native iOS / Android app | Web-first (PWA-ready); native app deferred |
| Real SMS provider in v1 | OTP=123456 sufficient for dev/demo; wired in v2 |
| OpenAI/Claude provider in v1 | OpenClaw covers OpenAI-compatible real AI in v1; other provider SDKs are v2 |
| Real STT/transcription in v1 | Audio stored with `status=pending`; STT plugged in v2 |
| Image meal analysis in v1 | Text-only for v1; camera architecture prepared |
| Calorie-counting / macro tracking | Explicitly anti-feature — behavior-centric coaching, not calorie obsession |
| Gamification (points, badges, streaks) | Risk of shallow engagement over sustainable behavior change; defer |
| Social features (sharing, community) | Not relevant to core nutrition companion value |
| Admin/moderator panel | Not needed in v1 |
| Multi-device sync / real-time | Single-user sessions in v1; real-time not required |
| Dark mode | Not blocking v1 launch; can be added without refactor |

---

## Traceability

*(Populated during roadmap creation — 2026-06-03)*

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-02 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-03 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-04 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-05 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-06 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-07 | Phase 1: Infra & Backend Foundation | Pending |
| INFRA-08 | Phase 1: Infra & Backend Foundation | Pending |
| BE-01 | Phase 1: Infra & Backend Foundation | Pending |
| BE-02 | Phase 1: Infra & Backend Foundation | Pending |
| BE-03 | Phase 1: Infra & Backend Foundation | Pending |
| BE-04 | Phase 1: Infra & Backend Foundation | Pending |
| BE-05 | Phase 1: Infra & Backend Foundation | Pending |
| BE-06 | Phase 1: Infra & Backend Foundation | Pending |
| BE-07 | Phase 1: Infra & Backend Foundation | Pending |
| BE-08 | Phase 1: Infra & Backend Foundation | Pending |
| BE-09 | Phase 1: Infra & Backend Foundation | Pending |
| BE-10 | Phase 1: Infra & Backend Foundation | Pending |
| BE-11 | Phase 1: Infra & Backend Foundation | Pending |
| BE-12 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-01 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-02 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-03 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-04 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-05 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-06 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-07 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-08 | Phase 1: Infra & Backend Foundation | Pending |
| DATA-09 | Phase 1: Infra & Backend Foundation | Pending |
| I18N-01 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-02 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-03 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-04 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-05 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-06 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-07 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-08 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-09 | Phase 2: i18n & Frontend Shell | Pending |
| I18N-10 | Phase 2: i18n & Frontend Shell | Pending |
| AUTH-01 | Phase 3: Authentication | Pending |
| AUTH-02 | Phase 3: Authentication | Pending |
| AUTH-03 | Phase 3: Authentication | Pending |
| AUTH-04 | Phase 3: Authentication | Pending |
| AUTH-05 | Phase 3: Authentication | Pending |
| AUTH-06 | Phase 3: Authentication | Pending |
| AUTH-07 | Phase 3: Authentication | Pending |
| AUTH-08 | Phase 3: Authentication | Pending |
| AUTH-09 | Phase 3: Authentication | Pending |
| AUTH-10 | Phase 3: Authentication | Pending |
| UI-01 | Phase 3: Authentication | Pending |
| UI-02 | Phase 3: Authentication | Pending |
| UI-03 | Phase 3: Authentication | Pending |
| OB-01 | Phase 4: Onboarding Backend | Pending |
| OB-02 | Phase 4: Onboarding Backend | Pending |
| OB-03 | Phase 4: Onboarding Backend | Pending |
| OB-04 | Phase 4: Onboarding Backend | Pending |
| OB-05 | Phase 4: Onboarding Backend | Pending |
| OB-06 | Phase 4: Onboarding Backend | Pending |
| OB-07 | Phase 4: Onboarding Backend | Pending |
| OB-13 | Phase 4: Onboarding Backend | Pending |
| NUTR-01 | Phase 4: Onboarding Backend | Pending |
| NUTR-02 | Phase 4: Onboarding Backend | Pending |
| NUTR-03 | Phase 4: Onboarding Backend | Pending |
| NUTR-04 | Phase 4: Onboarding Backend | Pending |
| OB-08 | Phase 5: Onboarding Frontend | Pending |
| OB-09 | Phase 5: Onboarding Frontend | Pending |
| OB-10 | Phase 5: Onboarding Frontend | Pending |
| OB-11 | Phase 5: Onboarding Frontend | Pending |
| OB-12 | Phase 5: Onboarding Frontend | Pending |
| UI-04 | Phase 5: Onboarding Frontend | Pending |
| UI-05 | Phase 5: Onboarding Frontend | Pending |
| AUDIO-01 | Phase 6: Voice & Audio | Pending |
| AUDIO-02 | Phase 6: Voice & Audio | Pending |
| AUDIO-03 | Phase 6: Voice & Audio | Pending |
| AUDIO-04 | Phase 6: Voice & Audio | Pending |
| AUDIO-05 | Phase 6: Voice & Audio | Pending |
| AUDIO-06 | Phase 6: Voice & Audio | Pending |
| AUDIO-07 | Phase 6: Voice & Audio | Pending |
| AUDIO-08 | Phase 6: Voice & Audio | Pending |
| AUDIO-09 | Phase 6: Voice & Audio | Pending |
| AUDIO-10 | Phase 6: Voice & Audio | Pending |
| AUDIO-11 | Phase 6: Voice & Audio | Pending |
| AUDIO-12 | Phase 6: Voice & Audio | Pending |
| AUDIO-13 | Phase 6: Voice & Audio | Pending |
| INFRA-09 | Phase 1: Infra & Backend Foundation | Pending |
| CONT-01 | Phase 1: Infra & Backend Foundation | Pending |
| CONT-02 | Phase 1: Infra & Backend Foundation | Pending |
| CONT-03 | Phase 1: Infra & Backend Foundation | Pending |
| CONT-04 | Phase 1: Infra & Backend Foundation | Pending |
| PWA-01 | Phase 2: i18n & Frontend Shell | Pending |
| PWA-02 | Phase 2: i18n & Frontend Shell | Pending |
| PWA-03 | Phase 2: i18n & Frontend Shell | Pending |
| PWA-04 | Phase 2: i18n & Frontend Shell | Pending |
| PWA-05 | Phase 2: i18n & Frontend Shell | Pending |
| UI-STYLE-01 | Phase 2: i18n & Frontend Shell | Pending |
| UI-STYLE-02 | Phase 2: i18n & Frontend Shell | Pending |
| UI-STYLE-03 | Phase 2: i18n & Frontend Shell | Pending |
| UI-STYLE-04 | Phase 2: i18n & Frontend Shell | Pending |
| NUTR-05 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-06 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-07 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-08 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-09 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-10 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-11 | Phase 7: Nutrition Backend & AI Layer | Pending |
| NUTR-12 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-01 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-02 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-03 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-04 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-05 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-06 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-07 | Phase 7: Nutrition Backend & AI Layer | Pending |
| AI-08 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-01 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-02 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-03 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-04 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-05 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-06 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-07 | Phase 7: Nutrition Backend & AI Layer | Pending |
| OC-08 | Phase 7: Nutrition Backend & AI Layer | Pending |
| MEM-01 | Phase 7: Nutrition Backend & AI Layer | Pending |
| MEM-02 | Phase 7: Nutrition Backend & AI Layer | Pending |
| MEM-03 | Phase 7: Nutrition Backend & AI Layer | Pending |
| MEM-04 | Phase 7: Nutrition Backend & AI Layer | Pending |
| CHAT-01 | Phase 8: Nutrition Frontend & Chat | Pending |
| CHAT-02 | Phase 8: Nutrition Frontend & Chat | Pending |
| CHAT-03 | Phase 8: Nutrition Frontend & Chat | Pending |
| CHAT-04 | Phase 8: Nutrition Frontend & Chat | Pending |
| CHAT-05 | Phase 8: Nutrition Frontend & Chat | Pending |
| CHAT-06 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-06 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-07 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-08 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-09 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-10 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-11 | Phase 8: Nutrition Frontend & Chat | Pending |
| UI-15 | Phase 8: Nutrition Frontend & Chat | Pending |
| PROG-01 | Phase 9: Progress & Reports | Pending |
| PROG-02 | Phase 9: Progress & Reports | Pending |
| PROG-03 | Phase 9: Progress & Reports | Pending |
| PROG-04 | Phase 9: Progress & Reports | Pending |
| PROG-05 | Phase 9: Progress & Reports | Pending |
| UI-12 | Phase 9: Progress & Reports | Pending |
| UI-13 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-14 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-16 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-17 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-18 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-19 | Phase 10: Settings, Polish & Remaining UI | Pending |
| UI-20 | Phase 10: Settings, Polish & Remaining UI | Pending |

**Coverage:**
- v1 requirements: 152 total (126 original + 26 added 2026-06-03: INFRA-09, PWA-01..05, OC-01..08, MEM-01..04, UI-STYLE-01..04, CONT-01..04)
- Mapped to phases: 152
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-03*
*Last updated: 2026-06-03 after PWA, OpenClaw, UI style, conversation memory, and continuation file requirements added*

---
*Requirements defined: 2026-06-03*
*Last updated: 2026-06-03 — traceability populated during roadmap creation*
