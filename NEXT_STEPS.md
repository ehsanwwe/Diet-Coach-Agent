# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 6 COMPLETE. Phase 7 (Nutrition Backend & AI Layer) ready to start.

## Immediate Next Action

**Start Phase 7: Nutrition Backend & AI Layer**

Command: `/gsd:plan-phase 7` (then `/gsd:execute-phase 7`)

## What Phase 7 Builds

Full AI nutrition layer:
- `AIProvider` ABC with `OpenClawProvider` (OpenAI-compatible) and `MockAIProvider` fallback
- `NutritionMemoryService` — builds `NutritionMemoryContext` from user profile
- `PromptBuilder` — token-safe history pruning, rolling summaries when enabled
- `NutritionAgentService` — orchestrates full AI call pipeline
- `SafetyGuardrailService` injected on every AI endpoint
- All 6 nutrition endpoints:
  1. `POST /api/v1/nutrition/plan/generate`
  2. `POST /api/v1/nutrition/chat`
  3. `POST /api/v1/nutrition/meal/analyze`
  4. `POST /api/v1/nutrition/what-to-eat-now`
  5. `GET  /api/v1/nutrition/plan`
  6. `GET  /api/v1/nutrition/history`

## Onboarding Chat API (Working Now — Phase 6)

All endpoints require `Authorization: Bearer <token>`.

1. `POST /api/v1/onboarding/chat/text` — sends text, returns user + placeholder assistant message
2. `POST /api/v1/onboarding/chat/audio` — uploads multipart audio, stores locally, returns metadata
3. `GET /api/v1/onboarding/chat/history` — full onboarding chat history

Audio storage: `backend/storage/audio/` (gitignored, configurable via AUDIO_STORAGE_PATH)
STT: Not implemented yet (transcription_status = "not_configured")

## Known Limitations (Phase 6)

- No speech-to-text. Audio is stored but not transcribed.
- Assistant responses are placeholder Persian text — no AI.
- Audio playback in history shows metadata only (no re-download endpoint yet).

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. ✅ i18n & Frontend Shell (COMPLETE)
3. ✅ Authentication (COMPLETE)
4. ✅ Onboarding Backend (COMPLETE)
5. ✅ Onboarding Frontend (COMPLETE)
6. ✅ Voice & Audio (COMPLETE)
7. → Nutrition Backend & AI Layer (NEXT)
8. Nutrition Frontend & Chat (after Phase 7)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
