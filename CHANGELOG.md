# Changelog — Diet Coach Agent

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

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
