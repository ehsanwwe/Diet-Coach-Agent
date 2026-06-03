# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 7 COMPLETE. Phase 8 (Nutrition Frontend & Chat) ready to start.

## Immediate Next Action

**Start Phase 8: Nutrition Frontend & Chat**

Command: `/gsd:plan-phase 8` (then `/gsd:execute-phase 8`)

## What Phase 8 Builds

Nutrition frontend screens wired to Phase 7 backend:
- Nutrition dashboard screen (active plan display)
- Meal log / analyze screen (text input → MealAnalysisResponse)
- "What to eat now" quick suggestion screen
- Nutrition chat screen (persistent companion session)
- Plan adapt flow (feedback → AdaptPlanResponse)
- Risk-level-aware UI messaging (clinical review prompts)

## Current Nutrition API (Working Now — Phase 7)

All endpoints require `Authorization: Bearer <token>`.

1. `GET  /api/v1/nutrition/profile` — full profile summary
2. `GET  /api/v1/nutrition/plan` — current active plan
3. `POST /api/v1/nutrition/plan/generate` — generate plan
4. `POST /api/v1/nutrition/meal/analyze` — analyze meal + log
5. `POST /api/v1/nutrition/what-to-eat-now` — quick food suggestions
6. `POST /api/v1/nutrition/adapt-plan` — adapt plan from feedback

## Provider Behavior (Phase 7)

- `AI_PROVIDER=mock` → MockAIProvider (no external calls, always works)
- `AI_PROVIDER=openclaw` + `OPENCLAW_BASE_URL` → OpenClawProvider
- Auto-fallback to mock on provider failure
- Clinical-review users: wellness guidance only (no aggressive plan)

## Known Limitations (Phase 7)

- No nutrition chat session (POST /nutrition/chat) — will be Phase 8.
- No history endpoint — will be Phase 8.
- No image meal analysis — out of scope.
- No STT in meal analysis — out of scope.

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. ✅ i18n & Frontend Shell (COMPLETE)
3. ✅ Authentication (COMPLETE)
4. ✅ Onboarding Backend (COMPLETE)
5. ✅ Onboarding Frontend (COMPLETE)
6. ✅ Voice & Audio (COMPLETE)
7. ✅ Nutrition Backend & AI Layer (COMPLETE)
8. → Nutrition Frontend & Chat (NEXT)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
