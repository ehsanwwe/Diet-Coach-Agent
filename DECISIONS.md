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
*Last updated: 2026-06-03*
