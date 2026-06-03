# Project Research Summary

**Project:** Diet Coach Agent
**Domain:** AI-powered multilingual nutrition coaching web app (Persian-first, RTL-native, mobile PWA)
**Researched:** 2026-06-03
**Confidence:** HIGH (core stack and architecture verified against official docs; MEDIUM on Persian market specifics and medical guardrail adequacy)

## Executive Summary

The Diet Coach Agent is a mobile-first AI nutrition companion built for Persian-speaking users, with full RTL support and cultural awareness for Iranian food patterns. Expert implementations of this class of product follow a layered architecture: a FastAPI backend with a clean Router-Service-Repository separation, a pluggable AI abstraction layer (mock-first), and a Next.js App Router frontend using dictionary-based i18n and Tailwind CSS v4 logical properties for automatic RTL handling. The 7-step onboarding wizard, phone OTP auth, and daily coaching loop are the structural backbone -- everything else depends on these being solid.

The recommended approach is to build in strict dependency order: infrastructure and database foundations first, then auth, then onboarding (which generates the profile data all AI features depend on), then the AI layer, then chat and voice, then progress reporting, and finally polish. The AI abstraction layer must be built from day one with a MockAIProvider so the entire application runs end-to-end without a live API key. This is not premature generalization -- it is the only way to develop and test the full product stack without external dependencies. RTL layout must also be treated as a foundation concern, not a polish step; retrofitting physical CSS properties into logical ones after components are built is three times the work.

The primary risks are: (1) RTL layout breakage from physical CSS slipping into components -- mitigated by using Tailwind v4 logical utilities (ms-, me-, ps-, pe-) from day one; (2) SQLAlchemy async lazy loading causing DetachedInstanceError -- mitigated by lazy=raise and explicit selectinload(); (3) medical safety guardrails enforced only in plan generation and silently bypassed in chat -- mitigated by making SafetyGuardrailService a FastAPI dependency injected into every AI-generating endpoint; (4) Alembic migrations corrupting SQLite without render_as_batch=True -- configure before first migration.

---

## Key Findings

### Recommended Stack

The backend is Python 3.12 + FastAPI 0.136.x with Pydantic v2, SQLAlchemy 2.x 2.0-style (select() + session.execute()), Alembic 1.13.x, and PyJWT 2.x (not python-jose). The frontend is Next.js 16.x App Router, React 19.x, TypeScript 5.x strict mode, Tailwind CSS v4 (CSS logical properties by default -- critical for RTL), Zustand 4.x, and React Hook Form 7.x + Zod 3.x. Audio uses only native browser APIs (MediaRecorder + Web Audio API AnalyserNode). Dictionary-based i18n (fa.ts, en.ts, ar.ts) was chosen over next-intl or i18next for full control and zero vendor lock-in.

**Core technologies:**
- FastAPI 0.136.x: REST API framework -- native async, Pydantic v2 integration, dependency injection for auth guards and service injection
- SQLAlchemy 2.x + Alembic 1.13.x: ORM + migrations -- 2.0-style mandatory; enables SQLite-to-PostgreSQL upgrade path without code changes
- PyJWT 2.x: JWT encode/decode -- FastAPI recommended library as of 2025; replaces unmaintained python-jose
- Next.js 16.x App Router: React framework -- Server Components, file-system routing maps to 16-screen structure
- Tailwind CSS v4: Styling -- CSS logical properties built-in, eliminating rtl: plugin complexity from v3
- Zustand 4.x: Client state -- no Provider boilerplate, works with App Router, handles recording state machine
- Framer Motion 11.x: Animations -- direction-aware slide transitions for RTL/LTR onboarding require programmatic control
- MediaRecorder API + Web Audio API (browser built-in): Voice recording + waveform visualization -- no external library needed

### Expected Features

