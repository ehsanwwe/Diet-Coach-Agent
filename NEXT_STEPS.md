# Next Steps — Diet Coach Agent

> Updated after every meaningful commit. Start here after `/clear` or a new session.

## Immediate Next Action

**Start Phase 1: Infra & Backend Foundation**

Run: `/gsd:plan-phase 1`

Or to discuss first: `/gsd:discuss-phase 1`

## What Phase 1 Delivers

- Monorepo structure (`backend/` + `frontend/`)
- FastAPI app factory with CORS from env
- SQLAlchemy 2.x (sync) + Alembic (`render_as_batch=True`, `lazy="raise"`)
- All 22 ORM models migrated on blank SQLite
- `pydantic-settings` typed config with all 10 `OPENCLAW_*` vars
- `SECRET_KEY` startup validation
- Root `.env.example` + `backend/.env.example` + `frontend/.env.example`
- `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md` initialized

## Files to Touch First (Phase 1)

1. `backend/pyproject.toml` — dependencies
2. `backend/app/core/config.py` — pydantic-settings with OPENCLAW vars
3. `backend/app/core/database.py` — SQLAlchemy engine + session
4. `backend/app/models/` — all 22 models
5. `backend/alembic/env.py` — render_as_batch=True
6. `backend/.env.example` — all env vars documented
7. `frontend/package.json` — Next.js 16 + Tailwind v4 setup
8. Root `.env.example`

## After Phase 1

Next: `/gsd:plan-phase 2` — i18n & Frontend Shell (PWA, RTL, UI style system)

---
*Last updated: 2026-06-03*
