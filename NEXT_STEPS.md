# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 2 COMPLETE. Phase 3 (Authentication) ready to start.

## Immediate Next Action

**Start Phase 3: Authentication**

Command: `/gsd:plan-phase 3` (then `/gsd:execute-phase 3`)

## What Phase 3 Builds

Backend + Frontend authentication via Phone OTP:
- `POST /api/v1/auth/request-otp` — accepts phone number, creates AuthOTP record
- `POST /api/v1/auth/verify-otp` — validates OTP (dev: 123456), returns JWT
- `POST /api/v1/auth/logout` — invalidates token via jti blocklist
- `GET /api/v1/auth/me` — returns current user profile
- Auth screens: `/fa/auth/login` (phone input), `/fa/auth/verify` (OTP input)
- JWT stored in httpOnly cookie
- Route guard: redirect unauthenticated users to /[lang]/auth/login

## First Files to Touch in Phase 3

1. `backend/app/api/v1/auth.py` — OTP + JWT endpoints
2. `backend/app/services/auth_service.py` — OTP generation, JWT encode/decode
3. `backend/app/repositories/user_repository.py` — find/create user
4. `frontend/src/app/[lang]/auth/login/page.tsx` — phone number input screen
5. `frontend/src/app/[lang]/auth/verify/page.tsx` — OTP entry screen

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. ✅ i18n & Frontend Shell (COMPLETE)
3. → Authentication (NEXT)
4. Onboarding Backend (after Phase 3)
5. Onboarding Frontend (after Phase 4)
6. Voice & Audio (after Phase 5)
7. Nutrition Backend & AI Layer (after Phase 4)
8. Nutrition Frontend & Chat (after Phase 7)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
