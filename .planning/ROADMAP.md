# Roadmap: Diet Coach Agent

## Overview

The Diet Coach Agent is built in strict dependency order: infrastructure and database foundations with critical SQLite/ORM safeguards baked in from the start, then an i18n and frontend shell so RTL is never retrofitted, then authentication, then the full onboarding wizard (which generates every piece of profile data the AI layer depends on), then the AI and nutrition services, then voice and audio, then the chat companion, then progress and reporting, and finally settings and UI polish across all 16 screens. Each phase delivers a coherent, testable capability before the next phase begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Infra & Backend Foundation** - Monorepo, FastAPI app, SQLAlchemy 2.x with lazy="raise", Alembic with render_as_batch=True, all ORM models, and project tooling
- [ ] **Phase 2: i18n & Frontend Shell** - Next.js skeleton, Tailwind v4 CSS logical properties baseline, fa/en/ar dictionaries, RTL direction from cookie, and direction-aware utilities
- [ ] **Phase 3: Authentication** - Phone OTP flow, JWT with jti revocation table, auth frontend screens, and protected route guards
- [ ] **Phase 4: Onboarding Backend** - All 7-step onboarding APIs, medical flag detection, SafetyGuardrailService as FastAPI Depends(), and NutritionProfile creation
- [ ] **Phase 5: Onboarding Frontend** - Animated 7-step wizard, direction-aware slide transitions, React Hook Form + Zod validation, video gate, and onboarding chat text input
- [ ] **Phase 6: Voice & Audio** - MediaRecorder with MIME type detection, Web Audio waveform visualizer, recording controls, audio upload, and AudioMessage backend
- [ ] **Phase 7: Nutrition Backend & AI Layer** - AIProvider ABC, MockAIProvider with 20+ Persian variants, NutritionMemoryService, PromptBuilder, NutritionAgentService, and all nutrition endpoints
- [ ] **Phase 8: Nutrition Frontend & Chat** - Home dashboard, chat companion screen, meal analysis, "what to eat now", diet plan screen, and medical safety screen
- [x] **Phase 9: Progress & Reports** - Daily check-in, progress summary, weekly report, and behavior-centric progress dashboard (completed 2026-06-03)
- [ ] **Phase 10: Settings, Polish & Remaining UI** - Settings screen, language selector, mobile nav, loading/empty/error states, and full UI polish pass

## Phase Details

