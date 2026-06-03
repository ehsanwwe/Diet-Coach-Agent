# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 5 COMPLETE → Phase 6 next
**Overall progress:** Phase 5 of 10 complete (50%)

## What Exists Now

### Backend (`backend/`) — Phases 1, 3, 4 COMPLETE
- Full ORM models, Alembic migrations, FastAPI shell
- Auth: OTP login, JWT, logout, /me
- Onboarding: GET /status, POST /profile /medical /lifestyle /preferences /behavior /complete
- Safety guardrail service (risk_level, clinical_review_required)

### Frontend (`frontend/`) — Phases 2, 3, 5 COMPLETE

#### Phase 2 — i18n & Shell
- Dictionary system (fa/en/ar), middleware locale detection, RTL direction utils, PWA

#### Phase 3 — Authentication
- Phone OTP login, JWT storage, AuthGuard, useAuth hook

#### Phase 5 — Onboarding Frontend (NEW)
- `src/types/onboarding.ts` — typed API shapes matching Phase 4 backend
- `src/lib/onboarding.ts` — typed API client (7 functions)
- `src/lib/cn.ts` — cn() utility (clsx + tailwind-merge)
- Dictionaries extended with full `onboarding` section (fa/en/ar, ~80 keys each)
- `src/components/onboarding/` — complete wizard:
  - `OnboardingWizard.tsx` — state manager, API calls, Framer Motion transitions
  - `OnboardingShell.tsx` — header + progress bar shell
  - `OnboardingProgress.tsx` — animated dots + bar
  - `ClinicalReviewNotice.tsx` — medical safety banner
  - `TagInput.tsx` — reusable tag/chip input
  - `steps/ProfileStep.tsx` — name, gender, age, height, weight
  - `steps/GoalStep.tsx` — UI-only goal selection (11 goals)
  - `steps/MedicalStep.tsx` — conditions, medications, allergies, symptoms
  - `steps/LifestyleStep.tsx` — sleep/stress sliders, schedule/activity selects
  - `steps/PreferencesStep.tsx` — dietary toggles, food tag inputs, frequency pickers
  - `steps/BehaviorStep.tsx` — eating habits, cravings, motivation slider
  - `steps/FinalVideoStep.tsx` — video placeholder + dev bypass + complete
- `src/app/[lang]/onboarding/page.tsx` — server component entry point
- New packages: framer-motion, react-hook-form, lucide-react, clsx, tailwind-merge, zod, @hookform/resolvers

## Critical Safeguards Verified
- All backend API calls authenticated with Bearer token
- AuthGuard redirects unauthenticated users to /[lang]/login
- If is_onboarded=true, wizard redirects to /[lang] immediately
- Clinical review notice shown when risk_level=clinical_review_required
- Video "dev bypass" button gated by NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS env var
- Final complete button disabled until video is marked watched
- No hard-coded Persian text in components — all from dictionaries
- RTL/LTR direction-aware Framer Motion slide transitions
- No pl-/pr-/ml-/mr- Tailwind classes used

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | **COMPLETE** |
| 4 — Onboarding Backend | **COMPLETE** |
| 5 — Onboarding Frontend | **COMPLETE** |
| 6 — Voice & Audio | Not started |
| 7 — Nutrition Backend & AI Layer | Not started |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

## How to Resume (Cold Start)
1. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm run dev` → open http://localhost:3000
3. Login: POST /api/v1/auth/request-otp → verify-otp with OTP 123456 → redirected to /fa/onboarding
4. Onboarding: 7-step wizard → POST each step → final video → complete
