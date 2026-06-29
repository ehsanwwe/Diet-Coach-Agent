# Changelog — Diet Coach Agent

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

---

## [1.0.1] - 2026-06-29

### Fixed — Nutrition Agent Quality Fixes

#### Fix 1: Duplicate medical warnings now deduplicated
- `backend/app/services/calendar_service.py` — added `_is_consult_warning()` and `_dedupe_medical_warnings()` helpers; applied in both `generate_week()` and `regenerate_day()` to collapse semantically-equivalent "consult doctor" warnings into a single canonical sentence
- `backend/app/services/prompt_builder.py` — added LLM instruction not to emit medical-consultation warnings (backend injects the canonical one automatically)

#### Fix 2: Meal descriptions now include explicit quantities
- `backend/app/services/mock_ai_provider.py` — updated all 7 days of FA mock data; every meal's `description` and `portion_guidance` now use measurable Persian household units (کف دست، قاشق غذاخوری، کاسه، گرم) — no vague "مقدار مناسب" phrases
- `backend/app/services/prompt_builder.py` — strengthened `for_generate_week_plan()` portion rules to require explicit quantities in `description` field as well as `portion_guidance`; added same rule to `for_generate_plan()`

#### Fix 3: Chat meal substitution now persists to actual stored plan
- `backend/app/repositories/calendar_repository.py` — added `get_meal_by_slot()` (finds meal by slot or type) and `update_meal_fields()` (updates title/description/portion/alternatives in-place)
- `backend/app/services/calendar_service.py` — added `substitute_day_meal()` to replace a single named meal in an existing plan day and return the updated day schema
- `backend/app/services/agent_tools/registry.py` — added `SubstituteMealTool` (tool #12); registered in `build_tool_registry()`
- `backend/app/services/agent_orchestrator.py` — added rule 3b to `_ORCHESTRATOR_SYSTEM`: meal substitution intent triggers `get_calendar` + `substitute_meal`; LLM must craft explicit quantities before calling the tool; after success must show updated meal; "برنامه جدید" request must call `get_calendar` not invent from memory

---

## [1.0.0] - 2026-06-04

### Added — Phase 10: Settings, Polish & Remaining UI

- **Backend:** `PATCH /api/v1/settings/language` — persist user language preference to `UserLanguagePreference` (UI-13, UI-14)
- **Frontend:** `frontend/src/lib/api.ts` — added `api.patch()` method mirroring `api.post()` with `method: 'PATCH'`
- **Frontend:** `SettingsScreen` client component — Language nav row, Profile (phone read-only), Account section with inline logout confirmation (UI-13)
- **Frontend:** `LanguageSelector` client component — writes `NEXT_LOCALE` cookie, fire-and-forget backend persist, navigate to `/${newLocale}/settings/language` (UI-14)
- **Frontend:** `/[lang]/settings` route — AuthGuard + app-container + SettingsScreen + AppBottomNav (UI-16)
- **Frontend:** `/[lang]/settings/language` route — AuthGuard + app-container + LanguageSelector (no nav bar; sub-screen) (UI-16)
- **Frontend:** AppBottomNav settings tab enabled — `active: isActive('settings')`, `disabled: false` (UI-17)
- **Dictionaries:** `settings.*` namespace (12 keys: title, languageSection, profileSection, accountSection, currentLanguage, changeLanguage, displayName, phoneNumber, logoutBtn, logoutConfirm, logoutCancel, appVersion) across fa/en/ar

### Implementation Notes

- Canonical UNAUTHORIZED pattern (`err.message === 'UNAUTHORIZED'` FIRST) adopted in SettingsScreen — consistent with ProgressScreen.tsx line 45
- Phone numbers rendered with `dir="ltr"` — technical identifiers always LTR even in RTL layouts
- Language selector fires `PATCH /api/v1/settings/language` fire-and-forget; cookie is canonical client-side source of truth
- TypeScript strict: 0 errors across all new files

---

## [0.9.0] - 2026-06-04

### Added — Phase 9: Progress & Reports
- **Backend:** `POST /api/v1/progress/check-in` — daily check-in with upsert semantics (PROG-01)
- **Backend:** `GET /api/v1/progress/summary` — progress summary with weight series, behavior wins (8 chips), logging streak (PROG-02, PROG-04)
- **Backend:** `GET /api/v1/progress/weekly-report` — current-week aggregated report with adherence %, averages, focus suggestion (PROG-03)
- **Backend:** Rule-based behavior wins (sleep ≥7h, activity ≥30min, streak ≥3, stress ≤2.5, hunger ≤2.5) + 3 untracked informational chips
- **Backend:** `pytest` test suite — 7/7 tests passing, `StaticPool` for reliable in-memory SQLite tests
- **Frontend:** `/[lang]/progress` authenticated screen (UI-12)
- **Frontend:** `WeightSparkline` — inline SVG sparkline, no external charting library (PROG-05)
- **Frontend:** `CheckInForm` — daily check-in with scale pickers for hunger/stress
- **Frontend:** `ProgressSummary` — weight card with sparkline + behavior win chips + streak
- **Frontend:** `WeeklyReport` — adherence headline, metric rows, sleep/stress note, suggested focus
- **Frontend:** Progress tab enabled in bottom nav (previously disabled)
- **Frontend:** `progress` dictionary namespace (49 keys each in fa/en/ar)
- **Frontend:** `src/types/progress.ts`, `src/lib/progress.ts` — typed API client

## [0.8.0] - 2026-06-03

### Added — Phase 8: Nutrition Frontend & Chat

**Backend — Companion Chat**
- `backend/app/schemas/chat.py` — ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
- `backend/app/repositories/chat_repository.py` — companion session/message DB ops
- `backend/app/services/chat_service.py` — AI chat using NutritionAgentService + NutritionMemoryService
- `backend/app/api/v1/endpoints/chat.py` — POST /chat/message, GET /chat/history (auth-required)
- `backend/app/services/mock_ai_provider.py` — TASK_CHAT constant + Persian mock response
- `backend/app/services/prompt_builder.py` — for_chat_message() with history context
- `backend/app/services/nutrition_agent_service.py` — chat_message() method

**Frontend — Types & Libs**
- `src/types/nutrition.ts`, `src/types/chat.ts` — TypeScript types for all responses
- `src/lib/nutrition.ts` — raw fetch helpers for all 5 nutrition endpoints
- `src/lib/chat.ts` — SuccessResponse-aware chat API helpers
- `src/hooks/useNutritionProfile.ts` — profile fetch hook with 401 redirect

**Frontend — Components**
- `AppBottomNav` — 4-tab nav (home/chat/progress[disabled]/settings[disabled])
- `ClinicalReviewState` — calm professional safety notice (compact + full variants)
- `NutritionDashboard` — dashboard with quick actions, plan summary, risk badge
- `PlanSummary` — full plan with daily guidelines grid + meal list + warnings
- `PlanGenerator` — generate/regenerate button with loading state
- `MealAnalysisForm` — text + meal-time selector + context
- `MealAnalysisResult` — quality score, nutrient details, suggestions, warnings
- `WhatToEatForm` — food tag input, hunger level, time, context
- `WhatToEatResult` — food option cards with tags, reasoning, warnings
- `CompanionChat` — optimistic UI chat with history load + typing indicator
- `ChatBubble`, `ChatComposer` — chat message display + text input

**Frontend — Pages (all AuthGuard-protected)**
- `/[lang]/dashboard` — home screen
- `/[lang]/nutrition/plan` — diet plan + generate
- `/[lang]/nutrition/meal-analysis` — meal analysis flow
- `/[lang]/nutrition/what-to-eat` — what to eat now flow
- `/[lang]/chat` — companion chat screen
- `/[lang]` (splash) — updated with login + dashboard CTAs

**Dictionaries** — fa/en/ar extended with: dashboard, plan, mealAnalysis, whatToEat, companionChat, safety

### Not Implemented (Out of Scope for Phase 8)
- Progress/weekly reports (Phase 9)
- Settings/polish (Phase 10)
- Image meal analysis
- STT transcription
- Voice chat

---

## [0.7.0] - 2026-06-03

### Added — Phase 7: Nutrition Backend & AI Layer

**AI Provider Layer**
- `backend/app/services/ai_provider.py` — AIProvider ABC, AIProviderResult dataclass, `get_ai_provider()` factory
- `backend/app/services/mock_ai_provider.py` — deterministic mock for generate_plan, analyze_meal, what_to_eat_now, adapt_plan (Persian-friendly JSON responses, no external calls)
- `backend/app/services/openclaw_provider.py` — httpx-based OpenAI-compatible provider with configurable retries and fallback

**Prompt & Context Layer**
- `backend/app/services/prompt_builder.py` — builds Persian system+user prompts with TASK:<type> markers, safety notes, cultural context
- `backend/app/services/conversation_context_manager.py` — trims message list to OPENCLAW_CONTEXT_MAX_MESSAGES
- `backend/app/services/nutrition_memory_service.py` — NutritionMemoryContext dataclass; builds compact user context from all DB tables

**Orchestration & Business Logic**
- `backend/app/services/nutrition_agent_service.py` — AI pipeline: prompt → messages → provider → JSON parse with mock fallback
- `backend/app/services/nutrition_service.py` — all 6 endpoint handlers with safety guardrails and DB persistence

**Data Layer**
- `backend/app/schemas/nutrition.py` — Pydantic v2 schemas: NutritionProfileResponse, NutritionPlanResponse, MealAnalyzeRequest/Response, WhatToEatNowRequest/Response, AdaptPlanRequest/Response, DailyGuidelines, MealItem, FoodOption
- `backend/app/repositories/nutrition_repository.py` — NutritionGoal, NutritionPlan, NutritionPlanMeal, MealEntry DB operations
- `backend/alembic/versions/0003_add_nutrition_plan_metadata.py` — adds `plan_metadata` Text column to `nutrition_plans`
- `backend/app/models/nutrition.py` — added `plan_metadata` field

**API**
- `backend/app/api/v1/endpoints/nutrition.py` — 6 authenticated endpoints
- `backend/app/api/v1/router.py` — registered nutrition_router under /nutrition prefix

**Config**
- `backend/app/core/config.py` — added `AI_PROVIDER` setting (default: "mock")
- `backend/.env.example` — added AI_PROVIDER var; updated OpenClaw recommended values

### Safety Behavior
- Clinical-review users receive wellness guidance only (no aggressive plan)
- High-risk users receive wellness reminder in all warning lists
- No body-shaming language in prompts; no medical prescription claims
- is_mock flag in all responses tells frontend when AI is not live

---

## [0.6.0] - 2026-06-03

### Added — Phase 6: Voice & Audio

**Backend**
- `backend/app/schemas/onboarding_chat.py` — Pydantic v2 schemas: TextMessageRequest, ChatMessageOut, TextMessageResponse, AudioUploadResponse, ChatHistoryItem, ChatHistoryResponse
- `backend/app/repositories/onboarding_chat_repository.py` — DB access (get_or_create_onboarding_session, create_text_message, create_audio_message, get_text_messages, get_audio_messages)
- `backend/app/services/audio_storage_service.py` — local file storage with MIME/size validation, UUID-based filenames, storage_key abstraction (no absolute paths to clients)
- `backend/app/services/onboarding_chat_service.py` — send_text_message (placeholder assistant response), upload_audio, get_history
- `backend/app/api/v1/endpoints/onboarding_chat.py` — 3 authenticated endpoints: POST /onboarding/chat/text, POST /onboarding/chat/audio, GET /onboarding/chat/history
- `backend/app/api/v1/router.py` — registered onboarding_chat_router under /onboarding prefix
- `backend/app/core/config.py` — added AUDIO_STORAGE_PATH, MAX_AUDIO_UPLOAD_MB, ALLOWED_AUDIO_MIME_TYPES settings
- `backend/.env.example` — documented 3 new audio env vars
- `.gitignore` — added backend/storage/ to ignored paths

**Frontend**
- `src/types/onboardingChat.ts` — TypeScript types for all 3 chat API endpoints
- `src/lib/onboardingChat.ts` — API client (sendTextMessage, uploadAudio, getChatHistory)
- `src/lib/media.ts` — MIME type detection via MediaRecorder.isTypeSupported, support/availability checks, formatDuration
- `src/hooks/useAudioRecorder.ts` — MediaRecorder hook: state machine (idle/requesting/recording/stopped/error), Web Audio AnalyserNode for waveform, elapsed timer, stream cleanup on unmount
- `src/components/audio/AudioWaveform.tsx` — canvas-based real-time waveform using AnalyserNode.getByteTimeDomainData
- `src/components/audio/AudioPreview.tsx` — audio playback preview with progress bar, play/pause/reset, object URL lifecycle management
- `src/components/audio/AudioRecorder.tsx` — full recorder UI: unsupported/error/idle/recording/stopped states, waveform + timer, cancel/stop/send controls
- `src/components/onboarding/OnboardingHabitChat.tsx` — chat UI: text textarea + send, AudioRecorder integration, history display (text bubbles + audio metadata), loads history on enable
- `src/components/onboarding/steps/FinalVideoStep.tsx` — updated: integrates OnboardingHabitChat enabled after video watched, accepts audioDict prop
- `src/components/onboarding/OnboardingWizard.tsx` — passes dict.audio to FinalVideoStep
- `src/dictionaries/fa.ts` — added audio section (23 keys, Persian)
- `src/dictionaries/en.ts` — added audio section (23 keys, English)
- `src/dictionaries/ar.ts` — added audio section (23 keys, Arabic)

**No new Alembic migration** — ChatSession, ChatMessage, AudioMessage tables already existed from Phase 1 schema

---

## [0.4.0] - 2026-06-03

### Added — Phase 4: Onboarding Backend

**Backend**
- `backend/app/models/user.py` — added `is_onboarded: bool = False` field
- `backend/alembic/versions/0002_add_user_is_onboarded.py` — migration adding `is_onboarded` column to users table
- `backend/app/schemas/onboarding.py` — `ProfileRequest/Response`, `MedicalRequest/Response`, `LifestyleRequest/Response`, `PreferencesRequest/Response`, `BehaviorRequest/Response`, `OnboardingStatusResponse`, `OnboardingCompleteResponse` (Pydantic v2, all list fields with JSON text deserialization)
- `backend/app/schemas/auth.py` — `UserResponse` extended with `is_onboarded` field (auth `/me` endpoint now reflects onboarding state)
- `backend/app/repositories/onboarding_repository.py` — `upsert_profile`, `replace_medical_flags`, `replace_medications`, `replace_allergies`, `upsert_warning_symptoms`, `get_warning_symptoms`, `upsert_lifestyle`, `upsert_food_preference`, `upsert_behavior_profile`, `create_risk_assessment`, `get_latest_risk_assessment`, `set_user_onboarded`
- `backend/app/services/safety_guardrail_service.py` — `assess()` evaluates risk from medical flags, medications, warning symptoms, and age; returns `SafetyAssessment` with `risk_level` (low/medium/high/clinical_review_required) and `flags_triggered`; detects 15+ high-risk patterns; never issues medical prescriptions
- `backend/app/services/onboarding_service.py` — `get_status`, `save_profile`, `save_medical`, `save_lifestyle`, `save_preferences`, `save_behavior`, `complete_onboarding`
- `backend/app/api/v1/endpoints/onboarding.py` — `GET /onboarding/status`, `POST /onboarding/profile`, `POST /onboarding/medical`, `POST /onboarding/lifestyle`, `POST /onboarding/preferences`, `POST /onboarding/behavior`, `POST /onboarding/complete`
- `backend/app/api/v1/router.py` — onboarding router registered at `/onboarding`

### Notes
- All 7 onboarding endpoints require Bearer token (401 if unauthenticated)
- Medical flags upserted per condition code (idempotent); medications/allergies fully replaced on each call
- Warning symptoms stored in sentinel `UserMedicalFlag` row (`condition_code="warning_symptoms"`)
- Safety assessment runs twice: preliminary at `/medical` step (ephemeral), authoritative at `/complete` (stored in `NutritionRiskAssessment`)
- `clinical_review_required` does not block `is_onboarded=True` — app delivers messaging based on stored risk level
- Profile (Step 1) is the only required step for `/complete`; medical/lifestyle/preferences/behavior enrich the profile
- No AI/OpenClaw calls — diet plan generation is Phase 7
- Alembic: `alembic check` confirms schema is fully in sync after migration

---

## [0.3.0] - 2026-06-03

### Added — Phase 3: Authentication

**Backend**
- `backend/app/core/security.py` — `create_access_token()`, `decode_access_token()` using PyJWT 2.x with jti, naive UTC for SQLite
- `backend/app/schemas/auth.py` — `RequestOTPRequest`, `VerifyOTPRequest`, `TokenResponse`, `UserResponse` (Pydantic v2)
- `backend/app/repositories/user_repository.py` — `get_by_phone()`, `get_by_id()`, `create()`
- `backend/app/repositories/auth_repository.py` — `create_otp()` (invalidates prior OTPs), `get_latest_valid_otp()`, `mark_otp_used()`, `add_to_blocklist()`, `is_jti_blocked()`
- `backend/app/services/auth_service.py` — `request_otp()` (mock SMS), `verify_otp()`, `logout()`, `get_current_user()`
- `backend/app/api/dependencies.py` — `AuthContext` dataclass, `get_auth_context()`, `get_current_user()` FastAPI dependencies
- `backend/app/api/v1/endpoints/auth.py` — `POST /auth/request-otp`, `POST /auth/verify-otp`, `POST /auth/logout`, `GET /auth/me`
- `backend/app/core/config.py` — added `OTP_EXPIRE_MINUTES=5`, `SMS_PROVIDER=mock`
- `backend/.env.example` — documented `OTP_EXPIRE_MINUTES`, `SMS_PROVIDER`

**Frontend**
- `frontend/src/types/auth.ts` — `AuthUser`, `TokenResponse`, `ApiSuccess`, `ApiError` TypeScript types
- `frontend/src/lib/storage.ts` — `getToken`, `setToken`, `clearToken`, `getStoredUser`, `setStoredUser` (localStorage abstraction)
- `frontend/src/lib/api.ts` — typed fetch wrapper with `ApiRequestError`, reads `NEXT_PUBLIC_API_BASE_URL`
- `frontend/src/lib/auth.ts` — `requestOtp()`, `verifyOtp()`, `logout()`, `getCurrentUser()` API helpers
- `frontend/src/hooks/useAuth.ts` — `useAuth()` hook: user state, isLoading, isAuthenticated, logout
- `frontend/src/components/auth/PhoneLoginForm.tsx` — phone input, validation, OTP request, redirect to verify
- `frontend/src/components/auth/OtpVerifyForm.tsx` — 6-digit OTP input, 60s countdown, resend, verify → redirect
- `frontend/src/components/auth/AuthGuard.tsx` — route guard: redirects unauthenticated users to login
- `frontend/src/app/[lang]/login/page.tsx` — login screen (Server Component)
- `frontend/src/app/[lang]/login/verify/page.tsx` — OTP verify screen; phone from query param
- Dictionaries (`fa.ts`, `en.ts`, `ar.ts`) extended with `auth` section (18 strings each)

### Notes
- No new Alembic migration — `users`, `auth_otps`, `token_blocklist` were created in Phase 1 schema
- Dev OTP is always `123456` when `ENVIRONMENT=development`; change `SMS_PROVIDER` for production
- Token in localStorage (not httpOnly cookie) — acceptable for mobile PWA; revisit in Phase 10
- `build` passes: 0 TypeScript errors, 4 routes (`/[lang]`, `/[lang]/login`, `/[lang]/login/verify`, `/_not-found`)

---

## [0.2.0] - 2026-06-03

### Added — Phase 2: i18n & Frontend Shell

**i18n infrastructure**
- `frontend/src/dictionaries/fa.ts` — Persian dictionary (defines the `Dictionary` interface as source of truth)
- `frontend/src/dictionaries/en.ts` — English dictionary
- `frontend/src/dictionaries/ar.ts` — Arabic dictionary
- `frontend/src/lib/i18n.ts` — `Locale` type, `SUPPORTED_LOCALES`, `isValidLocale()`, `getDictionary()`, `RTL_LOCALES`
- `frontend/src/lib/direction.ts` — `getDirection()`, `isRTL()`, `getSlideX()`, `getIconFlipClass()`, `getIconFlipStyle()`

**Routing & direction**
- `frontend/src/middleware.ts` — locale detection from cookie + Accept-Language; redirects to `/{locale}/`; sets `NEXT_LOCALE` cookie
- `frontend/src/app/layout.tsx` — reads cookie, sets `<html lang dir>` server-side (zero RTL flicker)
- `frontend/src/app/[lang]/layout.tsx` — validates locale param, 404s on unknown locales, generates static params
- `frontend/src/app/[lang]/page.tsx` — app-like mobile splash: icon, app name, tagline, description, coming-soon badge, language switcher

**Style system**
- `frontend/src/app/globals.css` — muted/pale brand palette via Tailwind v4 `@theme {}`, `.app-container` (mobile max-width centered), `.pb-safe`, `.pt-safe`, logical property defaults

**PWA**
- `frontend/public/manifest.json` — name, description, icons (SVG), start_url `/fa`, display standalone
- `frontend/public/sw.js` — install/activate/fetch lifecycle; offline fallback via `/offline.html`
- `frontend/public/offline.html` — standalone offline page with brand styles (no external deps)
- `frontend/public/icons/icon.svg` — leaf/sprout icon, scalable SVG placeholder (PNGs in Phase 10)
- `frontend/src/components/service-worker.tsx` — client component that registers SW on first load

**Config**
- `frontend/next.config.ts` — Cache-Control headers for `sw.js` and `manifest.json`
- `frontend/.env.example` — added `NEXT_PUBLIC_APP_NAME`, `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_DEFAULT_LOCALE`, `NEXT_PUBLIC_SUPPORTED_LOCALES`, `NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS`

### Notes
- No physical Tailwind classes used (no `pl-`, `pr-`, `ml-`, `mr-`) — all spacing via logical properties (`ps-`, `pe-`, `ms-`, `me-`)
- All i18n strings served from server-side dictionary; zero client bundle impact
- TypeScript strict mode: no `any` types, all components fully typed
- Build: `npm run build` passes with zero TypeScript errors; one deprecation warning (middleware.ts → proxy.ts in Next.js 16, deferred to Phase 10)

---

## [0.1.0] - 2026-06-03

### Added — Phase 1: Infra & Backend Foundation

**Backend**
- Monorepo structure: `backend/` and `frontend/` directories established
- `backend/pyproject.toml` with all required dependencies (FastAPI, SQLAlchemy 2.x, Alembic, PyJWT, pydantic-settings)
- `backend/app/core/config.py`: pydantic-settings BaseSettings with SECRET_KEY validation and all 10 OPENCLAW_* vars
- `backend/app/core/database.py`: SQLAlchemy 2.x sync engine, `get_session()` FastAPI dependency, `DeclarativeBase`
- `backend/app/core/errors.py`: consistent `{"status", "message", "detail"}` error response helpers
- All 22 ORM models with `lazy="raise"` on all relationships, UUID PKs, created_at/updated_at
- Alembic migration environment with `render_as_batch=True` + `compare_type=True` (SQLite DDL safety)
- Initial migration `0001_initial_schema.py` covering all 22 tables
- FastAPI app factory with CORS from environment, global error handlers, modular directory structure
- `/api/v1/health` endpoint returning `{"status": "ok"}`
- `backend/.env.example` documenting all env vars including all 10 OPENCLAW_* vars
- `backend/README.md` with setup, migration commands, technology notes

**Frontend**
- Next.js 16 skeleton with App Router `src/app/[lang]/` structure
- Tailwind CSS v4 with `@tailwindcss/postcss` PostCSS plugin
- TypeScript strict mode enabled
- `frontend/.env.example` documenting frontend env vars
- `frontend/README.md` with setup guide

**Repository**
- `.gitignore` covering SQLite files, env files, uploads, caches
- Root `.env.example` with cross-service documentation linking to service examples

### Notes
- `lazy="raise"` on all ORM relationships: accessing any relationship outside a session raises MissingGreenlet/DetachedInstanceError
- `render_as_batch=True` in BOTH alembic/env.py context.configure() calls — required for all future SQLite DDL
- SECRET_KEY absent causes server to refuse startup with clear error message

---

## [Unreleased]

### Planned
- Phase 1: Infra & Backend Foundation
- Phase 2: i18n & Frontend Shell (PWA, RTL, UI style system)
- Phase 3: Authentication
- Phase 4: Onboarding Backend
- Phase 5: Onboarding Frontend
- Phase 6: Voice & Audio
- Phase 7: Nutrition Backend & AI Layer (OpenClaw + MockAI + conversation memory)
- Phase 8: Nutrition Frontend & Chat
- Phase 9: Progress & Reports
- Phase 10: Settings, Polish & Remaining UI

---

## [0.0.2] — 2026-06-03

### Added
- PWA requirements: manifest, service worker, offline fallback, install prompt (PWA-01..05)
- OpenClaw AI integration requirements: OpenAI-compatible provider, 10 OPENCLAW_* env vars (OC-01..08)
- Conversation persistence and rolling summaries requirements (MEM-01..04)
- UI Style System requirements: muted/pale/app-like aesthetic (UI-STYLE-01..04)
- Continuation files requirements: PROJECT_STATE.md, NEXT_STEPS.md, DECISIONS.md, CHANGELOG.md (CONT-01..04)
- Root `.env.example` requirement (INFRA-09)
- `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md` initialized at repo root
- Phase 1 now includes OPENCLAW_* env var documentation, continuation file creation
- Phase 2 now includes PWA setup and UI style system establishment
- Phase 7 now includes OpenClawProvider, rolling summaries, NutritionMemoryContext
- Total requirements: 126 → 152

### Changed
- REQUIREMENTS.md: INFRA-03 updated to include OPENCLAW_* vars
- REQUIREMENTS.md: Out of Scope updated (OpenAI/Claude SDK → v2; OpenClaw is v1)
- ROADMAP.md: Phases 1, 2, 7 updated with new requirements and success criteria
- PROJECT.md: Active requirements, Constraints, Key Decisions updated
- CLAUDE.md: OpenClaw config, UI style, PWA, and continuation file update protocol added
- STATE.md: New decisions appended

---

## [0.0.1] — 2026-06-03

### Added
- GSD project initialization: config.json, PROJECT.md, research (STACK/FEATURES/ARCHITECTURE/PITFALLS/SUMMARY), REQUIREMENTS.md (126 requirements), ROADMAP.md (10 phases), STATE.md, CLAUDE.md
- Technology stack decisions: FastAPI 0.136.x, SQLAlchemy 2.x (sync), Alembic, Next.js 16, Tailwind v4, Zustand, Framer Motion, PyJWT
- 10-phase roadmap covering infra, i18n/RTL, auth, onboarding (backend + frontend), voice/audio, AI/nutrition backend, nutrition frontend/chat, progress/reports, polish

## [] feat(chat): persist draft and assistant response state
- Added status/client_message_id/error_message to chat_messages (migration 0009)
- Pending assistant placeholder committed before AI runs; GET /history shows thinking state immediately
- Idempotency: duplicate client_message_id returns existing response without creating extra rows
- Frontend: draft stored in localStorage (keyed by user ID), cleared only on send success
- Frontend: polling loop (2s) recovers pending state after navigation or refresh
- 4 new backend tests; all 11 chat tests pass