### Phase 1: Infra & Backend Foundation
**Goal**: The monorepo skeleton and backend engine exist with all critical safeguards — render_as_batch=True in Alembic, lazy="raise" on all ORM relationships, all 22 data models migrated cleanly against a blank SQLite database, FastAPI app factory running, all three env example files (root + backend + frontend) with all 10 OPENCLAW_* vars documented, and all four continuation files (PROJECT_STATE.md, NEXT_STEPS.md, DECISIONS.md, CHANGELOG.md) initialized at repository root.
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08, INFRA-09, BE-01, BE-02, BE-03, BE-04, BE-05, BE-06, BE-07, BE-08, BE-09, BE-10, BE-11, BE-12, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, CONT-01, CONT-02, CONT-03, CONT-04
**Success Criteria** (what must be TRUE):
  1. Running `uvicorn app.main:app` from `backend/` starts the server and `/docs` returns OpenAPI UI with no errors
  2. Running `alembic upgrade head` on a blank database creates all tables without error and is reversible with `alembic downgrade base`
  3. All ORM relationships raise an error if accessed outside a session (lazy="raise" is enforced)
  4. `SECRET_KEY` absent from environment causes backend to refuse startup with a clear error message; `backend/.env.example` lists all 10 `OPENCLAW_*` variables with descriptions
  5. `npm run dev` from `frontend/` starts the Next.js dev server (skeleton, no features yet); root `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, and `CHANGELOG.md` exist and are populated
**Plans**: 8 plans
Plans:
- [ ] 01-01-PLAN.md — Monorepo skeleton and .gitignore
- [ ] 01-02-PLAN.md — Backend pyproject.toml and core modules (config, database, errors)
- [ ] 01-03-PLAN.md — ORM models Group 1 (User core) and Group 2 (Profile)
- [ ] 01-04-PLAN.md — ORM models Groups 3-6 (Lifestyle, Nutrition, Chat, Progress)
- [ ] 01-05-PLAN.md — Alembic setup and initial migration (all 22 tables)
- [ ] 01-06-PLAN.md — FastAPI app factory, routers, schemas, startup validation
- [ ] 01-07-PLAN.md — Next.js 16 frontend skeleton and Tailwind v4
- [ ] 01-08-PLAN.md — Env example files, README files, continuation files

### Phase 2: i18n & Frontend Shell
**Goal**: The frontend has a complete i18n foundation — fa/en/ar dictionaries with full coverage, document direction set server-side from cookie with zero RTL flicker, all CSS using Tailwind v4 logical properties (never pl-/pr-/ml-/mr-), direction-aware utilities for icons and animations, PWA manifest + service worker + offline fallback, and the muted/pale/app-like visual style system established — all before any feature screen is built.
**Depends on**: Phase 1
**Requirements**: I18N-01, I18N-02, I18N-03, I18N-04, I18N-05, I18N-06, I18N-07, I18N-08, I18N-09, I18N-10, PWA-01, PWA-02, PWA-03, PWA-04, PWA-05, UI-STYLE-01, UI-STYLE-02, UI-STYLE-03, UI-STYLE-04
**Success Criteria** (what must be TRUE):
  1. Loading the app with `?lang=fa` (or Persian cookie) renders the root layout with `dir="rtl"` on the `<html>` tag — no direction flicker on load
  2. Loading with `?lang=en` renders `dir="ltr"` with English text; switching language live updates direction without full page reload
  3. The app can be installed as a PWA on mobile (manifest valid, service worker registered, offline fallback visible when offline)
  4. A chevron icon in the direction-aware utility points left in LTR and right in RTL (mirrors correctly); no component file contains `pl-`, `pr-`, `ml-`, or `mr-` Tailwind classes
  5. The shell screen uses the muted/pale/app-like style system — soft colors, rounded cards, bottom-nav layout, comfortable typography; does not resemble a website or admin panel
**Plans**: TBD
**UI hint**: yes

### Phase 3: Authentication
**Goal**: Users can authenticate via phone OTP — request OTP, verify with 123456 in dev, receive a JWT, stay logged in across sessions, and log out with server-side token invalidation via the jti revocation table. Auth screens (login, verify OTP) are complete with route guards protecting all post-auth pages.
**Depends on**: Phase 2
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07, AUTH-08, AUTH-09, AUTH-10, UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):
  1. User can enter a phone number on the login screen, receive OTP (dev: 123456), enter it on the verify screen, and land on a protected page — all in one flow
  2. Refreshing a protected page after login keeps the user logged in (JWT persisted correctly)
  3. Logging out invalidates the token server-side — reusing the old JWT on any endpoint returns 401
  4. Visiting a protected route while unauthenticated redirects to the login screen
  5. Splash screen renders with app name and entry CTA; login and OTP screens use all i18n strings with no hard-coded text
**Plans**: TBD
**UI hint**: yes

### Phase 4: Onboarding Backend
**Goal**: All 7 onboarding steps have working backend APIs — profile, medical conditions with UserMedicalFlag population, lifestyle, food preferences, behavior profile, and completion. SafetyGuardrailService is implemented as a FastAPI Depends() and correctly assigns risk_level including clinical_review_required. Onboarding state is resumable from the last completed step.
**Depends on**: Phase 3
**Requirements**: OB-01, OB-02, OB-03, OB-04, OB-05, OB-06, OB-07, OB-13, NUTR-01, NUTR-02, NUTR-03, NUTR-04
**Success Criteria** (what must be TRUE):
  1. A user who completes all 7 steps via API has a NutritionProfile created with all fields populated and risk_level assigned
  2. A user with diabetes + medication in step 3 medical screening has risk_level = "clinical_review_required" after completion
  3. GET /api/v1/onboarding/status returns the correct current step for a user who partially completed onboarding and restarted
  4. SafetyGuardrailService is wired as a FastAPI Depends() — it cannot be bypassed by calling a route without it
  5. All onboarding endpoints return 401 for unauthenticated requests and 422 with descriptive validation errors for bad payloads
**Plans**: TBD

### Phase 5: Onboarding Frontend
**Goal**: The 7-step animated onboarding wizard is complete — direction-aware slide transitions driven by a Zustand direction field, React Hook Form + Zod validation on all steps, video placeholder on step 7 with chat disabled until "watched", and the entire flow works end-to-end calling the Phase 4 backend APIs. Partial progress survives browser close via sessionStorage.
**Depends on**: Phase 4
**Requirements**: OB-08, OB-09, OB-10, OB-11, OB-12, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. Navigating forward through steps slides in the natural direction for the current locale (left-to-right for LTR, right-to-left for RTL); pressing back reverses the animation
  2. Submitting a step with invalid data shows inline validation errors without advancing the step
  3. Closing the browser mid-onboarding and reopening resumes from the last saved step (sessionStorage + backend status)
  4. Step 7 renders a video placeholder component; the chat input below it is disabled until "Mark as watched" is clicked in dev mode
  5. Completing all 7 steps calls POST /api/v1/onboarding/complete and routes the user to the home dashboard
**Plans**: TBD
**UI hint**: yes

### Phase 6: Voice & Audio
**Goal**: The onboarding step 7 chat supports voice recording — MediaRecorder with MIME type auto-detection (audio/mp4 for iOS, audio/webm;codecs=opus for Chrome), a real-time waveform visualizer using Web Audio API AnalyserNode, elapsed timer, preview before send, and audio upload to backend creating an AudioMessage record. Unsupported browsers fall back to text-only gracefully.
**Depends on**: Phase 5
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04, AUDIO-05, AUDIO-06, AUDIO-07, AUDIO-08, AUDIO-09, AUDIO-10, AUDIO-11, AUDIO-12, AUDIO-13
**Success Criteria** (what must be TRUE):
  1. Starting a recording on Chrome shows an animated waveform and an incrementing elapsed timer; stopping produces a playable audio preview
  2. Sending the audio preview uploads to the backend via multipart/form-data and creates an AudioMessage with transcription_status = "not_configured"
  3. Recording on iOS Safari uses audio/mp4 MIME type (detected via isTypeSupported, not hard-coded)
  4. Opening the voice recorder in a browser that does not support MediaRecorder shows a text-only fallback with a user-friendly message
  5. Denying microphone permission triggers a user-friendly explanation message (not a raw browser error)
**Plans**: TBD
**UI hint**: yes

### Phase 7: Nutrition Backend & AI Layer
**Goal**: The full AI nutrition layer is operational — AIProvider ABC with OpenClawProvider (OpenAI-compatible) and MockAIProvider fallback, NutritionMemoryService building structured NutritionMemoryContext and injecting it into every system prompt, PromptBuilder with token-safe history pruning, rolling conversation summaries when OPENCLAW_CONTEXT_SUMMARY_ENABLED=true, NutritionAgentService orchestrating the full call, SafetyGuardrailService injected on every AI endpoint, and all 6 nutrition endpoints working end-to-end.
**Depends on**: Phase 4
**Requirements**: NUTR-05, NUTR-06, NUTR-07, NUTR-08, NUTR-09, NUTR-10, NUTR-11, NUTR-12, AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-07, AI-08, OC-01, OC-02, OC-03, OC-04, OC-05, OC-06, OC-07, OC-08, MEM-01, MEM-02, MEM-03, MEM-04
**Success Criteria** (what must be TRUE):
  1. With `OPENCLAW_BASE_URL` set and a valid OpenAI-compatible endpoint, POST /api/v1/nutrition/plan/generate calls the real AI and returns a plan; with it unset, MockAIProvider returns a deterministic response — both paths produce the same response structure
  2. A user with clinical_review_required risk level hitting any AI endpoint receives the clinical review response — not a plan, regardless of provider
  3. POST /api/v1/nutrition/what-to-eat-now with "برنج و مرغ" (rice and chicken) returns 2–3 suggestions referencing recognizable Iranian meal options (via mock or real OpenClaw)
  4. After `OPENCLAW_CONTEXT_MAX_MESSAGES` messages, the next request includes a rolling summary instead of full history; `ChatSession.summary` is populated when `OPENCLAW_CONTEXT_SUMMARY_ENABLED=true`
  5. All 10 OPENCLAW_* env vars are loaded via pydantic-settings; OpenClaw request logs appear at DEBUG level only (no user content in INFO logs)
**Plans**: TBD

### Phase 8: Nutrition Frontend & Chat
**Goal**: Users can interact with their nutrition plan and AI companion through a complete set of screens — home dashboard with daily goal progress, diet plan view, meal analysis input, "what to eat now" screen, chat companion with conversation history and smooth send UX, and the medical safety / clinical review required screen. Audio input in chat is architecturally prepared with a UI placeholder.
**Depends on**: Phase 7
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, NUTR-05, UI-06, UI-07, UI-08, UI-09, UI-10, UI-11, UI-15
**Success Criteria** (what must be TRUE):
  1. A logged-in user with a completed onboarding sees a populated home dashboard showing their current nutrition goal and a quick action to chat or log a meal
  2. Sending a message in the chat companion screen shows the message in the thread, triggers a loading indicator, and displays the AI reply when it arrives
  3. Entering a meal description in meal analysis returns a quality breakdown (protein, fiber, sugar, balance notes) — not just a calorie count
  4. A user whose risk_level is clinical_review_required sees the respectful clinical review screen (not a blank page or error) with a clear path forward
  5. The chat screen shows a voice input placeholder button that is visible but disabled (or "coming soon") — the architecture is prepared without being broken
**Plans**: TBD
**UI hint**: yes

### Phase 9: Progress & Reports
**Goal**: Users can track their wellness journey through a behavior-centric progress system — daily check-in form capturing weight, hunger, sleep, stress, activity, and adherence notes; a progress summary with weight trend shown as a sparkline; and a weekly report with adherence trend, hunger pattern, sleep/stress correlation, and suggested next-week focus. Dashboard emphasizes behavior wins, not only weight.
**Depends on**: Phase 8
**Requirements**: PROG-01, PROG-02, PROG-03, PROG-04, PROG-05, UI-12
**Success Criteria** (what must be TRUE):
  1. User can submit a daily check-in with all fields and see it reflected in the progress summary immediately
  2. The progress dashboard shows behavior wins (protein, fiber, water, sleep, movement, logging consistency) alongside weight — not only a weight number
  3. After 7 days of check-ins, GET /api/v1/progress/weekly-report returns a report with weight trend, adherence trend, and a suggested next-week focus
  4. Weight trend is displayed as a sparkline or mini-chart (not just a raw number) on the progress screen
  5. The progress screen handles the empty state (no check-ins yet) with a helpful prompt, not a blank or broken layout
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Backend: pytest scaffold, schemas, repository, service, endpoints, router registration (PROG-01, PROG-02, PROG-03)
- [x] 09-02-PLAN.md — Frontend contract: types, lib client, fa/en/ar dictionary additions
- [x] 09-03-PLAN.md — Frontend implementation: sparkline, check-in form, summary view, weekly report, progress screen, bottom-nav enable (PROG-04, PROG-05, UI-12)
**UI hint**: yes

### Phase 10: Settings, Polish & Remaining UI
**Goal**: The application is complete and production-quality — settings screen with language and profile options, language selector screen, bottom mobile navigation, and consistent loading/empty/error states across all screens. The full UI is audited for RTL correctness, mobile viewport safety (dvh + safe-area-inset), and zero hard-coded text. All 16 screens are functional and polished.
**Depends on**: Phase 9
**Requirements**: UI-13, UI-14, UI-16, UI-17, UI-18, UI-19, UI-20
**Success Criteria** (what must be TRUE):
  1. Every async operation across all screens shows a loading indicator — no screen ever appears broken during a pending API call
  2. Every list or dashboard with no data shows a friendly empty state with contextual guidance (not a blank region)
  3. Every API error is surfaced as a user-friendly message — no raw error codes or stack traces appear to the user
  4. The language selector screen allows switching between fa/en/ar with live direction update and persists the choice across sessions
  5. On mobile, the bottom navigation bar is visible after onboarding completes; the desktop layout shows the same mobile view centered with max-width
**Plans**: 3 plans
Plans:
- [ ] 10-01-PLAN.md — Dictionary settings.* namespace + backend PATCH /api/v1/settings/language endpoint (UI-13, UI-14 foundation)
- [ ] 10-02-PLAN.md — Polish pass: dictionary-mapped errors + loading/empty/error state audit across 7 existing screens (UI-18, UI-19, UI-20)
- [ ] 10-03-PLAN.md — SettingsScreen + LanguageSelector + enable bottom-nav settings tab (UI-13, UI-14, UI-16, UI-17)
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infra & Backend Foundation | 0/8 | In progress | - |
| 2. i18n & Frontend Shell | 0/TBD | Not started | - |
| 3. Authentication | 0/TBD | Not started | - |
| 4. Onboarding Backend | 0/TBD | Not started | - |
| 5. Onboarding Frontend | 0/TBD | Not started | - |
| 6. Voice & Audio | 0/TBD | Not started | - |
| 7. Nutrition Backend & AI Layer | 0/TBD | Not started | - |
| 8. Nutrition Frontend & Chat | 0/TBD | Not started | - |
| 9. Progress & Reports | 3/3 | Complete   | 2026-06-03 |
| 10. Settings, Polish & Remaining UI | 0/3 | Not started | - |
