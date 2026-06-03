# Architecture Research

**Domain:** AI-powered multilingual nutrition coaching web application
**Researched:** 2026-06-03
**Confidence:** HIGH (patterns well-established; greenfield project with clear spec)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                           │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Pages   │  │ Onboard  │  │  Chat    │  │  Progress/Plan   │   │
│  │ /splash  │  │ 7-step   │  │Companion │  │  Dashboard       │   │
│  │ /login   │  │ wizard   │  │+ Voice   │  │  Meal Analysis   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │             │             │                  │             │
│  ┌────┴─────────────┴─────────────┴──────────────────┴──────────┐  │
│  │              State Layer (Zustand stores)                     │  │
│  │  authStore | onboardingStore | chatStore | progressStore      │  │
│  └────────────────────────────────┬──────────────────────────────┘  │
│                                   │ HTTP / fetch                    │
│  ┌────────────────────────────────┴──────────────────────────────┐  │
│  │              API Client Layer (typed fetch wrappers)           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  i18n Layer: dictionary loader + useTranslation hook         │   │
│  │  dir() utility → <html dir="rtl|ltr" lang="fa|en|ar">        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │ HTTPS REST (JSON + multipart)
┌───────────────────────────────────▼─────────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Routers Layer  (api/v1/)                        │   │
│  │  auth | onboarding | nutrition | chat | progress | audio     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │ calls                                 │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │              Service Layer                                    │   │
│  │  AuthService | OnboardingService | NutritionAgentService     │   │
│  │  ChatService | ProgressService  | AudioService               │   │
│  │  SafetyGuardrailService | NutritionMemoryService             │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │ calls                                 │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │              Repository Layer                                 │   │
│  │  UserRepo | ProfileRepo | ChatRepo | ProgressRepo            │   │
│  │  NutritionRepo | AudioRepo | OnboardingRepo                  │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │ SQLAlchemy 2.x async sessions         │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                   Database Layer                             │   │
│  │           SQLite (dev/v1) → PostgreSQL (future)              │   │
│  │           Alembic migrations (schema versioned)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AI Abstraction Layer (pluggable)                │   │
│  │  AIProvider (ABC) → MockProvider | OpenAIProvider(future)    │   │
│  │  PromptBuilder | NutritionAgentService | ContextAssembler    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Background / Async Tasks                        │   │
│  │  STT Pipeline (async, pluggable): audio → transcription      │   │
│  │  FastAPI BackgroundTasks (dev) → Celery/ARQ (future)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| **Routers** (`api/v1/`) | HTTP surface, request validation via Pydantic schemas, auth dependency injection | Services (never repositories directly) |
| **Services** | Business logic, orchestration, safety rules, AI calls | Repositories, AI Layer, other services |
| **Repositories** | All DB reads/writes, query construction, ORM models | SQLAlchemy session only |
| **AIProvider (ABC)** | Abstract interface for LLM calls: `chat()`, `analyze_meal()` | Called by NutritionAgentService |
| **MockProvider** | Deterministic in-memory responses matching AIProvider interface | Replaces real provider without code changes |
| **SafetyGuardrailService** | Evaluates user medical flags → assigns risk level, blocks unsafe plans | Called before any plan generation or AI response |
| **NutritionMemoryService** | Assembles context window: user profile + medical flags + recent meals + behavior | Called by NutritionAgentService before every AI call |
| **PromptBuilder** | Constructs locale-aware system prompts (Persian food knowledge, safety disclaimers) | Called by NutritionAgentService |
| **AudioService** | Receives multipart upload, persists file, enqueues STT task, returns status | Calls STTProvider (pluggable), writes AudioMessage row |
| **STTProvider (ABC)** | Abstract interface: `transcribe(audio_bytes) → str` | AudioService |
| **OnboardingService** | Stores step data, detects medical flags, triggers risk assessment on complete | SafetyGuardrailService, NutritionMemoryService |
| **i18n Layer (FE)** | Dictionary-based `t()` hook, `dir()` utility, `<html>` attribute management | All React components |
| **Zustand Stores (FE)** | Client state: auth session, onboarding wizard step, chat history slice | Pages, hooks |

---

## Recommended Project Structure