**Must have (table stakes) -- v1:**
- Phone OTP auth -- Persian market uses phone number as primary identity; email/password is a friction point
- 7-step onboarding with medical screening -- without deep personalization the product is a generic diet PDF
- Medical safety guardrails (clinical_review_required gate) -- legal defensibility and user trust; never optional for a health app
- AI-generated personalized nutrition plan (mock AI in v1) -- core value proposition
- Persian food vocabulary -- Iranian dishes (ghormeh sabzi, ash, doogh, chelokabab, adasi) must be in AI food knowledge
- Full RTL + i18n -- Persian and Arabic speakers will not tolerate broken LTR layouts; this is a quality signal
- Daily check-in loop -- users need a feedback mechanism to feel the product is dynamic, not a static form
- Contextual meal suggestion (what to eat now) -- real-time coaching differentiates from a diet plan PDF
- Conversational chat companion -- users expect to talk to an AI coach
- Progress dashboard (behavior-centric, not weight-only) -- weight-only dashboards drive abandonment at plateau weeks
- Voice recording in onboarding chat (MediaRecorder, STT deferred) -- architecture in place for v1

**Should have (differentiators):**
- Behavior-aware coaching from onboarding step 6 (emotional eating, night eating, binge history)
- PCOS-specific goal path -- Iran has among the highest PCOS rates globally; market-critical differentiator
- Direction-aware animations in onboarding -- signals native quality to Persian users; almost no competitor does this
- Culturally-aware Persian tone in AI responses -- translated English prompts are insufficient
- Risk stratification with clear clinical referral path -- builds trust rather than blocking users at a wall
- Waveform visualizer for voice recording -- trust signal the app is listening

**Defer to v2+:**
- Real STT/transcription for Persian (architecture prepared in v1)
- Real AI provider wiring (mock AI ships first; no code changes needed to wire real provider)
- Adaptive plan modification using weekly report signals
- Ramadan/fasting mode, push notifications, native app, barcode scanning, wearable integration

### Architecture Approach

The backend follows strict three-layer separation: Routers handle HTTP surface and Pydantic validation; Services hold all business logic and AI orchestration; Repositories contain all SQLAlchemy query logic. Routers never call Repositories directly -- bypassing services silently skips SafetyGuardrailService, which is a safety violation. The AI layer uses an Abstract Base Class (AIProvider) with MockProvider shipping in v1. NutritionMemoryService assembles structured context (profile snapshot + medical flags + behavior profile + last N messages) for every AI call, ensuring medical context is always in the system prompt. The frontend uses Zustand stores as state source of truth with a typed API client layer -- components never call fetch() directly.

**Major components:**
1. SafetyGuardrailService (backend) -- evaluates medical flags, assigns risk level; must be injected into every AI-generating endpoint, never bypassed
2. NutritionMemoryService (backend) -- assembles AI context: profile + medical + behavior + recent messages; prevents token-limit-induced guardrail loss
3. AIProvider ABC + MockProvider (backend) -- pluggable AI abstraction; MockProvider enables full end-to-end development with no API key
4. onboardingStore + useOnboarding hook (frontend) -- tracks step, direction, and stepData; drives direction-aware Framer Motion animations
5. i18n layer with getDir() (frontend) -- dictionary-based translation, dir applied at html level server-side from cookie

### Critical Pitfalls

1. **SQLAlchemy async lazy loading causes DetachedInstanceError** -- Set lazy=raise on all relationships from the first model commit; use selectinload() explicitly; convert to Pydantic schemas inside session context.

2. **Alembic + SQLite: ALTER TABLE silently corrupts schema** -- Set render_as_batch=True in env.py before writing any migration; add server_default on non-nullable columns; test alembic upgrade head on blank DB in CI.

3. **RTL layout broken by physical CSS properties** -- Use only Tailwind v4 logical-property utilities (ms-, me-, ps-, pe-) from the first component; add ESLint rule flagging ml-, mr-, pl-, pr-; render dir server-side from cookie.

4. **Medical guardrail checked only at plan generation, not in chat** -- SafetyGuardrailService.assess_risk() must be a FastAPI dependency injected into every AI-output endpoint; log every evaluation in AuditLog.

5. **Onboarding state lost on browser refresh** -- Persist step data to sessionStorage; use URL-based step navigation; track step completion in backend via step endpoints.

6. **AI context window overflow silently drops safety system prompt** -- PromptBuilder must token-count history and truncate from oldest messages; medical flags must always be in system prompt, never in conversation history.

7. **MediaRecorder cross-browser MIME type mismatch** -- Use MediaRecorder.isTypeSupported() to select MIME type priority; store MIME type in AudioMessage; test on real iOS Safari.

---

## Implications for Roadmap

The architecture research defines a clear 6-tier build order based on hard dependencies. The following phase structure maps directly to that tier ordering.

