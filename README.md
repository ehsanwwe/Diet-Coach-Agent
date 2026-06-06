# Diet Coach Agent

<p align="center">
  <img alt="Project Status" src="https://img.shields.io/badge/status-active_development-2ea44f?style=for-the-badge">
  <img alt="Backend" src="https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white">
  <img alt="TypeScript" src="https://img.shields.io/badge/typescript-strict-3178C6?style=for-the-badge&logo=typescript&logoColor=white">
  <img alt="Database" src="https://img.shields.io/badge/database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
</p>

<p align="center">
  <img alt="GitHub License" src="https://img.shields.io/github/license/ehsanwwe/Diet-Coach-Agent?style=flat-square">
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/ehsanwwe/Diet-Coach-Agent?style=flat-square">
  <img alt="Repo Size" src="https://img.shields.io/github/repo-size/ehsanwwe/Diet-Coach-Agent?style=flat-square">
  <img alt="Issues" src="https://img.shields.io/github/issues/ehsanwwe/Diet-Coach-Agent?style=flat-square">
</p>

## Overview

**Diet Coach Agent** is a production-oriented multilingual nutrition and wellness companion designed to help users build healthier eating habits, complete a structured nutrition onboarding flow, record personal health context, and receive safe, adaptive guidance through a modern mobile-first experience.

The project is built with a clear separation between backend and frontend, migration-managed data models, authenticated user flows, multilingual UI, RTL/LTR support, and a scalable architecture prepared for future nutrition intelligence, voice input, meal analysis, progress tracking, and professional review workflows.

This repository is designed with long-term maintainability in mind: clean structure, typed code, explicit environment configuration, database migrations, modular service/repository layers, and a frontend experience suitable for real product delivery.

---

## Product Positioning

Diet Coach Agent is not a simple calorie calculator or a static meal-plan generator. It is designed as a daily nutrition companion that can gradually understand the user's profile, lifestyle, preferences, risk factors, eating behavior, and progress history.

The application focuses on:

- Structured nutrition onboarding
- Safe medical screening and risk detection
- Habit and behavior awareness
- Multilingual user experience
- Persian-first product localization
- Voice-ready onboarding interaction
- Future-ready architecture for adaptive nutrition guidance

The product is especially suitable for teams or organizations that need a serious, extensible foundation for a digital health, nutrition, wellness, or lifestyle-coaching platform.

---

## Key Features

### Authentication

- Phone-number based OTP login
- Development OTP support with `123456`
- JWT-compatible authentication architecture
- Protected backend routes
- Frontend auth state handling
- Logout-ready token revocation structure

### Multilingual UI

- Persian as the default language
- English and Arabic language foundations
- Dictionary-based i18n
- RTL support for Persian and Arabic
- LTR support for English
- Direction-aware layout and transitions

### Onboarding

- Seven-step animated onboarding wizard
- Profile, goal, medical, lifestyle, preferences, behavior, and final review steps
- Backend-backed onboarding persistence
- Auth-protected onboarding APIs
- Clinical review notice for high-risk users
- Final video placeholder with development bypass support

### Voice & Habit Chat Foundation

- Onboarding habit chat architecture
- Text message endpoint support
- Audio upload endpoint support
- Local audio storage configuration
- Audio metadata persistence
- Frontend-ready voice recorder architecture
- Future-ready transcription/STT integration path

### Backend Architecture

- FastAPI application shell
- API versioning under `/api/v1`
- SQLAlchemy 2.x ORM models
- Alembic migrations
- SQLite database for current stage
- Pydantic v2 schemas
- Service and repository separation
- Environment-based configuration
- Consistent validation and error handling

### Frontend Architecture

- Next.js App Router
- TypeScript strict mode
- Mobile-first layout
- Desktop-centered mobile app experience
- Component-based structure
- Tailwind CSS styling
- Reusable auth, onboarding, and UI modules

---

## Current Implementation Status

| Phase | Status | Description |
|---|---:|---|
| Phase 01 | Completed | Infrastructure, backend foundation, ORM models, Alembic, FastAPI shell, frontend skeleton |
| Phase 02 | Completed | i18n foundation, RTL/LTR support, mobile-first frontend shell |
| Phase 03 | Completed | OTP authentication flow, backend endpoints, frontend login screens |
| Phase 04 | Completed | Onboarding backend APIs, safety guardrail service, onboarding persistence |
| Phase 05 | Completed | Animated onboarding frontend wizard consuming backend APIs |
| Phase 06 | In progress / Next | Voice, audio upload, waveform recorder, onboarding habit chat |
| Phase 07+ | Planned | Nutrition backend, agent layer, adaptive guidance, progress, reports, polish |

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- SQLite
- Pydantic v2
- PyJWT
- Uvicorn
- Modular service/repository architecture