### Backend

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, lifespan, middleware
│   ├── config.py                  # Pydantic Settings from .env
│   ├── database.py                # SQLAlchemy async engine, session factory
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          # APIRouter aggregator
│   │       ├── auth.py            # POST /auth/request-otp, verify-otp, me, logout
│   │       ├── onboarding.py      # POST /onboarding/step/{n}, /complete, /chat/*
│   │       ├── nutrition.py       # GET|POST /nutrition/profile|plan|meal|what-to-eat
│   │       ├── chat.py            # POST /chat/message, GET /chat/history
│   │       ├── progress.py        # POST /progress/check-in, GET /progress/*
│   │       └── audio.py           # POST /audio/upload
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── onboarding_service.py
│   │   ├── nutrition_agent_service.py  # Orchestrates AI calls
│   │   ├── safety_guardrail_service.py # Risk assessment logic
│   │   ├── nutrition_memory_service.py # Context assembly
│   │   ├── chat_service.py
│   │   ├── progress_service.py
│   │   └── audio_service.py
│   │
│   ├── repositories/
│   │   ├── base.py                # Generic CRUD mixin (get, create, update, delete)
│   │   ├── user_repository.py
│   │   ├── profile_repository.py
│   │   ├── onboarding_repository.py
│   │   ├── nutrition_repository.py
│   │   ├── chat_repository.py
│   │   ├── progress_repository.py
│   │   └── audio_repository.py
│   │
│   ├── models/                    # SQLAlchemy ORM models (one file per domain group)
│   │   ├── user.py                # User, AuthOTP
│   │   ├── profile.py             # UserProfile, MedicalCondition, UserMedicalFlag
│   │   │                          # Medication, Allergy, LifestyleProfile
│   │   │                          # FoodPreference, BehaviorProfile
│   │   ├── nutrition.py           # NutritionGoal, NutritionRiskAssessment
│   │   │                          # NutritionPlan, NutritionPlanMeal, MealEntry
│   │   ├── chat.py                # ChatSession, ChatMessage, AudioMessage
│   │   └── progress.py            # DailyCheckIn, ProgressEntry, WeeklyReport
│   │
│   ├── schemas/                   # Pydantic v2 request/response schemas
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── nutrition.py
│   │   ├── chat.py
│   │   └── progress.py
│   │
│   ├── ai/
│   │   ├── base.py                # AIProvider ABC: chat(), analyze_meal(), generate_plan()
│   │   ├── mock_provider.py       # Deterministic mock (Persian-aware responses)
│   │   ├── openai_provider.py     # Stub — wired when OPENAI_API_KEY present
│   │   ├── prompt_builder.py      # System prompt construction, locale injection
│   │   └── context_assembler.py   # Pulls from NutritionMemoryService → message list
│   │
│   ├── audio/
│   │   ├── base.py                # STTProvider ABC: transcribe(bytes) → str
│   │   ├── mock_stt.py            # Returns status="not_configured"
│   │   └── whisper_provider.py    # Stub — wired when OPENAI_API_KEY present
│   │
│   ├── core/
│   │   ├── security.py            # JWT encode/decode, OTP generation
│   │   ├── dependencies.py        # FastAPI Depends: get_db, get_current_user, get_ai_provider
│   │   └── exceptions.py          # Custom HTTP exceptions + handlers
│   │
│   └── migrations/                # Alembic (alembic.ini at backend/ root)
│       ├── env.py
│       └── versions/
│
└── tests/
    ├── unit/
    │   ├── services/
    │   └── ai/
    └── integration/
        └── api/
