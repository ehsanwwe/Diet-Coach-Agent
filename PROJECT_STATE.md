# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 8 COMPLETE → Phase 9 next
**Overall progress:** Phase 8 of 10 complete (80%)

## What Exists Now

### Backend (`backend/`) — Phases 1, 3, 4, 6, 7, 8 COMPLETE

#### Phase 8 — Companion Chat (NEW)
- `backend/app/schemas/chat.py` — ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
- `backend/app/repositories/chat_repository.py` — companion ChatSession/ChatMessage DB ops
- `backend/app/services/chat_service.py` — send_message() + get_history() using NutritionAgentService
- `backend/app/api/v1/endpoints/chat.py` — POST /chat/message, GET /chat/history (both auth-required)
- `backend/app/api/v1/router.py` — chat_router registered at /chat
- `backend/app/services/mock_ai_provider.py` — TASK_CHAT + _MOCK_CHAT response added
- `backend/app/services/prompt_builder.py` — for_chat_message() added
- `backend/app/services/nutrition_agent_service.py` — chat_message() method added

### Frontend (`frontend/`) — Phases 2, 3, 5, 6, 8 COMPLETE

#### Phase 8 — Nutrition Frontend & Chat (NEW)
- **Dictionaries:** fa.ts / en.ts / ar.ts — extended with dashboard, plan, mealAnalysis, whatToEat, companionChat, safety sections
- **Types:** `src/types/nutrition.ts`, `src/types/chat.ts`
- **API libs:** `src/lib/nutrition.ts` (raw fetch, no SuccessResponse wrapper), `src/lib/chat.ts` (SuccessResponse-wrapped)
- **Hooks:** `src/hooks/useNutritionProfile.ts`
- **Components:**
  - `components/layout/AppBottomNav.tsx` — 4-tab bottom nav (home/chat/progress[disabled]/settings[disabled])
  - `components/nutrition/ClinicalReviewState.tsx` — calm professional safety notice
  - `components/nutrition/NutritionDashboard.tsx` — dashboard with quick actions + plan summary
  - `components/nutrition/PlanSummary.tsx` — full plan display with guidelines + meals
  - `components/nutrition/PlanGenerator.tsx` — generate/regenerate button
  - `components/nutrition/MealAnalysisForm.tsx` — meal text + meal time + context form
  - `components/nutrition/MealAnalysisResult.tsx` — quality score + nutrient breakdown + suggestions
  - `components/nutrition/WhatToEatForm.tsx` — food tag input + hunger + time form
  - `components/nutrition/WhatToEatResult.tsx` — food options cards + reasoning
  - `components/chat/ChatBubble.tsx`, `ChatComposer.tsx`, `CompanionChat.tsx`
- **Pages:**
  - `/[lang]/dashboard` — home screen with AuthGuard + bottom nav
  - `/[lang]/nutrition/plan` — diet plan screen
  - `/[lang]/nutrition/meal-analysis` — meal analysis screen
  - `/[lang]/nutrition/what-to-eat` — what to eat now screen
  - `/[lang]/chat` — companion chat screen
  - `/[lang]` (splash) — updated with Get Started + Dashboard links

## API Endpoints (All Phases)
- GET/POST /api/v1/auth/* — auth
- GET/POST /api/v1/onboarding/* — onboarding
- POST/GET /api/v1/onboarding/chat/* — onboarding habit chat
- GET/POST /api/v1/nutrition/* — nutrition AI layer
- POST /api/v1/chat/message — companion chat send
- GET /api/v1/chat/history — companion chat history

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | **COMPLETE** |
| 4 — Onboarding Backend | **COMPLETE** |
| 5 — Onboarding Frontend | **COMPLETE** |
| 6 — Voice & Audio | **COMPLETE** |
| 7 — Nutrition Backend & AI Layer | **COMPLETE** |
| 8 — Nutrition Frontend & Chat | **COMPLETE** |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

## How to Resume (Cold Start)
1. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm run dev` → open http://localhost:3000
3. Login: POST /api/v1/auth/request-otp → verify-otp with OTP 123456
4. Dashboard: navigate to /fa/dashboard
5. Mock mode: AI_PROVIDER=mock in .env → works without OpenClaw
