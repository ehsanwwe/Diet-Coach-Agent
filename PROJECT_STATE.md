# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 4 COMPLETE → Phase 5 next
**Overall progress:** Phase 4 of 10 complete (40%)

## What Exists Now

### Backend (`backend/`) — Phase 1
- `pyproject.toml`, all dependencies, all 22 ORM models, Alembic migrations
- `app/core/config.py` — SECRET_KEY validation, all 10 OPENCLAW_* vars
- `app/main.py`, `/api/v1/health`, `backend/.env.example`, `backend/README.md`

### Frontend (`frontend/`) — Phase 2 COMPLETE
- **i18n infrastructure**
  - `src/dictionaries/fa.ts` — Persian dictionary (defines Dictionary interface)
  - `src/dictionaries/en.ts` — English dictionary
  - `src/dictionaries/ar.ts` — Arabic dictionary
  - `src/lib/i18n.ts` — Locale types, SUPPORTED_LOCALES, getDictionary()
  - `src/lib/direction.ts` — getDirection(), isRTL(), getSlideX(), getIconFlipClass()
- **Middleware** — `src/middleware.ts` — locale detection from cookie/Accept-Language, redirect to /[lang], sets NEXT_LOCALE cookie
- **Root layout** — `src/app/layout.tsx` — reads NEXT_LOCALE cookie, sets `<html lang dir>` server-side (zero RTL flicker)
- **[lang] layout** — validates locale, 404s on unknown lang
- **Splash page** — `src/app/[lang]/page.tsx` — app-like mobile shell, dictionary strings, language switcher
- **Globals CSS** — muted/pale brand palette via Tailwind v4 `@theme {}`, logical spacing, .app-container
- **PWA** — `public/manifest.json`, `public/sw.js`, `public/offline.html`, `public/icons/icon.svg`
- **Service worker registration** — `src/components/service-worker.tsx` (client component)
- **next.config.ts** — Cache-Control headers for sw.js and manifest.json
- **frontend/.env.example** — NEXT_PUBLIC_APP_NAME, NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_DEFAULT_LOCALE, NEXT_PUBLIC_SUPPORTED_LOCALES, NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS

### Backend (`backend/`) — Phase 3
- `app/core/security.py` — JWT create/decode with PyJWT 2.x, naive UTC for SQLite
- `app/schemas/auth.py` — RequestOTPRequest, VerifyOTPRequest, TokenResponse, UserResponse (Pydantic v2)
- `app/repositories/user_repository.py` — get_by_phone, get_by_id, create
- `app/repositories/auth_repository.py` — create_otp, get_latest_valid_otp, mark_otp_used, add_to_blocklist, is_jti_blocked
- `app/services/auth_service.py` — request_otp, verify_otp, logout, get_current_user; SMS mock architecture
- `app/api/dependencies.py` — AuthContext dataclass, get_auth_context, get_current_user FastAPI deps
- `app/api/v1/endpoints/auth.py` — POST /request-otp, POST /verify-otp, POST /logout, GET /me
- Config: added OTP_EXPIRE_MINUTES=5, SMS_PROVIDER=mock
- No new Alembic migration — users, auth_otps, token_blocklist all existed in Phase 1

### Backend (`backend/`) — Phase 4
- `app/models/user.py` — added `is_onboarded: bool = False`
- `alembic/versions/0002_add_user_is_onboarded.py` — migration for new column
- `app/schemas/onboarding.py` — ProfileRequest/Response, MedicalRequest/Response, LifestyleRequest/Response, PreferencesRequest/Response, BehaviorRequest/Response, OnboardingStatusResponse, OnboardingCompleteResponse (Pydantic v2)
- `app/schemas/auth.py` — UserResponse extended with `is_onboarded` field
- `app/repositories/onboarding_repository.py` — upsert_profile, replace_medical_flags, replace_medications, replace_allergies, upsert_warning_symptoms, upsert_lifestyle, upsert_food_preference, upsert_behavior_profile, create_risk_assessment, set_user_onboarded
- `app/services/safety_guardrail_service.py` — assess() returning SafetyAssessment with risk_level (low/medium/high/clinical_review_required) and triggered flags
- `app/services/onboarding_service.py` — get_status, save_profile, save_medical, save_lifestyle, save_preferences, save_behavior, complete_onboarding
- `app/api/v1/endpoints/onboarding.py` — GET /onboarding/status, POST /onboarding/profile, POST /onboarding/medical, POST /onboarding/lifestyle, POST /onboarding/preferences, POST /onboarding/behavior, POST /onboarding/complete
- All 7 endpoints require Bearer token authentication

### Frontend (`frontend/`) — Phase 3
- `src/types/auth.ts` — AuthUser, TokenResponse, ApiSuccess, ApiError types
- `src/lib/storage.ts` — localStorage abstraction (getToken, setToken, clearToken, getStoredUser, setStoredUser)
- `src/lib/api.ts` — typed fetch wrapper with ApiRequestError, BASE_URL from env
- `src/lib/auth.ts` — requestOtp, verifyOtp, logout, getCurrentUser API helpers
- `src/hooks/useAuth.ts` — useAuth hook (user, isLoading, isAuthenticated, logout)
- `src/components/auth/PhoneLoginForm.tsx` — phone input, validation, OTP request, redirects to verify
- `src/components/auth/OtpVerifyForm.tsx` — 6-digit OTP input, countdown timer, resend, verify flow
- `src/components/auth/AuthGuard.tsx` — route protection, redirects to /[lang]/login when unauthenticated
- `src/app/[lang]/login/page.tsx` — login screen (Server Component)
- `src/app/[lang]/login/verify/page.tsx` — OTP verify screen (Server Component), reads phone from query param
- Dictionaries (fa/en/ar) extended with `auth` section (18 strings each)

### Root
- `.env.example`, `.gitignore`, `backend/README.md`, `frontend/README.md`

## Critical Safeguards Verified
- `lazy="raise"` on ALL ORM relationships
- `render_as_batch=True` in both Alembic env.py calls
- `SECRET_KEY` validation at startup
- No hard-coded CORS origins
- No pl-/pr-/ml-/mr- Tailwind classes used (logical properties only)
- Direction set server-side via cookie — no RTL flicker

## Known Issues / Notes
- `middleware.ts` naming is deprecated in Next.js 16 (prefer `proxy.ts`) — rename in Phase 10 polish
- PWA icon uses SVG (browser-supported); Phase 10 should add 192×192 and 512×512 PNGs for iOS
- Token stored in localStorage (not httpOnly cookie) — acceptable for mobile PWA, revisit in Phase 10
- Splash page still shows "Coming Soon" badge — Phase 5 (Onboarding Frontend) will replace with "Get Started" → login

## How to Resume (Cold Start)
1. Read this file + NEXT_STEPS.md
2. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
3. Frontend: `cd frontend && npm run dev` → open http://localhost:3000 → redirects to /fa/login
4. Test auth: POST /api/v1/auth/request-otp → POST /api/v1/auth/verify-otp with OTP 123456
5. Test onboarding: Bearer token → GET /api/v1/onboarding/status → POST /api/v1/onboarding/profile → ...
6. Start Phase 5: `/gsd:plan-phase 5`

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | **COMPLETE** |
| 4 — Onboarding Backend | **COMPLETE** |
| 5 — Onboarding Frontend | Not started |
| 6 — Voice & Audio | Not started |
| 7 — Nutrition Backend & AI Layer | Not started |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

---
*Last updated: 2026-06-03*