```

### Frontend

```
frontend/
└── src/
    ├── app/                        # Next.js App Router
    │   ├── layout.tsx              # Root layout: applies dir/lang to <html>
    │   ├── page.tsx                # Splash / landing redirect
    │   ├── (auth)/
    │   │   ├── login/page.tsx      # Phone entry
    │   │   └── verify/page.tsx     # OTP entry
    │   ├── (onboarding)/
    │   │   └── onboarding/
    │   │       ├── layout.tsx      # Step shell: progress bar, animated container
    │   │       └── [step]/page.tsx # Steps 1-7 rendered by step param
    │   ├── (app)/                  # Protected: requires auth
    │   │   ├── home/page.tsx
    │   │   ├── chat/page.tsx
    │   │   ├── plan/page.tsx
    │   │   ├── meal-analysis/page.tsx
    │   │   ├── what-to-eat/page.tsx
    │   │   ├── progress/page.tsx
    │   │   └── settings/page.tsx
    │   └── api/                    # Next.js Route Handlers (thin proxy if needed)
    │
    ├── components/
    │   ├── ui/                     # Primitives: Button, Input, Card, Spinner
    │   ├── onboarding/             # Step components, StepShell, StepProgress
    │   ├── chat/                   # MessageBubble, ChatInput, VoiceRecorder
    │   ├── voice/                  # AudioVisualizer (Web Audio API), WaveformBar
    │   ├── nutrition/              # PlanCard, MealCard, MacroBar
    │   └── progress/               # CheckInForm, WeeklyReport, TrendChart
    │
    ├── stores/                     # Zustand stores
    │   ├── auth.store.ts           # token, user, isAuthenticated
    │   ├── onboarding.store.ts     # currentStep, stepData map, direction
    │   ├── chat.store.ts           # messages[], isStreaming, sessionId
    │   └── progress.store.ts       # checkIns[], weeklyReport
    │
    ├── lib/
    │   ├── api/                    # Typed fetch clients
    │   │   ├── client.ts           # Base fetch with auth header injection
    │   │   ├── auth.api.ts
    │   │   ├── onboarding.api.ts
    │   │   ├── chat.api.ts
    │   │   └── nutrition.api.ts
    │   └── audio/
    │       ├── recorder.ts         # MediaRecorder wrapper: start/pause/stop/cancel
    │       └── visualizer.ts       # Web Audio API AnalyserNode → Uint8Array → canvas
    │
    ├── i18n/
    │   ├── index.ts                # useTranslation() hook, t() function
    │   ├── dir.ts                  # getDir(locale) → "rtl" | "ltr"
    │   ├── fa.ts                   # Persian dictionary (primary, must be complete)
    │   ├── en.ts                   # English dictionary
    │   └── ar.ts                   # Arabic dictionary
    │
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useOnboarding.ts        # Step navigation with direction awareness
    │   ├── useVoiceRecorder.ts     # Stateful recorder + visualizer connection
    │   └── useDirection.ts         # Current dir, isRTL boolean
    │
    └── types/
        ├── api.types.ts            # Request/response shape mirrors
        └── domain.types.ts         # Shared domain enums (RiskLevel, GoalType, etc.)
