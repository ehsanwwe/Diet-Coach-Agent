# Decisions — Diet Coach Agent

> Append-only log of architectural and product decisions. Never delete entries.

---

## 2026-06-03 — Project Initialization

### D-001: SQLite (not PostgreSQL) for v1
**Decision:** Use SQLite as the sole database engine for v1.
**Rationale:** Simplicity, zero infra overhead, faster onboarding for contributors. Alembic migrations with `render_as_batch=True` make the upgrade path to PostgreSQL safe and non-breaking.
**Alternatives rejected:** PostgreSQL (adds infra complexity for v1); MySQL (no benefit over SQLite at this scale).

### D-002: Phone OTP only (no email/password)
**Decision:** Authentication is phone number + OTP only.
**Rationale:** Persian market norm; lower friction than email/password; prepares for real SMS providers (Kavenegar). OTP = `123456` in dev.
**Alternatives rejected:** Email/password (higher friction, no benefit for target market); OAuth (adds complexity, requires redirect flows incompatible with PWA install UX).

### D-003: Persian as default language (RTL-first)
**Decision:** Persian (`fa`) is the default locale; RTL is the primary direction.
**Rationale:** Primary target market. RTL-first is significantly cheaper than retrofitting RTL onto an LTR codebase.
**Alternatives rejected:** English-first (wrong for target market); locale detection from browser (complicates server-side rendering and flicker).

### D-004: Dictionary-based i18n (not next-intl or i18next)
**Decision:** Custom `getDictionary(lang)` with JSON files per locale.
**Rationale:** Zero vendor lock-in, full control, zero client bundle impact (dictionaries loaded server-side), simpler mental model. Aligns exactly with Next.js official i18n pattern.
**Alternatives rejected:** next-intl (vendor dependency, different RSC patterns); i18next (designed for client-side, conflicts with Server Components).

### D-005: Tailwind CSS v4 (not v3)
**Decision:** Tailwind CSS v4.x with CSS logical properties by default.
**Rationale:** v4 generates all spacing utilities with logical properties (`margin-inline`, `padding-inline-start`) — RTL support is automatic when `dir="rtl"` is set. v3 requires manual `rtl:` plugin setup on every directional class.
**Alternatives rejected:** Tailwind v3 (requires per-class RTL config, high retrofit cost); plain CSS (too verbose for rapid UI development).

### D-006: Sync SQLAlchemy (not async) for SQLite
**Decision:** Use synchronous SQLAlchemy with `check_same_thread=False`.
**Rationale:** SQLite serializes all writes regardless; async SQLAlchemy with `aiosqlite` adds complexity with zero throughput benefit. Sync `Session` via `Depends(get_session)` is the official FastAPI pattern.
**Alternatives rejected:** Async SQLAlchemy + aiosqlite (more complex, no benefit for SQLite).

### D-007: PyJWT (not python-jose)
**Decision:** Use `PyJWT 2.x` for JWT encode/decode.
**Rationale:** FastAPI official docs switched to PyJWT recommendation in 2024. python-jose has an unmaintained ECDSA dependency (security risk).
**Alternatives rejected:** python-jose (unmaintained dependency, security risk).

### D-008: AI provider abstraction from day 1
**Decision:** `AIProvider` ABC + `OpenClawProvider` + `MockAIProvider`; active provider from env var.
**Rationale:** Avoids tight coupling to any one provider. Mock enables full e2e testing without API keys. OpenClaw covers real AI when env vars are set.
**Alternatives rejected:** Hard-coding OpenAI SDK (vendor lock-in); no abstraction (impossible to test without live API keys).

### D-009: OpenClaw as v1 real AI provider
**Decision:** `OpenClawProvider` uses OpenAI-compatible `/chat/completions` endpoint; all config from 10 `OPENCLAW_*` backend env vars only.
**Rationale:** OpenAI-compatible interface works with any compatible endpoint; env-var-only config keeps secrets out of code; falls back to MockAIProvider when not configured.
**Alternatives rejected:** Direct OpenAI SDK (vendor lock-in); hard-coded config (security risk).

