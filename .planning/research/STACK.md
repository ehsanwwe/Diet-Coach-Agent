# Stack Research

**Domain:** AI-powered multilingual nutrition coaching web app
**Researched:** 2026-06-03
**Confidence:** HIGH (core stack verified against official docs; some library versions from training data flagged where unverifiable)

---

## Recommended Stack

### Backend — Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Runtime | 3.12 is the current LTS-equivalent; match-statement, improved error messages, performance gains over 3.10/3.11 |
| FastAPI | 0.136.x | API framework | Latest stable (0.136.3 as of 2026-05-23). Native async, Pydantic v2 integration, automatic OpenAPI docs, dependency injection system is perfect for auth guards and DB sessions |
| Pydantic v2 | 2.x | Data validation / serialization | Ships with FastAPI; v2 is 5–50x faster than v1 due to Rust core; `model_config`, `@field_validator`, `@model_validator` replace v1 patterns entirely. Never mix v1 patterns |
| SQLAlchemy | 2.0.x | ORM / query builder | 2.x "2.0 style" is mandatory — `select()`, `Session.execute()`, mapped classes. v1-style `session.query()` is deprecated. Sync engine with `check_same_thread=False` is correct for SQLite + FastAPI sync routes |
| Alembic | 1.13.x | Database migrations | Standard companion to SQLAlchemy; autogenerate from mapped classes; `env.py` must be configured for SQLite; never hand-edit migration files |
| SQLite | 3.x (bundled) | Database | v1 constraint: SQLite only. Use `sqlite+pysqlite:///./app.db`. Set `check_same_thread=False`. Alembic handles schema evolution cleanly |
| Uvicorn | 0.30.x | ASGI server | Standard FastAPI server; `uvicorn[standard]` includes `httptools` and `uvloop` on Linux; `--reload` in dev |
| PyJWT | 2.x | JWT token encode/decode | Recommended by FastAPI official docs (verified). Use `jwt.encode()` / `jwt.decode()` with `HS256`. Simpler than python-jose which has unmaintained ECDSA dependency |
| python-multipart | 0.0.x | Multipart form / audio upload | Required for `UploadFile` in FastAPI; audio file upload for voice messages needs this |
| python-dotenv | 1.x | Environment config | Load `.env` files in dev; use `pydantic-settings` (`BaseSettings`) for type-safe config objects |
| pydantic-settings | 2.x | Typed settings management | `BaseSettings` with env file support; integrates cleanly with FastAPI's dependency injection for config |

### Backend — Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| passlib | 1.7.x | Password hashing | Not needed for OTP-only auth, but include for future use. If added, use `bcrypt` backend |
| httpx | 0.27.x | Async HTTP client | For calling external AI providers (OpenAI, Claude, etc.) when real AI is wired in; also used by FastAPI's `TestClient` |
| pytest | 8.x | Backend testing | Standard; use `pytest-asyncio` for async route testing |
| pytest-asyncio | 0.23.x | Async test support | Required for testing async FastAPI endpoints |

### Frontend — Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 16.x (latest) | React framework | App Router is now the default and stable. Server Components reduce client bundle. File-system routing maps cleanly to the 16-screen app structure. Turbopack is now the default dev bundler |
| React | 19.x | UI runtime | Ships with Next.js 16; React 19 stable features (use() hook, Actions, improved Suspense) are available. Declare in package.json for tooling compatibility |
| TypeScript | 5.x | Type safety | Minimum 5.1.0 per Next.js docs. Strict mode (`strict: true`) is mandatory — catches RTL direction errors, locale type mismatches |
| Tailwind CSS | 4.x | Styling | v4.3 as of 2026. Critical for this project: v4 generates CSS using **CSS logical properties by default** (`margin-inline`, `padding-inline-start` etc.) — this means RTL support is automatic without `rtl:` variant prefixes. No `tailwind.config.js` required for basic use |
| `@tailwindcss/postcss` | 4.x | PostCSS plugin | Required for Next.js integration with Tailwind v4; replaces `tailwindcss` PostCSS plugin from v3. Config: `postcss.config.mjs` with `"@tailwindcss/postcss": {}` |