```

---

## Architectural Patterns

### Pattern 1: Repository / Service Separation (Backend)

**What:** Routers call services only. Services call repositories for data access. Repositories hold all SQLAlchemy query logic. No repository code in routers; no HTTP concern in services.

**When to use:** Any time a route needs business logic beyond a trivial CRUD passthrough. This project needs it everywhere — safety rules, AI orchestration, medical flag evaluation all belong in services.

**Trade-offs:** Slightly more files upfront; pays back when services need testing without HTTP or when business logic changes independently of the DB schema.

**Example:**
```python
# router — validates input, delegates
@router.post("/plan/generate", response_model=NutritionPlanResponse)
async def generate_plan(
    current_user: User = Depends(get_current_user),
    service: NutritionAgentService = Depends(get_nutrition_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.generate_plan(user=current_user, db=db)

# service — business logic, safety check, AI call
class NutritionAgentService:
    async def generate_plan(self, user: User, db: AsyncSession) -> NutritionPlan:
        profile = await self.profile_repo.get_full_profile(user.id, db)
        risk = await self.safety_service.assess_risk(profile)
        if risk.level == RiskLevel.CLINICAL_REVIEW_REQUIRED:
            raise ClinicalReviewRequiredError()
        context = await self.memory_service.assemble_context(profile)
        raw = await self.ai_provider.generate_plan(context)
        return await self.nutrition_repo.save_plan(raw, user.id, db)

# repository — only data access
class NutritionRepository:
    async def save_plan(self, plan_data: dict, user_id: int, db: AsyncSession) -> NutritionPlan:
        plan = NutritionPlan(user_id=user_id, **plan_data)
        db.add(plan)
        await db.commit()
        return plan
```

### Pattern 2: AI Provider Abstraction (Abstract Base Class)

**What:** `AIProvider` defines the interface. `NutritionAgentService` depends on `AIProvider`, never on a concrete class. FastAPI's dependency injection wires the correct provider at startup based on environment config.

**When to use:** From day one. Retrofitting this after tight coupling to OpenAI is a significant rewrite.

**Trade-offs:** One extra file per provider; worth it because mock-first development means the entire application works before a single API key exists.

**Example:**
```python
# ai/base.py
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system_prompt: str) -> str: ...

    @abstractmethod
    async def generate_nutrition_plan(self, context: NutritionContext) -> dict: ...

    @abstractmethod
    async def analyze_meal(self, meal_description: str, locale: str) -> dict: ...

# ai/mock_provider.py
class MockAIProvider(AIProvider):
    async def chat(self, messages, system_prompt):
        last = messages[-1]["content"] if messages else ""
        return MOCK_RESPONSES.get_best_match(last)  # deterministic lookup

# core/dependencies.py
def get_ai_provider() -> AIProvider:
    if settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    return MockAIProvider()
```

### Pattern 3: Safety Guardrail as a First-Class Service

**What:** `SafetyGuardrailService` is called by `OnboardingService` (on completion) and `NutritionAgentService` (before any plan generation or AI response). It is never bypassed by routers.

**When to use:** Everywhere a diet plan or nutritional advice is generated. Safety logic must not live in the router or be inlined into AI prompts — it must be testable in isolation.

**Trade-offs:** Adds one indirection; worth it because safety rules will evolve (new medical conditions, stricter pregnancy rules) and must be auditable.

**Example:**
```python
class SafetyGuardrailService:
    CLINICAL_FLAGS = {
        "diabetes_with_medication", "kidney_disease",
        "pregnancy", "eating_disorder", "bariatric_surgery",
    }

    async def assess_risk(self, profile: FullProfile) -> RiskAssessment:
        flags = {f.condition for f in profile.medical_flags}
        if flags & self.CLINICAL_FLAGS:
            return RiskAssessment(level=RiskLevel.CLINICAL_REVIEW_REQUIRED, reason=...)
        if profile.serious_symptoms:
            return RiskAssessment(level=RiskLevel.HIGH, reason=...)
        return RiskAssessment(level=RiskLevel.LOW)
```

### Pattern 4: Onboarding Wizard State Machine (Frontend)

**What:** `onboardingStore` (Zustand) tracks `currentStep` (1–7), `stepData` (a keyed map), and `direction` ("forward" | "backward"). Step navigation mutates `direction` before updating `currentStep` so the animation knows which way to slide.

**When to use:** Any multi-step flow longer than 3 steps where direction-aware animations and partial-save semantics are needed.

**Trade-offs:** More store complexity than a simple counter; necessary here because the 7 steps have RTL-mirrored slide directions and partial data must persist across accidental navigations.

**Example:**
```typescript
// stores/onboarding.store.ts
interface OnboardingStore {
  currentStep: number;          // 1..7
  direction: "forward" | "backward";
  stepData: Record<number, StepPayload>;
  goToStep: (target: number) => void;
  setStepData: (step: number, data: StepPayload) => void;
}

// hooks/useOnboarding.ts
export function useOnboarding() {
  const { currentStep, direction, goToStep } = useOnboardingStore();
  const { isRTL } = useDirection();

  // Natural RTL: "forward" slides from LEFT (enter) for RTL, RIGHT for LTR
  const enterFrom = direction === "forward"
    ? (isRTL ? "-100%" : "100%")
    : (isRTL ? "100%" : "-100%");

  return { currentStep, enterFrom, goToStep };
}
```

### Pattern 5: Dictionary-Based i18n with CSS Logical Properties

**What:** A plain TypeScript dictionary (`fa.ts`, `en.ts`, `ar.ts`) with a `useTranslation()` hook and a `getDir(locale)` utility. The root `layout.tsx` sets `<html dir={dir} lang={locale}>`. All CSS uses logical properties (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`) — never `margin-left` or `padding-right`.

**When to use:** When RTL is a first-class requirement and the team wants full control without next-intl or i18next build complexity.

**Trade-offs:** More manual work than a library; in this project that trade-off is accepted intentionally (see PROJECT.md Key Decisions). The risk is missing a translation key — mitigated by a TypeScript union type over the dictionary keys.

**Example:**
```typescript
// i18n/index.ts
type Locale = "fa" | "en" | "ar";
const dictionaries = { fa, en, ar };

export function useTranslation() {
  const locale = useLocaleStore(s => s.locale) as Locale;
  const dict = dictionaries[locale];
  return { t: (key: keyof typeof fa) => dict[key] ?? fa[key], locale };
}

// i18n/dir.ts
export const getDir = (locale: Locale): "rtl" | "ltr" =>
  locale === "fa" || locale === "ar" ? "rtl" : "ltr";
```

