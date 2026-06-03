# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 6 COMPLETE → Phase 7 next
**Overall progress:** Phase 6 of 10 complete (60%)

## What Exists Now

### Backend (`backend/`) — Phases 1, 3, 4, 6 COMPLETE
- Full ORM models, Alembic migrations, FastAPI shell
- Auth: OTP login, JWT, logout, /me
- Onboarding: GET /status, POST /profile /medical /lifestyle /preferences /behavior /complete
- Safety guardrail service (risk_level, clinical_review_required)
- **Onboarding Chat (Phase 6 NEW):**
  - `POST /api/v1/onboarding/chat/text` — send text message, returns user + placeholder assistant message
  - `POST /api/v1/onboarding/chat/audio` — upload multipart audio file, stores locally, returns metadata
  - `GET /api/v1/onboarding/chat/history` — returns all text + audio history for user's onboarding session
  - `backend/app/schemas/onboarding_chat.py` — Pydantic v2 schemas
  - `backend/app/repositories/onboarding_chat_repository.py` — DB ops (ChatSession, ChatMessage, AudioMessage)
  - `backend/app/services/audio_storage_service.py` — local file storage, MIME validation, size validation
  - `backend/app/services/onboarding_chat_service.py` — business logic, no AI
  - `backend/app/api/v1/endpoints/onboarding_chat.py` — 3 authenticated endpoints
  - Audio stored under `backend/storage/audio/` (gitignored)
  - No STT/transcription (transcription_status = "not_configured")
  - No AI/OpenClaw (placeholder assistant response)

### Frontend (`frontend/`) — Phases 2, 3, 5, 6 COMPLETE

#### Phase 2 — i18n & Shell
- Dictionary system (fa/en/ar), middleware locale detection, RTL direction utils, PWA

#### Phase 3 — Authentication
- Phone OTP login, JWT storage, AuthGuard, useAuth hook

#### Phase 5 — Onboarding Frontend
- 7-step animated wizard

#### Phase 6 — Voice & Audio (NEW)
- `src/types/onboardingChat.ts` — TypeScript types for all 3 endpoints
- `src/lib/onboardingChat.ts` — typed API client (sendTextMessage, uploadAudio, getChatHistory)
- `src/lib/media.ts` — MIME type detection, MediaRecorder support check, duration formatter
- `src/hooks/useAudioRecorder.ts` — MediaRecorder hook with Web Audio AnalyserNode, state machine, cleanup
- `src/components/audio/AudioWaveform.tsx` — Canvas waveform via AnalyserNode
- `src/components/audio/AudioPreview.tsx` — playback preview with progress bar
- `src/components/audio/AudioRecorder.tsx` — full recorder UI (idle/requesting/recording/stopped/error)
- `src/components/onboarding/OnboardingHabitChat.tsx` — chat UI with text + voice, history display
- Updated `steps/FinalVideoStep.tsx` — integrates OnboardingHabitChat, enabled after video watched
- Dictionaries extended with `audio` section (fa/en/ar, 23 keys each)

## Critical Safeguards Verified
- All 3 onboarding chat endpoints require Authentication (Bearer token)
- AUDIO_STORAGE_PATH configurable via env var (default: ./storage/audio)
- Audio storage path gitignored (backend/storage/)
- MIME type validation: rejects non-audio formats
- File size validation: configurable MAX_AUDIO_UPLOAD_MB (default: 20)
- Absolute filesystem paths never returned to client (storage_key only)
- No STT calls, no AI calls — Phase 06 scope respected
- Frontend chat disabled until video watched (dev bypass still works)
- No hard-coded Persian text — all from dictionaries

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | **COMPLETE** |
| 4 — Onboarding Backend | **COMPLETE** |
| 5 — Onboarding Frontend | **COMPLETE** |
| 6 — Voice & Audio | **COMPLETE** |
| 7 — Nutrition Backend & AI Layer | Not started |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

## How to Resume (Cold Start)
1. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm run dev` → open http://localhost:3000
3. Login: POST /api/v1/auth/request-otp → verify-otp with OTP 123456 → redirected to /fa/onboarding
4. Onboarding: 7-step wizard → final step → mark video watched → use text/voice chat
5. Audio upload test: `curl -X POST http://localhost:8000/api/v1/onboarding/chat/audio -H "Authorization: Bearer <token>" -F "file=@test.webm"`