### Frontend — i18n and RTL

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Custom dictionary system | — | Translation strings | **This project explicitly chose dictionary-based i18n over next-intl/i18next** (see PROJECT.md Key Decisions). Pattern: `app/[lang]/dictionaries/fa.json`, `en.json`, `ar.json` loaded via `getDictionary(lang)` server-side. Zero client bundle impact |
| `@formatjs/intl-localematcher` | 0.5.x | Locale negotiation | Recommended in Next.js official docs for matching `Accept-Language` headers to supported locales in middleware |
| `negotiator` | 1.x | HTTP header parsing | Companion to `intl-localematcher`; parses `Accept-Language` header |

**RTL pattern:** The `dir` attribute is set on `<html>` in the root layout based on locale. `fa` and `ar` → `dir="rtl"`, `en` → `dir="ltr"`. Tailwind v4's logical properties handle all directional CSS automatically. **Do not hardcode `left`/`right` in CSS** — use `start`/`end` (e.g., `ps-4` not `pl-4`, `ms-2` not `ml-2`).

### Frontend — State Management and Data Fetching

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Zustand | 4.x | Client state | Auth state, active locale, UI state (recording status, onboarding step). Lightweight; works with Next.js App Router without Provider boilerplate. Store locale in Zustand + localStorage sync |
| Native `fetch` | built-in | API calls | Use Next.js extended `fetch` in Server Components (with caching). In Client Components, use `fetch` directly or a thin wrapper. For this app's complexity, a custom `apiClient.ts` wrapper is sufficient |
| React Hook Form | 7.x | Form management | 7-step onboarding forms; phone input; OTP verification. Native HTML validation + Zod schema resolver. Zero re-renders during typing |
| Zod | 3.x | Schema validation | Used with React Hook Form (`@hookform/resolvers/zod`). Define schemas for each onboarding step. Generates TypeScript types automatically |

### Frontend — Audio and Voice

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| MediaRecorder API | Browser built-in | Audio recording | No external SDK needed. Widely available (all modern browsers since 2021). Use `audio/webm;codecs=opus` — best compression, widely supported. Fallback detect with `MediaRecorder.isTypeSupported()` |
| Web Audio API / AnalyserNode | Browser built-in | Waveform visualization | `AnalyserNode` provides frequency data for real-time audio visualizer. `getByteTimeDomainData()` for waveform, `getByteFrequencyData()` for bars. No library needed |
| No external audio library | — | — | `react-use`, `use-sound`, wavesurfer.js are **not** needed — this project uses raw Web APIs as specified |

### Frontend — UI Components

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Framer Motion | 10.x or 11.x | Animations | Direction-aware slide animations for onboarding steps (slide left vs right based on `dir`). Page transitions. The `AnimatePresence` component handles enter/exit. Required for the 7-step animated flow |
| Lucide React | 0.4xx | Icons | Tree-shakeable, TypeScript-first. All icons as React components. For RTL mirroring, apply `scale-x-[-1]` transform when `dir="rtl"` on directional icons (chevrons, arrows) |
| clsx + tailwind-merge | 2.x / 2.x | Conditional class names | `clsx` for conditionals, `tailwind-merge` (or `twMerge`) to resolve conflicts. Use `cn()` utility combining both — standard Next.js pattern |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package manager | Fast Rust-based package manager; replaces pip/venv in 2025. `uv sync` installs from `pyproject.toml`. Optional but strongly recommended |
| pyproject.toml | Python project config | Standard over `requirements.txt`; defines dependencies, dev dependencies, tool config |
| ESLint | Frontend linting | `eslint.config.mjs` flat config format (required in Next.js 16). Include `eslint-plugin-react-hooks` and Next.js plugin |
| TypeScript | Type checking | Run `tsc --noEmit` in CI to catch type errors separately from build |
| Biome | Optional alternative linter | Fast Rust linter; can replace ESLint + Prettier; mention as alternative |

---

## Installation

### Backend

```bash
# Create virtual environment (using uv — recommended)
uv init backend
cd backend
uv add fastapi[standard] sqlalchemy alembic pyjwt pydantic-settings python-multipart python-dotenv

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx

# Or with pip
pip install "fastapi[standard]" sqlalchemy alembic pyjwt pydantic-settings python-multipart python-dotenv
```

### Frontend