### Pattern 6: Audio Upload / STT Pipeline (Async, Pluggable)

**What:** The browser records via MediaRecorder API, sends a multipart POST to `/api/v1/onboarding/chat/audio`. The `AudioService` saves the file, creates an `AudioMessage` row with `status="pending"`, and enqueues a background task. The STT provider interface mirrors the AI provider pattern (ABC + mock). In dev, the mock returns `status="not_configured"` immediately. The frontend polls `GET /audio/{id}/status` until terminal state.

**When to use:** Whenever audio processing is async (transcription can take seconds). Keeps the upload endpoint snappy.

**Trade-offs:** Status polling adds one extra request; avoids blocking the HTTP response on a slow STT call.

**Example:**
```python
# audio/base.py
class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str) -> STTResult: ...

# audio/mock_stt.py
class MockSTTProvider(STTProvider):
    async def transcribe(self, audio_bytes, language):
        return STTResult(status="not_configured", text=None)

# services/audio_service.py
async def upload_audio(file: UploadFile, user_id: int, db: AsyncSession) -> AudioMessage:
    path = await save_to_disk(file)
    msg = await self.audio_repo.create(user_id=user_id, path=path, status="pending")
    background_tasks.add_task(self._transcribe, msg.id)
    return msg
```

---

## Data Flow

### Request Flow: AI-Assisted Chat Message

```
User types/sends message
    ↓
ChatInput component → chatStore.sendMessage(text)
    ↓
lib/api/chat.api.ts → POST /api/v1/chat/message {text, session_id}
    ↓
chat router → Depends(get_current_user) → ChatService.handle_message()
    ↓
ChatService → NutritionMemoryService.assemble_context(user)
    ↓                           ↓
    │              [reads: NutritionProfile, recent meals,
    │               behavior flags, last N messages from ChatRepo]
    ↓
ChatService → SafetyGuardrailService.assess_risk(profile)
    ↓ (risk == LOW or MEDIUM)
ChatService → NutritionAgentService.chat(context, user_message)
    ↓
NutritionAgentService → PromptBuilder.build_system_prompt(profile, locale)
    ↓
NutritionAgentService → AIProvider.chat(messages)   ← Mock or real
    ↓
Response text returned
    ↓
ChatService → ChatRepository.save_message(user_msg, assistant_msg)
    ↓
Response schema → JSON response
    ↓
chatStore updates messages[] → MessageBubble renders
```

### Request Flow: Onboarding Step Submission

```
User fills step N form → "Next" clicked
    ↓
onboardingStore.setStepData(N, formValues) + goToStep(N+1)
    ↓ (in parallel)
lib/api/onboarding.api.ts → POST /api/v1/onboarding/step/{N} {data}
    ↓
onboarding router → OnboardingService.save_step(user, step_n, data)
    ↓
OnboardingService → OnboardingRepository.upsert_step_data()
    ↓ (on step 3 — medical screening)
OnboardingService → SafetyGuardrailService.flag_medical_conditions(data)
    → UserMedicalFlag rows created
    ↓
Animation plays (direction-aware slide) while API call is in flight
```

### Request Flow: Audio Voice Message

```
User presses record → MediaRecorder starts
    ↓
Web Audio API AnalyserNode → AudioVisualizer component (canvas animation)
    ↓
User presses stop → MediaRecorder produces Blob
    ↓
AudioPreview shown → User presses send
    ↓
FormData(blob) → POST /api/v1/onboarding/chat/audio
    ↓
AudioService.upload() → file saved to disk → AudioMessage(status="pending")
    ↓
BackgroundTask: STTProvider.transcribe(bytes) → update AudioMessage(status="done"|"not_configured")
    ↓
Frontend polls GET /audio/{id}/status every 2s → renders transcription or "voice message"
```

### State Management

```
Zustand Stores (client-side)
─────────────────────────────
authStore
  token (persisted localStorage)
  user { id, phone, name, language }
  ↓ injected into
  api/client.ts (Authorization header)

onboardingStore
  currentStep: 1..7
  direction: "forward" | "backward"
  stepData: { 1: {...}, 2: {...}, ... }
  ↓ consumed by
  onboarding/[step]/page.tsx
  useOnboarding() hook (animation direction)

chatStore
  sessionId
  messages: ChatMessage[]
  isLoading: boolean
  ↓ consumed by
  chat/page.tsx
  MessageBubble, ChatInput, VoiceRecorder

progressStore
  recentCheckIns[]
  weeklyReport | null
  ↓ consumed by
  progress/page.tsx
```

