# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 4 COMPLETE. Phase 5 (Onboarding Frontend) ready to start.

## Immediate Next Action

**Start Phase 5: Onboarding Frontend**

Command: `/gsd:plan-phase 5` (then `/gsd:execute-phase 5`)

## What Phase 5 Builds

7-step animated onboarding UI consuming the Phase 4 backend APIs:
- Step 1: Basic profile (name, gender, age/DOB, height, weight, target weight)
- Step 2: Medical safety screening (conditions, medications, allergies, symptoms)
- Step 3: Lifestyle (sleep, stress, work, activity, exercise, cooking, budget)
- Step 4: Food preferences (Iranian foods, veg/vegan, halal, dislikes, favorites)
- Step 5: Behavior patterns (emotional eating, cravings, diet history, motivation)
- Step 6: Summary + complete (risk level display, clinical review notice if needed)
- Direction-aware RTL/LTR slide animations (Framer Motion)
- All POST calls to `/api/v1/onboarding/*` with Bearer token

## Onboarding API (Working Now — Phase 4)

All endpoints require `Authorization: Bearer <token>`.

1. `GET  /api/v1/onboarding/status` — completed steps, next_step, risk_level
2. `POST /api/v1/onboarding/profile` — name, gender, age/birth_date, height, weight
3. `POST /api/v1/onboarding/medical` — conditions, medications, allergies, symptoms → risk_level
4. `POST /api/v1/onboarding/lifestyle` — sleep, stress, activity, cooking, budget
5. `POST /api/v1/onboarding/preferences` — Iranian food, veg/vegan, halal, favorites
6. `POST /api/v1/onboarding/behavior` — emotional eating, cravings, motivation
7. `POST /api/v1/onboarding/complete` — finalizes onboarding, sets is_onboarded=true

## Auth Flow (Working Now — Phase 3)

1. `POST /api/v1/auth/request-otp` — phone_number → OTP 123456 in dev
2. `POST /api/v1/auth/verify-otp` — phone_number + otp_code → access_token + user (includes is_onboarded)
3. Frontend: `/fa/login` → `/fa/login/verify?phone=...` → redirects to `/fa`
4. Token stored in localStorage via `src/lib/storage.ts`

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. ✅ i18n & Frontend Shell (COMPLETE)
3. ✅ Authentication (COMPLETE)
4. ✅ Onboarding Backend (COMPLETE)
5. → Onboarding Frontend (NEXT)
6. Voice & Audio (after Phase 5)
7. Nutrition Backend & AI Layer (after Phase 4)
8. Nutrition Frontend & Chat (after Phase 7)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