```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --eslint --app --tailwind --src-dir

# State, forms, validation
npm install zustand react-hook-form @hookform/resolvers zod

# i18n
npm install @formatjs/intl-localematcher negotiator
npm install --save-dev @types/negotiator

# Animation and icons
npm install framer-motion lucide-react

# Utility
npm install clsx tailwind-merge
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| SQLModel (sync via SQLAlchemy) | asyncpg + SQLAlchemy async | Async SQLite requires `aiosqlite` and adds complexity with no real benefit for SQLite (SQLite writes are serialized anyway); sync is simpler and sufficient |
| PyJWT | python-jose | python-jose has an unmaintained ECDSA dependency; PyJWT is actively maintained and is FastAPI's own docs recommendation as of 2025 |
| Custom dictionary i18n | next-intl | Project decision: avoid vendor lock-in, simpler mental model, full control. Next-intl adds complexity for a custom-language app like this |
| Custom dictionary i18n | i18next / react-i18next | Same reason; also, i18next is designed for client-side and conflicts with Next.js Server Components RSC architecture |
| Tailwind CSS v4 | Tailwind CSS v3 | v4 has logical properties built-in — critical for RTL. v3 required `rtl:` plugin and explicit configuration. v4 removes the need entirely |
| Zustand | Redux Toolkit / Jotai | Zustand has the lowest boilerplate for this complexity level; no Provider needed; works cleanly with App Router |
| Framer Motion | CSS transitions only | Direction-aware animated transitions for RTL/LTR step navigation require programmatic control; CSS alone cannot detect direction at animation time |
| Native fetch | Axios | Next.js 15+ extended `fetch` has built-in caching and revalidation semantics; Axios adds no value in RSC context and complicates server/client boundary |
| React Hook Form + Zod | Formik + Yup | RHF has zero re-renders; Zod is TypeScript-first and generates types; Formik/Yup is slower and less type-safe |
| SQLAlchemy 2.x ORM | SQLModel | SQLModel is syntactic sugar over SQLAlchemy 2.x. For a complex schema (20+ models), raw SQLAlchemy 2.x with explicit `DeclarativeBase` is more explicit and less magical. Either works; raw SQLAlchemy is preferred when teams know SQL |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SQLAlchemy 1.x patterns (`session.query()`) | Deprecated in SQLAlchemy 2.0; will be removed. `select()` + `session.execute()` is the only correct pattern | SQLAlchemy 2.x with `select()` |
| python-jose | Has unmaintained ECDSA dependency; security risk; FastAPI docs switched to PyJWT in 2024 | PyJWT 2.x |
| next-intl / i18next | Not wrong for other projects, but this project explicitly chose dictionary-based i18n. Adding a library creates a conflict with that decision | Custom `getDictionary()` + JSON files |
| Tailwind CSS v3 with `rtl:` plugin | v3 RTL requires explicit plugin setup and `rtl:` prefixes on every directional utility. v4 eliminates this entirely | Tailwind CSS v4 with logical properties |
| Hardcoded `padding-left` / `margin-right` in CSS | Breaks RTL layout immediately. Persian and Arabic users will see mirrored spacing | CSS logical properties: `padding-inline-start`, `margin-inline-end` |
| `pl-4`, `mr-2` Tailwind classes | These are physical properties — they don't flip in RTL. Tailwind v4 still has them for edge cases, but avoid for any directional spacing | `ps-4`, `me-2` (inline-start / inline-end variants) |
| Hardcoded `left:`/`right:` for icon direction | Directional icons (chevron-left, arrow-right) point the wrong way in RTL | Detect `dir` and apply `scale-x-[-1]` transform, or use a `DirectionalIcon` wrapper component |
| wavesurfer.js for audio visualization | Heavy dependency (300KB+) for something achievable with 20 lines of Web Audio API code | Native `AnalyserNode` from Web Audio API |
| next-auth | Built for OAuth and email/password flows; phone OTP with custom JWT is simpler to implement from scratch | FastAPI JWT + custom Next.js auth context |
| SQLite in async mode without `aiosqlite` | SQLite's async driver (`aiosqlite`) has known quirks and no performance benefit over sync for this use case | Sync SQLAlchemy with sync FastAPI routes |
| `any` TypeScript type | Defeats the purpose of TypeScript; RTL direction bugs and locale mismatches are caught by strict typing | Strict TypeScript with `Locale = 'fa' | 'en' | 'ar'` union types |

---

## Stack Patterns by Variant

**For the AI abstraction layer:**
- Define an `AIProvider` abstract base class (Python ABC or Protocol) with methods: `generate_response()`, `analyze_meal()`, `transcribe_audio()`
- `MockAIProvider` returns deterministic JSON responses — no LLM calls
- `OpenAIProvider` and `ClaudeProvider` implement the same interface
- `NutritionAgentService` takes `AIProvider` via constructor injection
- Wire the active provider from env var: `AI_PROVIDER=mock|openai|claude`
- Never import OpenAI/Anthropic SDK directly in service layer; always through the abstraction

**For the OTP flow:**
- `AuthOTP` model stores: `phone`, `otp_code`, `expires_at`, `used`
- In dev: always accept `123456` as valid OTP (env-gated)
- In prod: call SMS provider (Kavenegar for Iran, Twilio international) — the service interface is the same
- JWT issued after OTP verification: `sub` = user ID, `exp` = 7 days for mobile UX, `iat`, optional `jti` for logout/invalidation
- Store JWT in `httpOnly` cookie (preferred) or `localStorage` (acceptable for mobile-first PWA)

**For RTL/LTR direction detection in animations:**
- Read `dir` from `document.documentElement.dir` or pass it as a React context value
- Framer Motion slide: `x: isRTL ? -100 : 100` for "next step" direction
- Onboarding step advancing = slide toward reading direction start

**For voice recording state machine:**
```
idle → recording → paused → stopped → uploading → idle
                          ↓
                       cancelled → idle