---

## Build Order

Components have hard dependencies that dictate a rational build sequence:

### Tier 0 — Foundations (must exist before anything else)

1. **Monorepo scaffolding** — directory layout, .env.example, .gitignore
2. **Database models + Alembic** — all ORM models and initial migration; every other backend component depends on this
3. **FastAPI app factory + config** — `main.py`, `config.py`, `database.py`, `core/dependencies.py`
4. **Base repository mixin** — generic CRUD; all domain repositories extend this
5. **Next.js project + Tailwind** — App Router skeleton, root layout, CSS logical-properties baseline
6. **i18n layer** — dictionaries + `useTranslation()` + `getDir()`; every UI component needs this from the start

### Tier 1 — Auth (unblocks everything user-scoped)

7. **Auth models + AuthService + AuthRepository** — User, AuthOTP, JWT logic
8. **Auth routers** — `/auth/request-otp`, `/verify-otp`, `/me`, `/logout`
9. **Frontend auth flow** — login/verify pages, authStore, API client with token injection, route guards

### Tier 2 — Onboarding (delivers the data that AI and nutrition depend on)

10. **Profile models + OnboardingRepository + OnboardingService**
11. **SafetyGuardrailService** — standalone, testable, no AI dependency; must exist before onboarding completes
12. **Onboarding routers** — step endpoints + `/complete`
13. **Frontend onboarding wizard** — 7-step shell, stepData store, direction-aware animations
14. **NutritionMemoryService** — depends on all profile models being populated by onboarding

### Tier 3 — AI Layer (depends on profile + memory)

15. **AIProvider ABC + MockProvider** — no external dependencies; enables all AI paths immediately
16. **PromptBuilder + ContextAssembler** — depends on NutritionMemoryService
17. **NutritionAgentService** — wires all AI components together
18. **Nutrition routers** — profile, plan, meal-analyze, what-to-eat-now

### Tier 4 — Chat + Voice (depends on AI layer)

19. **ChatService + ChatRepository + chat router**
20. **Frontend chat UI** — MessageBubble, ChatInput, chatStore
21. **AudioService + STTProvider ABC + MockSTT**
22. **Audio router** (`/onboarding/chat/audio`, `/audio/{id}/status`)
23. **Frontend VoiceRecorder + AudioVisualizer** — MediaRecorder wrapper, Web Audio API visualizer

### Tier 5 — Progress + Reports (depends on core profile + chat being live)

24. **ProgressService + ProgressRepository + progress router**
25. **Frontend progress dashboard** — CheckInForm, WeeklyReport, TrendChart

### Tier 6 — Polish + Settings

26. **Settings page** — language switcher, profile edit
27. **Medical safety notice screen** — triggered by CLINICAL_REVIEW_REQUIRED risk level
28. **RTL animation polish** — verify all slide directions, icon mirroring, logical-property audit

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0–500 users | Monolith as described; SQLite; FastAPI BackgroundTasks for STT; single Uvicorn process |
| 500–10k users | Swap SQLite → PostgreSQL (Alembic migration; connection string change only); add connection pooling (asyncpg); move background tasks to Celery + Redis |
| 10k–100k users | Add Redis for chat session cache; consider read replica for progress queries; add CDN for audio files (S3 + presigned URLs instead of local disk) |
| 100k+ users | Extract AI/STT as separate service; rate-limit AI calls per user; horizontal FastAPI scaling behind load balancer |

### Scaling Priorities

1. **First bottleneck:** SQLite write contention under concurrent users → swap to PostgreSQL (prepared by Alembic from day 1)
2. **Second bottleneck:** AI API latency blocking HTTP responses → streaming responses (`StreamingResponse` + `async for` from OpenAI) or job-queue pattern
3. **Third bottleneck:** Audio file storage on local disk → replace `save_to_disk()` with S3-compatible object store; `AudioService` interface does not change

---

## Anti-Patterns

### Anti-Pattern 1: Router Calling Repository Directly

**What people do:** Skip the service layer for "simple" CRUD endpoints (e.g., get profile), calling `ProfileRepository` directly from the router.

**Why it's wrong:** Safety checks and memory assembly live in services. A router that bypasses services will silently skip safety guardrails. One inconsistency like this causes a clinical safety violation.