### D-010: Rolling conversation summaries for long sessions
**Decision:** When `OPENCLAW_CONTEXT_SUMMARY_ENABLED=true` and message count exceeds `OPENCLAW_CONTEXT_MAX_MESSAGES`, generate a rolling summary and store it in `ChatSession.summary`; inject into next session's system prompt.
**Rationale:** OpenClaw context windows are finite. Nutrition memory (medical flags, behavior patterns) must persist across context resets. Rolling summaries maintain continuity without exceeding token limits.
**Alternatives rejected:** Truncate oldest messages only (loses critical nutrition context); no persistence (each session starts cold).

### D-011: PWA (not native app)
**Decision:** Build as a Progressive Web App — manifest, service worker, offline fallback, install prompt.
**Rationale:** Web-first; no App Store dependency; installable on iOS and Android via browser; centered mobile layout on desktop mimics native app feel.
**Alternatives rejected:** React Native / Expo (separate codebase, deployment complexity); Capacitor (wrapping overhead, still requires store submission).

### D-012: Muted/pale/app-like UI aesthetic
**Decision:** UI uses desaturated, pale colors; app-like layout (bottom nav, full-bleed screens, soft rounded cards); no website-style top nav, no Bootstrap card grids, no admin-panel borders.
**Rationale:** Target users are health-conscious adults seeking a trustworthy companion; clinical-calm aesthetic builds trust. Aggressive gym-app or admin-panel look reduces perceived quality.
**Alternatives rejected:** Saturated/bold palette (gym-app feel, wrong for this audience); Bootstrap-style components (boxy, website-like, low trust signal for health context).

### D-013: Continuation files updated every commit
**Decision:** `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md` at repo root; Claude updates them after every meaningful commit.
**Rationale:** After `/clear`, all conversation context is lost. These files are the persistent resume trail — they let work continue from any new session without re-reading all planning docs.
**Alternatives rejected:** Relying on git log (too noisy); relying on .planning/ STATE.md (not surfaced enough).

---

## 2026-06-03 — Phase 1 Implementation Decisions

### D-014: All ORM models use String(36) for UUID primary keys (not native UUID type)
**Decision:** Use `String(36)` with `default=lambda: str(uuid.uuid4())` for all primary keys.
**Rationale:** SQLite has no native UUID type. String(36) is portable to PostgreSQL without migration changes. The Alembic render_as_batch=True flag handles future type changes safely.
**Alternatives rejected:** Python UUID type (dialect-specific, requires extra Alembic config); Integer PKs (prevents distributed ID generation).