### Phase 1: Infrastructure and Foundations
**Rationale:** Every subsequent phase depends on this. Database models, FastAPI app factory, Alembic with render_as_batch=True, Next.js skeleton, Tailwind v4 with logical properties baseline, and the i18n layer must all exist before any feature is built. Setting up i18n here is critical -- retrofitting RTL is 3x the work.
**Delivers:** Monorepo structure, both app skeletons running locally, all ORM models defined, first Alembic migration applying cleanly against a blank DB, i18n dictionaries with useTranslation() and getDir(), root layout setting dir/lang from cookie server-side.
**Avoids:** Alembic SQLite corruption (Pitfall 2), RTL physical CSS properties (Pitfall 4), locale-in-React-context server-component failure

### Phase 2: Authentication
**Rationale:** Auth is a prerequisite for every user-scoped feature. JWT revocation must be implemented correctly from the start -- health data sensitivity demands it.
**Delivers:** request-otp + verify-otp + me + logout endpoints, dev OTP 123456, JWT with jti claim and server-side revocation, login/verify frontend pages, authStore, route guards.
**Avoids:** JWT never-expires with no revocation (Pitfall 3), OTP brute-force with no rate limiting (Pitfall 10)

### Phase 3: Onboarding Wizard
**Rationale:** Onboarding generates all profile, medical, lifestyle, and behavior data that the AI layer depends on. Nothing in Phase 4+ works without it. Most complex frontend phase (7 animated steps, direction-aware transitions) and most complex backend phase (medical flag extraction, SafetyGuardrailService invocation).
**Delivers:** 7-step animated onboarding wizard, all profile models populated, SafetyGuardrailService standalone and testable, risk_level assigned on completion, step-completion tracking in backend, sessionStorage partial-save in frontend.
**Avoids:** Onboarding state lost on refresh (Pitfall 9), animation direction hard-coded LTR (Pitfall 12)

### Phase 4: AI Layer and Nutrition Planning
**Rationale:** Depends on complete profile data from Phase 3. The AI abstraction (MockProvider) ships here -- this makes the product usable end-to-end without a real API key. NutritionMemoryService context assembly must include medical flags permanently in the system prompt.
**Delivers:** AIProvider ABC + MockProvider with Persian-aware deterministic responses (20+ variants), PromptBuilder with locale injection and token budget management, NutritionMemoryService, NutritionAgentService, SafetyGuardrailService wired to all AI endpoints, nutrition plan generation, meal analysis, what-to-eat-now endpoint.
**Avoids:** Tight coupling to single AI provider, AI context window overflow (Pitfall 8), guardrail only in plan generation (Pitfall 5)

### Phase 5: Chat Companion and Voice
**Rationale:** Depends on the AI layer (Phase 4). Chat uses the same NutritionAgentService and SafetyGuardrailService -- guardrails must be verified to fire in chat, not only in plan generation.
**Delivers:** Daily chat companion (text + history), VoiceRecorder (MediaRecorder with MIME type detection), AudioVisualizer (Web Audio API AnalyserNode), audio upload endpoint, AudioMessage with status + MIME type, MockSTTProvider.
**Avoids:** MediaRecorder cross-browser MIME type bug (Pitfall 7), guardrail bypassed in chat (Pitfall 5 re-verification)

### Phase 6: Progress, Reports, and Settings
**Rationale:** Depends on active users with check-in history. Progress dashboard must be behavior-centric -- not weight-only -- to maintain engagement during plateau weeks.
**Delivers:** Daily check-in form, progress dashboard, weekly report, settings page (language switcher, profile edit, medical condition update with risk re-assessment), medical safety notice with clear path forward.
**Avoids:** Weight-only progress display, clinical review block with no path forward

### Phase 7: Polish and Production Hardening
**Rationale:** RTL audit, animation verification, mobile viewport fixes, and security hardening are cross-cutting concerns affecting every screen and deserve a dedicated phase.
**Delivers:** Full RTL layout audit (zero physical CSS properties), animation direction verification in Persian locale, iOS Safari viewport fix (dvh + env(safe-area-inset-bottom)), CORS lockdown, audio files served via authenticated endpoint, AuditLog review.
**Avoids:** iOS 100vh viewport clipping (Pitfall 11), audio files accessible via guessable URLs