**Do this instead:** Every router endpoint calls a service method, even if the service is a thin pass-through today.

### Anti-Pattern 2: Tight Coupling to a Single AI Provider

**What people do:** Import `openai` directly in `NutritionAgentService` and call `openai.chat.completions.create()` inline.

**Why it's wrong:** App breaks without an API key, making development painful and testing impossible without hitting real APIs.

**Do this instead:** `AIProvider` ABC + `MockProvider` from the first AI commit. The mock must return realistic Persian nutrition responses, not just "OK".

### Anti-Pattern 3: Hard-Coded `left`/`right` CSS

**What people do:** Write `margin-left: 16px`, `padding-right: 8px`, `left: 0` in component styles.

**Why it's wrong:** RTL layout breaks silently. With Persian as the primary language, most users see a broken layout.

**Do this instead:** Use CSS logical properties exclusively: `margin-inline-start`, `padding-inline-end`, `inset-inline-start`. Set `dir` on `<html>` and let the browser handle mirroring.

### Anti-Pattern 4: Storing AI Context in the LLM's "Memory"

**What people do:** Rely on the conversation history array alone for context, appending all past messages to every request.

**Why it's wrong:** Token limits are hit quickly; medical flags from step 3 of onboarding are no longer in the recent window after 20 messages.

**Do this instead:** `NutritionMemoryService` assembles a structured context (profile snapshot + medical flags + behavior profile + last N messages) into a system-prompt prefix before every AI call. Medical safety data is always injected, regardless of conversation length.

### Anti-Pattern 5: Global Onboarding State in URL Only

**What people do:** Use URL params (`/onboarding?step=3`) as the only state, reading form values from query strings.

**Why it's wrong:** Step data is lost on refresh or accidental navigation; direction-aware animation requires knowing the previous step, which URL state does not track.

**Do this instead:** Zustand `onboardingStore` as the source of truth for step data and animation direction. The URL reflects the current step for shareability; the store holds the data.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| AI Provider (OpenAI/Claude) | `AIProvider` ABC; configured via `OPENAI_API_KEY` env; falls back to mock when absent | Never imported directly in services |
| STT Provider (Whisper/Deepgram) | `STTProvider` ABC; async background task; `status` field on `AudioMessage` | Returns "not_configured" in dev |
| SMS Provider (Kavenegar/Twilio) | `SMSProvider` interface in `AuthService`; default dev implementation logs OTP to console | OTP hardcoded to 123456 in dev |
| PostgreSQL | Same SQLAlchemy 2.x models; change `DATABASE_URL` in `.env`; run `alembic upgrade head` | No code changes required |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Router → Service | Direct async method call; service injected via `Depends()` | Routers never import repositories |
| Service → Repository | Direct async method call; `AsyncSession` passed from router dependency | Repositories never call other repositories |
| Service → AIProvider | Via `Depends(get_ai_provider)` injected into service constructor | Provider swappable without service changes |
| NutritionAgentService → SafetyGuardrailService | Direct method call; safety always runs before AI | Safety is synchronous; no DB writes |
| NutritionAgentService → NutritionMemoryService | Direct method call; returns assembled context dict | Memory service reads but never writes |
| Frontend Store → API Client | Store actions call `lib/api/*.ts` functions; stores hold loading/error state | No direct `fetch()` in components |
| Frontend i18n → Root Layout | `useLocaleStore` → `getDir(locale)` → `<html dir>` update on locale change | `layout.tsx` reads locale from cookie or store hydration |

---

## Sources

- FastAPI official documentation — dependency injection, BackgroundTasks, async sessions: https://fastapi.tiangolo.com/
- SQLAlchemy 2.x async docs — AsyncSession, async engine: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Next.js App Router — layout, route groups, dynamic routes: https://nextjs.org/docs/app
- MDN Web Audio API — AnalyserNode, getByteTimeDomainData: https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode
- MDN MediaRecorder API — start/stop/ondataavailable: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder
- CSS Logical Properties (MDN) — margin-inline, padding-inline, inset-inline: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values
- Zustand documentation — store creation, persist middleware: https://docs.pmnd.rs/zustand
- Project specification: .planning/PROJECT.md (2026-06-03)

---
*Architecture research for: AI-powered multilingual diet coaching agent*
*Researched: 2026-06-03*
