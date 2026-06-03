# Changelog — Diet Coach Agent

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

---

## [0.1.0] - 2026-06-03

### Added — Phase 1: Infra & Backend Foundation

**Backend**
- Monorepo structure: `backend/` and `frontend/` directories established
- `backend/pyproject.toml` with all required dependencies (FastAPI, SQLAlchemy 2.x, Alembic, PyJWT, pydantic-settings)
- `backend/app/core/config.py`: pydantic-settings BaseSettings with SECRET_KEY validation and all 10 OPENCLAW_* vars
- `backend/app/core/database.py`: SQLAlchemy 2.x sync engine, `get_session()` FastAPI dependency, `DeclarativeBase`
- `backend/app/core/errors.py`: consistent `{"status", "message", "detail"}` error response helpers
- All 22 ORM models with `lazy="raise"` on all relationships, UUID PKs, created_at/updated_at
- Alembic migration environment with `render_as_batch=True` + `compare_type=True` (SQLite DDL safety)
- Initial migration `0001_initial_schema.py` covering all 22 tables
- FastAPI app factory with CORS from environment, global error handlers, modular directory structure
- `/api/v1/health` endpoint returning `{"status": "ok"}`
- `backend/.env.example` documenting all env vars including all 10 OPENCLAW_* vars
- `backend/README.md` with setup, migration commands, technology notes

**Frontend**
- Next.js 16 skeleton with App Router `src/app/[lang]/` structure
- Tailwind CSS v4 with `@tailwindcss/postcss` PostCSS plugin
- TypeScript strict mode enabled
- `frontend/.env.example` documenting frontend env vars
- `frontend/README.md` with setup guide

**Repository**
- `.gitignore` covering SQLite files, env files, uploads, caches
- Root `.env.example` with cross-service documentation linking to service examples

### Notes
- `lazy="raise"` on all ORM relationships: accessing any relationship outside a session raises MissingGreenlet/DetachedInstanceError
- `render_as_batch=True` in BOTH alembic/env.py context.configure() calls — required for all future SQLite DDL
- SECRET_KEY absent causes server to refuse startup with clear error message

---

## [Unreleased]

### Planned
- Phase 1: Infra & Backend Foundation
- Phase 2: i18n & Frontend Shell (PWA, RTL, UI style system)
- Phase 3: Authentication
- Phase 4: Onboarding Backend
- Phase 5: Onboarding Frontend
- Phase 6: Voice & Audio
- Phase 7: Nutrition Backend & AI Layer (OpenClaw + MockAI + conversation memory)
- Phase 8: Nutrition Frontend & Chat
- Phase 9: Progress & Reports
- Phase 10: Settings, Polish & Remaining UI

---

## [0.0.2] — 2026-06-03

### Added
- PWA requirements: manifest, service worker, offline fallback, install prompt (PWA-01..05)
- OpenClaw AI integration requirements: OpenAI-compatible provider, 10 OPENCLAW_* env vars (OC-01..08)
- Conversation persistence and rolling summaries requirements (MEM-01..04)
- UI Style System requirements: muted/pale/app-like aesthetic (UI-STYLE-01..04)
- Continuation files requirements: PROJECT_STATE.md, NEXT_STEPS.md, DECISIONS.md, CHANGELOG.md (CONT-01..04)
- Root `.env.example` requirement (INFRA-09)
- `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md` initialized at repo root
- Phase 1 now includes OPENCLAW_* env var documentation, continuation file creation
- Phase 2 now includes PWA setup and UI style system establishment
- Phase 7 now includes OpenClawProvider, rolling summaries, NutritionMemoryContext
- Total requirements: 126 → 152

### Changed
- REQUIREMENTS.md: INFRA-03 updated to include OPENCLAW_* vars
- REQUIREMENTS.md: Out of Scope updated (OpenAI/Claude SDK → v2; OpenClaw is v1)
- ROADMAP.md: Phases 1, 2, 7 updated with new requirements and success criteria
- PROJECT.md: Active requirements, Constraints, Key Decisions updated
- CLAUDE.md: OpenClaw config, UI style, PWA, and continuation file update protocol added
- STATE.md: New decisions appended

---

## [0.0.1] — 2026-06-03

### Added
- GSD project initialization: config.json, PROJECT.md, research (STACK/FEATURES/ARCHITECTURE/PITFALLS/SUMMARY), REQUIREMENTS.md (126 requirements), ROADMAP.md (10 phases), STATE.md, CLAUDE.md
- Technology stack decisions: FastAPI 0.136.x, SQLAlchemy 2.x (sync), Alembic, Next.js 16, Tailwind v4, Zustand, Framer Motion, PyJWT
- 10-phase roadmap covering infra, i18n/RTL, auth, onboarding (backend + frontend), voice/audio, AI/nutrition backend, nutrition frontend/chat, progress/reports, polish