### Frontend

- Next.js
- React
- TypeScript
- App Router
- Tailwind CSS
- React Hook Form
- Zod
- Framer Motion
- Dictionary-based i18n

---

## Repository Structure

```text
diet-coach-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── dictionaries/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── .env.example
│   └── README.md
│
├── .planning/
├── CHANGELOG.md
├── DECISIONS.md
├── NEXT_STEPS.md
├── PROJECT_STATE.md
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following tools before running the project:

- Python 3.11+
- Node.js 20+
- npm
- Git

---

## Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
```

Create local environment file:

```bash
cp .env.example .env
```

Run migrations:

```bash
alembic upgrade head
```

Start backend:

```bash
uvicorn app.main:app --reload
```

Default backend URL:

```text
http://127.0.0.1:8000
```

OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

```bash
cd frontend
npm install
```

Create local environment file:

```bash
cp .env.example .env.local
```

Start development server:

```bash
npm run dev
```

Default frontend URL:

```text
http://localhost:3000
```

---

## Environment Configuration

### Backend

Typical backend variables:

```env
APP_NAME="Diet Coach Agent"
ENVIRONMENT=development
DEBUG=false

SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=10080

DATABASE_URL=sqlite+pysqlite:///./app.db

DEV_OTP_CODE=123456
OTP_EXPIRE_MINUTES=5
SMS_PROVIDER=mock

AUDIO_STORAGE_PATH=./storage/audio
MAX_AUDIO_UPLOAD_MB=20
ALLOWED_AUDIO_MIME_TYPES=audio/webm,audio/ogg,audio/mp4,audio/mpeg,audio/wav
```

### Frontend

Typical frontend variables:

```env
NEXT_PUBLIC_APP_NAME="Diet Coach Agent"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_DEFAULT_LOCALE=fa
NEXT_PUBLIC_SUPPORTED_LOCALES=fa,en,ar
NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS=true
```

> Local `.env` files, SQLite database files, uploads, audio files, caches, and build artifacts must not be committed.

---

## API Overview

### Health

```text
GET /api/v1/health
```

### Authentication

```text
POST /api/v1/auth/request-otp
POST /api/v1/auth/verify-otp
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

### Onboarding

```text
GET  /api/v1/onboarding/status
POST /api/v1/onboarding/profile
POST /api/v1/onboarding/medical
POST /api/v1/onboarding/lifestyle
POST /api/v1/onboarding/preferences
POST /api/v1/onboarding/behavior
POST /api/v1/onboarding/complete
```

### Onboarding Chat / Audio

```text
POST /api/v1/onboarding/chat/text
POST /api/v1/onboarding/chat/audio
GET  /api/v1/onboarding/chat/history
```

---

## Quality Standards

This project follows a professional delivery approach:

- Clear backend/frontend separation
- Versioned API structure
- Migration-managed database schema
- Typed backend schemas
- Strict TypeScript frontend
- Modular service/repository backend pattern
- Reusable frontend components
- Environment-based configuration
- Safe handling of local files and secrets
- Multilingual UI from the foundation
- Git history designed to remain clean and reviewable

The codebase is structured so future developers can continue work without reverse-engineering hidden assumptions.

---

## Security and Safety Notes

- Authentication uses a JWT-compatible architecture.
- OTP is mocked for development and must be connected to a real SMS provider before production use.
- Sensitive configuration must remain in local environment files.
- SQLite files and uploaded media are ignored by Git.
- Medical and nutrition-related flows include safety guardrails and clinical review states.
- The application must not be presented as a replacement for a licensed physician, registered dietitian, or emergency medical service.

---

## Roadmap

Planned next milestones:

- Complete voice recorder and audio upload UX
- Add transcription provider integration
- Add nutrition profile intelligence layer
- Add adaptive meal guidance
- Add daily check-in and progress tracking
- Add weekly reports
- Add settings and language management
- Add production deployment configuration
- Add automated tests for critical flows
- Add specialist review workflow foundation

---

## Professional Note

Diet Coach Agent is being developed as a serious product foundation, not a temporary prototype. The architecture is intentionally structured to support future growth, maintainability, localization, health-safety boundaries, and real user workflows.

The project is suitable for demonstration to stakeholders, staged product development, investor review, technical handoff, and continued production engineering. It is maintained with clear ownership, reviewable commits, and a practical architecture that can be extended by future engineering teams.

---

## Maintainer

**Ehsan Moradi**  
Senior Software Engineer & Product Developer  
GitHub: `ehsanwwe`

---

## License

This project is licensed under the terms defined in the repository `LICENSE` file.