```
- Use a Zustand slice for recording state, not component-local state — multiple UI elements observe it
- `MediaRecorder.ondataavailable` accumulates chunks in a ref, not state (avoid re-renders)
- On `stop`, create `Blob` and set in state for preview player

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| FastAPI 0.136.x | Pydantic v2 only | v1 Pydantic compatibility mode was removed; all models must use v2 patterns (`model_config`, not `class Config`) |
| SQLAlchemy 2.0.x | Alembic 1.13.x | Alembic 1.13+ required for SQLAlchemy 2.0 mapped class autogenerate support |
| Next.js 16.x | React 19.x | Next.js 16 ships with React 19; do not install React 18 separately |
| Tailwind CSS v4 | `@tailwindcss/postcss` v4 | v4 no longer uses `tailwind.config.js` by default; CSS-first config via `@theme {}` in globals.css |
| Tailwind CSS v4 | PostCSS 8.x | Requires PostCSS 8; incompatible with PostCSS 7 |
| Framer Motion 11.x | React 19 | Framer Motion 11 supports React 19 Server/Client component boundaries |
| Zod 3.x | React Hook Form 7.x via `@hookform/resolvers` | Use `zodResolver` from `@hookform/resolvers/zod` |
| PyJWT 2.x | Python 3.8+ | `jwt.encode()` returns `str` in v2 (was `bytes` in v1) — critical difference |

---

## Sources

- FastAPI release notes (fastapi.tiangolo.com/release-notes/) — FastAPI version 0.136.3 confirmed; HIGH confidence
- FastAPI JWT tutorial (fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — PyJWT recommendation confirmed; HIGH confidence
- FastAPI SQL tutorial (fastapi.tiangolo.com/tutorial/sql-databases/) — SQLModel/SQLAlchemy sync session pattern confirmed; HIGH confidence
- Next.js installation docs (nextjs.org/docs/app/getting-started/installation) — version 16.2.7, Node 20.9+ requirement confirmed; HIGH confidence
- Next.js i18n guide (nextjs.org/docs/app/guides/internationalization) — `app/[lang]` pattern, dictionary approach confirmed; HIGH confidence
- Tailwind CSS v4 install for Next.js (tailwindcss.com/docs/installation/framework-guides/nextjs) — v4.3, PostCSS config confirmed; HIGH confidence
- Tailwind CSS v4 blog post (tailwindcss.com/blog/tailwindcss-v4) — CSS logical properties default behavior confirmed; HIGH confidence
- MDN MediaRecorder API — browser availability (widely available since April 2021) confirmed; HIGH confidence
- SQLAlchemy 2.x, Alembic versions — MEDIUM confidence (official changelogs not fetchable; based on known stable releases as of mid-2026)
- Zustand, Framer Motion, React Hook Form, Zod versions — MEDIUM confidence (active projects; versions from training data + known ecosystem state)

---

*Stack research for: AI-powered multilingual diet coach (Diet-Coach-Agent)*
*Researched: 2026-06-03*
