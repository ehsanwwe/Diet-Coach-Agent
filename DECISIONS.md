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
*Last updated: 2026-06-03*
