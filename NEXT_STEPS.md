# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 3 COMPLETE. Phase 4 (Onboarding Backend) ready to start.

## Immediate Next Action

**Start Phase 4: Onboarding Backend**

Command: `/gsd:plan-phase 4` (then `/gsd:execute-phase 4`)

## What Phase 4 Builds

Backend onboarding data collection endpoints:
- `POST /api/v1/onboarding/profile` — name, gender, age, height, weight, activity level
- `POST /api/v1/onboarding/medical` — medical flags, medications, allergies
- `POST /api/v1/onboarding/lifestyle` — dietary preferences, food dislikes, meal frequency
- `POST /api/v1/onboarding/goals` — weight goal, target weight, timeline
- `GET /api/v1/onboarding/status` — which steps are complete
- All endpoints require authentication via Bearer token (use `get_current_user` dep)

## Auth Flow (Working Now)

1. `POST /api/v1/auth/request-otp` — phone_number → OTP 123456 in dev
2. `POST /api/v1/auth/verify-otp` — phone_number + otp_code → access_token + user
3. Frontend: `/fa/login` → `/fa/login/verify?phone=...` → redirects to `/fa`
4. Token stored in localStorage via `src/lib/storage.ts`

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. ✅ i18n & Frontend Shell (COMPLETE)
3. ✅ Authentication (COMPLETE)
4. → Onboarding Backend (NEXT)
5. Onboarding Frontend (after Phase 4)
6. Voice & Audio (after Phase 5)
7. Nutrition Backend & AI Layer (after Phase 4)
8. Nutrition Frontend & Chat (after Phase 7)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
