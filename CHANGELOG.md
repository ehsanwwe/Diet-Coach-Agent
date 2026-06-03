# Changelog — Diet Coach Agent

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

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