### D-015: JSON list fields stored as Text (not JSON type)
**Decision:** Fields containing lists (disliked_foods, cravings, report_data, etc.) use `Text` column type, with application-layer JSON serialization.
**Rationale:** SQLite has no native JSON type (JSON1 extension varies); using Text is portable to PostgreSQL (which does have JSON). The application layer owns serialization/deserialization.
**Alternatives rejected:** SQLAlchemy JSON type (uses SQLite's JSON1 extension — not universally available); separate junction tables (over-engineered for list fields that are read/written as units).

### D-016: SECRET_KEY validated via pydantic field_validator at import time
**Decision:** `settings = Settings()` is called at module level in `config.py`; the `@field_validator("SECRET_KEY")` runs immediately, raising `ValueError` if absent or placeholder. FastAPI import of `settings` in `main.py` triggers this at startup.
**Rationale:** Fails fast — the process never starts with a missing key. No runtime check needed in routes.
**Alternatives rejected:** Lifespan event validation (later failure, harder to catch in tests); manual check in each route (error-prone, could be missed).

---

## 2026-06-03 — Phase 2 Implementation Decisions

### D-017: middleware.ts kept (not renamed to proxy.ts despite Next.js 16 deprecation)
**Decision:** Keep `src/middleware.ts` filename for Phase 2. Rename to `proxy.ts` in Phase 10 (Polish).
**Rationale:** Next.js 16 deprecates `middleware.ts` in favor of `proxy.ts`, but the old name still works and is more widely documented. Renaming is safe but low priority.
**Alternatives rejected:** Rename now (extra noise in Phase 2 commit, not functionally required).

### D-018: Locale cookie is not httpOnly (readable by JavaScript)
**Decision:** Set `NEXT_LOCALE` cookie with `httpOnly: false` so client components can read the current locale if needed for live language switching.
**Rationale:** The locale cookie contains no sensitive data. Client-side readability enables future Zustand locale store to sync from cookie without a server round-trip.
**Alternatives rejected:** httpOnly=true (would require an API route for JS to learn the current locale).

### D-019: PWA icon uses SVG for Phase 2; PNGs deferred to Phase 10
**Decision:** `public/icons/icon.svg` is the only icon format for Phase 2. The manifest references it with `"sizes": "any"` and `"type": "image/svg+xml"`.
**Rationale:** Binary PNG files cannot be created by the code generation process. SVG icons are widely supported in modern browsers for PWA manifests. iOS Apple Touch Icon (PNG) is needed for Phase 10 Polish.
**Alternatives rejected:** Placeholder 1×1 PNG (misleading); skipping icons entirely (breaks manifest validation).

### D-020: Direction set server-side via NEXT_LOCALE cookie in root layout
**Decision:** Root `app/layout.tsx` reads the `NEXT_LOCALE` cookie (set by middleware) and applies `lang` and `dir` to `<html>`. The `[lang]` layout does not re-render `<html>`.
**Rationale:** Cookie is available at server-render time so `dir="rtl"` is in the initial HTML — zero client-side direction flicker. The alternative (script tag / useEffect) causes a visible layout shift.
**Alternatives rejected:** `dir` set via client script (causes flicker); `dir` only in body/div (breaks CSS logical properties on scrollbar and root fonts).

---

## 2026-06-03 — Phase 3 Implementation Decisions

### D-021: Token stored in localStorage (not httpOnly cookie) for Phase 3
**Decision:** Access token stored in `localStorage` via `src/lib/storage.ts` abstraction.
**Rationale:** This is a mobile PWA where `httpOnly` cookies add complexity (CSRF protection, cross-origin cookie handling). All token access is centralized in `storage.ts` — no scattered `localStorage` calls in components. Can be migrated to `httpOnly` cookie in Phase 10 polish.
**Alternatives rejected:** `httpOnly` cookie (requires cookie-based refresh logic and CSRF handling now); sessionStorage (lost on tab close, bad for mobile).

### D-022: Phone number passed via query parameter from login to verify page
**Decision:** After OTP request, router navigates to `/[lang]/login/verify?phone=<encoded>`. Verify page reads phone from `searchParams`.
**Rationale:** Simplest stateless approach; phone is not sensitive; avoids Zustand store for a single in-flight value; works with Next.js Server Components (searchParams available at server render).
**Alternatives rejected:** Zustand store (requires Provider, more setup for Phase 3); URL state via cookies (over-engineering for a single page transition).

### D-023: Naive UTC datetimes throughout for SQLite compatibility
**Decision:** All datetime values stored in SQLite use naive UTC datetimes (`datetime.now(timezone.utc).replace(tzinfo=None)`). API responses use timezone-aware datetimes.
**Rationale:** SQLite's DateTime column stores naive datetimes. Mixing timezone-aware and naive datetimes in comparisons causes errors. Consistent naive UTC avoids this. API layer can re-attach timezone info for clients.
**Alternatives rejected:** SQLite `DateTime(timezone=True)` (SQLite doesn't support it natively); `datetime.utcnow()` (deprecated in Python 3.12+).

### D-024: AuthContext dataclass for FastAPI dependency carrying jti + exp
**Decision:** `get_auth_context` returns `AuthContext(user, jti, exp)` dataclass. Routes needing only the user use `get_current_user` (derived dep); logout uses `get_auth_context` to access jti.
**Rationale:** Avoids decoding the JWT twice per request. FastAPI caches dependency results per request — `get_auth_context` is computed once even when both `get_auth_context` and `get_current_user` appear in the dependency tree.
**Alternatives rejected:** Decode token again in logout (wasteful, error-prone); put jti in a separate Depends (same double-decode problem).

### D-025: OTP invalidation on re-request
**Decision:** When a new OTP is requested for a phone number, all existing unused+valid OTPs for that phone are marked `invalidated_at = now()` before the new one is created.
**Rationale:** Prevents a user from having multiple valid OTPs concurrently, which would allow replaying an older code. Simpler than setting a flag on the user; works with the existing `AuthOTP.invalidated_at` column from Phase 1 schema.
**Alternatives rejected:** Let old OTPs expire naturally (allows concurrent valid codes); delete old OTPs (loses audit trail).

---

## 2026-06-03 — Phase 4 Implementation Decisions

### D-026: is_onboarded flag on User model (not separate OnboardingSession table)
**Decision:** Add `is_onboarded: bool = False` directly to the `User` model.
**Rationale:** Single boolean flag is the simplest check for whether onboarding is complete. A separate OnboardingSession table adds complexity with no benefit at this stage. Progress tracking (which step was last completed) is derived at query time from the existence of related rows, not stored as state.
**Alternatives rejected:** Separate OnboardingSession model (over-engineering); `onboarding_step: int` field (fragile, couples to step order).

### D-027: Warning symptoms stored as UserMedicalFlag sentinel row
**Decision:** Warning symptoms (free-text list) are stored in a `UserMedicalFlag` row with `condition_code="warning_symptoms"` and the symptom list JSON-encoded in the `notes` field.
**Rationale:** Keeps all medical data in one table without schema changes. The existing `notes: Text` column on `UserMedicalFlag` is designed for exactly this kind of supplementary information.
**Alternatives rejected:** Separate `WarningSymptom` table (unnecessary new table for a single list field); `UserProfile.notes` field (medical data belongs with medical flags).

### D-028: Medical flags replaced on every POST /onboarding/medical (upsert per code)
**Decision:** Each call to POST /onboarding/medical upserts all 10 condition flags using the `UniqueConstraint("user_id", "condition_code")`. Medications and allergies are fully replaced (delete-all + insert).
**Rationale:** The onboarding flow is idempotent — calling any step twice must produce the same final state. Upsert for flags preserves the exact state from the most recent call. Delete-all for medications/allergies is correct because the user may have removed items since the last call.
**Alternatives rejected:** Merge/diff medications (complex, error-prone, no benefit for onboarding-only use case).

### D-029: Safety risk assessment runs at both /medical step and /complete step
**Decision:** `SafetyGuardrailService.assess()` is called at both `POST /onboarding/medical` (returns preliminary risk_level in response) and `POST /onboarding/complete` (creates persisted NutritionRiskAssessment row).
**Rationale:** Frontend needs early risk feedback after the medical step so it can show appropriate messaging before the user continues. The authoritative assessment is created at `complete` and stored in `NutritionRiskAssessment`. The medical-step assessment is ephemeral (not stored).
**Alternatives rejected:** Risk assessment only at complete (delays feedback); store assessment at each medical call (creates many rows for partial updates).

### D-030: clinical_review_required does not block is_onboarded=True
**Decision:** Even users with `clinical_review_required` risk level have `is_onboarded` set to `True` on POST /onboarding/complete.
**Rationale:** Onboarding captures intent and data — it does not gatekeep access. The app delivers appropriate messaging (consult a doctor) based on `risk_level`/`clinical_review_required` fields on the response and stored NutritionRiskAssessment. Blocking completion would trap users who need medical guidance most.
**Alternatives rejected:** Block completion for clinical users (paternalistic, blocks flow for users who need the service most); separate "pending clinical review" status (extra state machine complexity).

---

## 2026-06-03 — Phase 6 Implementation Decisions

### D-031: Audio files stored locally under backend/storage/audio/ (not object storage)
**Decision:** Uploaded audio files are stored on the local filesystem under `AUDIO_STORAGE_PATH` (default `./storage/audio`). The storage directory is gitignored.
**Rationale:** Phase constraint is local/SQLite-only. S3/GCS integration would require cloud credentials and adds complexity. The `storage_key` (filename) is stored in the DB, keeping paths relative so the storage root can be changed via env var.
**Alternatives rejected:** Store audio as base64 in SQLite (not scalable, corrupts large blobs); use `/tmp` (data lost on restart); commit to git (binary files, privacy risk).

### D-032: transcription_status = "not_configured" for all Phase 6 uploads
**Decision:** All AudioMessage records created in Phase 6 receive `transcription_status = "not_configured"`.
**Rationale:** No STT provider is integrated in Phase 6. "not_configured" clearly signals to the frontend and future developers that transcription is architecturally supported but not yet wired. Frontend displays "صدا ذخیره شد" (audio saved) for this status.
**Alternatives rejected:** "pending" (implies STT is coming soon but just queued, which is misleading); "not_available" (implies a temporary failure rather than a config choice).

### D-033: Placeholder assistant response in Phase 6 text chat
**Decision:** POST /onboarding/chat/text always returns a hardcoded Persian placeholder as the assistant message.
**Rationale:** Phase 06 scope explicitly excludes AI/OpenClaw. The placeholder lets the frontend show a real chat bubble and prove the round-trip works, without misleading users that AI is active.
**Alternatives rejected:** Return no assistant message (frontend would need special-case null handling); return English placeholder (breaks Persian-first design).

### D-034: Separate `audio` dictionary namespace for Phase 6 UI strings
**Decision:** All audio/chat UI strings live in a dedicated `audio` section of the Dictionary interface (fa/en/ar), parallel to `onboarding`.
**Rationale:** The audio component tree is used in the onboarding final step and will reuse in Phase 8 (Nutrition Chat). A separate namespace makes the strings reusable without duplication. The `onboarding` dict grows large enough without adding 23 more keys.
**Alternatives rejected:** Add audio keys directly to `onboarding` dict (pollutes a large namespace); hardcode strings (violates no-hardcoded-text rule).

---

## 2026-06-03 — Phase 7 Implementation Decisions

### D-035: Single `generate_text()` method on AIProvider (not per-task methods)
**Decision:** AIProvider ABC exposes one `generate_text(messages, temperature, max_tokens)` method. Task dispatch is done by PromptBuilder injecting TASK:<type> markers into system messages, which MockAIProvider reads.
**Rationale:** Keeps the provider interface minimal and OpenAI-compatible. Any future provider (Claude, Gemini) implements one method. MockAIProvider reads task markers rather than separate methods, avoiding interface explosion.
**Alternatives rejected:** Per-task ABC methods (wider interface, every provider implements 4+ methods); task parameter on generate_text (not OpenAI-compatible, leaks app semantics into provider).

### D-036: MockAIProvider returns deterministic Persian-friendly JSON for all 4 tasks
**Decision:** MockAIProvider stores hardcoded JSON responses for generate_plan, analyze_meal, what_to_eat_now, and adapt_plan. Task type detected from TASK:<type> marker in system message.
**Rationale:** App must work end-to-end without OpenClaw. Mock responses are realistic (Persian food names, culturally appropriate) so frontend can be developed and tested against real-shaped data.
**Alternatives rejected:** Random/lorem responses (makes frontend development harder); empty stubs (not useful for UI testing).

### D-037: NutritionAgentService falls back to mock on provider failure or unparseable JSON
**Decision:** If OpenClawProvider raises AIProviderError, fall back to MockAIProvider. If JSON extraction from response fails, fall back to mock data. Both paths set is_mock=True.
**Rationale:** Nutrition advice failures must not surface as 500 errors to users. Mock fallback ensures the app always returns a usable response, and the is_mock flag tells the frontend the response is not real AI.
**Alternatives rejected:** Propagate errors to API layer (user sees error for transient network failure); return empty response (frontend breaks).

### D-038: plan_metadata as JSON Text field on NutritionPlan
**Decision:** Add one `plan_metadata` Text column (JSON) to `nutrition_plans` for daily_guidelines, warnings, and provider metadata. Meal rows store per-meal macros.
**Rationale:** The existing NutritionPlan model has title/description/generated_by but no structured field for guidelines and warnings. Adding one JSON Text field is the smallest safe change and consistent with the project convention (D-015).
**Alternatives rejected:** Multiple new columns for each guideline (over-engineering for Phase 7); encode in description (not machine-readable).

### D-039: Safety guardrails in nutrition_service.py, not nutrition_agent_service.py
**Decision:** NutritionService decides whether to call AI based on risk level. NutritionAgentService only does the AI call (no safety logic). Clinical-review users receive a hardcoded wellness guidance response.
**Rationale:** Safety is a business rule, not an AI concern. Centralizing it in the service layer means it applies regardless of which provider is used or how the agent changes.
**Alternatives rejected:** Safety in agent service (mixes AI orchestration with policy); safety in endpoints (thin services, bloated routes).

---

## 2026-06-03 — Phase 8 Implementation Decisions

### D-040: Nutrition endpoints return raw models (not SuccessResponse-wrapped)
**Decision:** Phase 7 nutrition endpoints return raw Pydantic models; Phase 8 frontend lib uses raw fetch (not `api.get/post`) to match.
**Rationale:** Nutrition endpoints were written in Phase 7 without SuccessResponse wrapper. Changing them would break nothing but adds churn. Frontend lib handles both patterns: `lib/nutrition.ts` parses raw, `lib/chat.ts` unwraps `data`.

### D-041: Chat dictionary loaded client-side on nutrition/plan/chat pages
**Decision:** Nutrition pages (plan, meal-analysis, what-to-eat, chat) load the dictionary client-side via `getDictionary()` in a `useEffect`.
**Rationale:** These are interactive Client Component pages that need the full dictionary. Server Component + Client Component split would require prop-drilling. Client-side load adds one render cycle but keeps components self-contained. Refactor to Server Components in Phase 10 if needed.

### D-042: Companion chat uses existing ChatSession model with session_type="companion"
**Decision:** Companion chat reuses ChatSession/ChatMessage tables from Phase 1 schema with `session_type="companion"`. One session per user (latest active).
**Rationale:** Tables already exist; no migration needed. One session per user is correct for Phase 8 (conversation persists across visits). Multi-session support can be added in Phase 9/10.

---

## 2026-06-04 — Phase 9 Implementation Decisions

### D-043: SQLite in-memory test DB requires StaticPool
**Decision:** Test engine uses `poolclass=StaticPool` to prevent connection pooling from opening fresh empty in-memory databases on each query.
**Rationale:** Default SQLAlchemy pool returns the connection after `commit()`, causing the next query (e.g. `db.refresh()`) to open a new connection with an empty in-memory DB — "no such table" errors. `StaticPool` reuses the same underlying connection for all requests.

### D-044: Progress service is pure aggregation — no AI calls
**Decision:** `progress_service.py` computes behavior wins and suggested focus via rule-based logic, no LLM call.
**Rationale:** Progress metrics are deterministic aggregations (averages, thresholds, streaks). LLM adds latency and cost with no accuracy benefit for quantitative summaries. AI-powered insights can be added in a future phase.

### D-045: Weekly report window = Monday–Sunday of current week
**Decision:** Weekly report always covers the current calendar week (Monday = week start, computed from `today.weekday()`).
**Rationale:** Consistent, predictable window for users; avoids "rolling 7 days" complexity that leads to confusing mid-week re-computation.

### D-046: Behavior wins — 5 tracked + 3 untracked chips
**Decision:** Summary returns 8 behavior win chips: sleep, activity, logging, low_stress, low_hunger (tracked v1), protein, fiber, hydration (not tracked in v1, shown as informational).
**Rationale:** Users see the full picture of what matters; untracked chips communicate future roadmap and set expectations without hiding data gaps.

---

## 2026-06-04 — Phase 10 Implementation Decisions

### D-047: Language selector page excludes AppBottomNav
**Decision:** `/[lang]/settings/language` page does NOT include `<AppBottomNav>`.
**Rationale:** Language selector is a sub-screen of Settings (navigated to from the Language row). Back navigation is via browser back button. Including bottom nav would create nested nav confusion and visual clutter.

### D-048: Phone number rendered dir="ltr" in Settings
**Decision:** The phone number display in SettingsScreen uses `dir="ltr"` attribute.
**Rationale:** Phone numbers are technical identifiers — they read left-to-right regardless of locale. This is the standard pattern for numeric/technical data in RTL layouts and is NOT a violation of the project's "no hard-coded direction" rule (which applies to `<html>` and layout containers, not inline data values).

### D-049: Logout server-side failure silently swallowed
**Decision:** `api.post('/api/v1/auth/logout', ...)` errors are caught and ignored; `clearToken() + router.replace(login)` always executes regardless of server response.
**Rationale:** The user's intent to log out must always succeed from their perspective. If the server logout endpoint fails (401 because token already expired, 500 because server error), the correct UX is still to clear the local token and redirect to login. Blocking logout on server failure would leave users stuck.

### D-050: api.patch() method added to api.ts
**Decision:** Extended `api` object with a `patch()` method matching `post()` pattern but with `method: 'PATCH'`.
**Rationale:** Required for fire-and-forget language preference persist call in LanguageSelector. Following the project's existing `api.get/post` pattern keeps all HTTP calls through the typed wrapper.

---
*Last updated: 2026-06-04*