### Phase Ordering Rationale

- Infrastructure before auth: ORM models and DB session factory are dependencies of auth routes
- Auth before onboarding: onboarding routes require authenticated users
- Onboarding before AI: NutritionMemoryService requires a fully-populated profile to assemble meaningful context
- AI layer before chat: chat routes delegate to NutritionAgentService
- Voice/audio alongside chat: both share ChatService and AudioService infrastructure
- Progress after chat: weekly reports require accumulated check-in history
- Polish as dedicated final phase: RTL and mobile viewport issues touch every screen -- incremental treatment causes regressions

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (AI Layer):** Persian food nutritional data accuracy; token counting for Persian/Arabic text (2-3 chars/token vs 4 for Latin); prompt engineering for culturally-appropriate coaching tone
- **Phase 5 (Voice):** iOS Safari MediaRecorder limitations across iOS versions are poorly documented; real-device testing plan needed before building

Phases with standard, well-documented patterns (research-phase can be skipped):
- **Phase 1 (Infrastructure):** FastAPI + SQLAlchemy 2.x + Next.js App Router has official documentation and is well-understood
- **Phase 2 (Auth):** Phone OTP + JWT is a standard FastAPI pattern documented in the official security tutorial

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies verified against official docs; library versions flagged where based on training data |
| Features | MEDIUM | Derived from project spec + market analysis; Persian market statistics are training knowledge -- validate with user research |
| Architecture | HIGH | Patterns (Repository/Service, AIProvider ABC, SafetyGuardrail as first-class service) are well-established |
| Pitfalls | HIGH (technical) / MEDIUM (medical) | Technical pitfalls verified against official docs; medical guardrail adequacy requires clinical validation |

**Overall confidence:** HIGH for technical implementation path; MEDIUM for product/market assumptions

### Gaps to Address

- **Persian food nutritional accuracy:** No authoritative open-source Iranian food nutrition database identified -- pre-populated food reference JSON must be built or sourced before v1 ships.
- **Medical guardrail clinical review:** Risk classification thresholds need validation by a clinical nutritionist. Current thresholds are conservative (correct direction).
- **SMS provider for Iranian market:** Kavenegar is referenced but not verified as current in 2026. SMSProvider interface design mitigates this -- any provider plugs in without code changes.
- **iOS Safari MediaRecorder behavior:** Must be tested on real hardware early in Phase 5, not emulators.
- **Persian STT provider quality:** Architecture prepares for Whisper/Deepgram; quality for Persian varies significantly. Acceptable gap for v1 (STT deferred).

---

## Sources

### Primary (HIGH confidence)
- FastAPI official docs (fastapi.tiangolo.com) -- router/service patterns, JWT security, dependency injection
- SQLAlchemy 2.x docs (docs.sqlalchemy.org) -- async session patterns, lazy=raise, selectinload
- Alembic docs -- render_as_batch, SQLite ALTER TABLE limitations
- Next.js App Router docs (nextjs.org/docs/app) -- route groups, layout, server components, i18n guide
- Tailwind CSS v4 docs (tailwindcss.com) -- CSS logical properties by default, PostCSS integration
- MDN MediaRecorder API -- browser availability, isTypeSupported, mimeType
- MDN Web Audio API -- AnalyserNode, getByteTimeDomainData
- MDN CSS Logical Properties -- margin-inline, padding-inline, inset-inline
- Project specification: .planning/PROJECT.md

### Secondary (MEDIUM confidence)
- Persian market dietary patterns and PCOS prevalence -- training knowledge, ~2024-2025
- Onboarding best practices for health apps (Noom, Fastic, Lifesum patterns) -- training knowledge
- RTL animation UX guidelines (Material Design RTL, Apple HIG Arabic/RTL) -- training knowledge
- iOS Safari viewport height behavior with dvh unit -- CSS Working Group documentation
- Medical safety guardrail patterns for health AI apps -- domain knowledge synthesis

### Tertiary (LOW confidence -- validate before production)
- SMS provider landscape for Iranian market in 2026 (Kavenegar status) -- needs live verification
- Persian STT provider quality comparison -- needs real-world testing
- Iranian food nutritional database availability -- no authoritative open source identified

---
*Research completed: 2026-06-03*
*Ready for roadmap: yes*