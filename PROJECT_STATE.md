# Project State — Diet Coach Agent

**Last updated:** 2026-06-03
**Current phase:** Phase 2 COMPLETE → Phase 3 next
**Overall progress:** Phase 2 of 10 complete (20%)

## What Exists Now

### Backend (`backend/`) — Phase 1
- `pyproject.toml`, all dependencies, all 22 ORM models, Alembic migrations
- `app/core/config.py` — SECRET_KEY validation, all 10 OPENCLAW_* vars
- `app/main.py`, `/api/v1/health`, `backend/.env.example`, `backend/README.md`

### Frontend (`frontend/`) — Phase 2 COMPLETE
- **i18n infrastructure**
  - `src/dictionaries/fa.ts` — Persian dictionary (defines Dictionary interface)
  - `src/dictionaries/en.ts` — English dictionary
  - `src/dictionaries/ar.ts` — Arabic dictionary
  - `src/lib/i18n.ts` — Locale types, SUPPORTED_LOCALES, getDictionary()
  - `src/lib/direction.ts` — getDirection(), isRTL(), getSlideX(), getIconFlipClass()
- **Middleware** — `src/middleware.ts` — locale detection from cookie/Accept-Language, redirect to /[lang], sets NEXT_LOCALE cookie
- **Root layout** — `src/app/layout.tsx` — reads NEXT_LOCALE cookie, sets `<html lang dir>` server-side (zero RTL flicker)
- **[lang] layout** — validates locale, 404s on unknown lang
- **Splash page** — `src/app/[lang]/page.tsx` — app-like mobile shell, dictionary strings, language switcher
- **Globals CSS** — muted/pale brand palette via Tailwind v4 `@theme {}`, logical spacing, .app-container
- **PWA** — `public/manifest.json`, `public/sw.js`, `public/offline.html`, `public/icons/icon.svg`
- **Service worker registration** — `src/components/service-worker.tsx` (client component)
- **next.config.ts** — Cache-Control headers for sw.js and manifest.json
- **frontend/.env.example** — NEXT_PUBLIC_APP_NAME, NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_DEFAULT_LOCALE, NEXT_PUBLIC_SUPPORTED_LOCALES, NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS

### Root
- `.env.example`, `.gitignore`, `backend/README.md`, `frontend/README.md`

## Critical Safeguards Verified
- `lazy="raise"` on ALL ORM relationships
- `render_as_batch=True` in both Alembic env.py calls
- `SECRET_KEY` validation at startup
- No hard-coded CORS origins
- No pl-/pr-/ml-/mr- Tailwind classes used (logical properties only)
- Direction set server-side via cookie — no RTL flicker

## Known Issues / Notes
- `middleware.ts` naming is deprecated in Next.js 16 (prefer `proxy.ts`) — rename in Phase 10 polish
- PWA icon uses SVG (browser-supported); Phase 10 should add 192×192 and 512×512 PNGs for iOS
- Frontend does not yet call the backend (no auth, no API calls)

## How to Resume (Cold Start)
1. Read this file + NEXT_STEPS.md
2. Backend: `cd backend && alembic upgrade head && uvicorn app.main:app --reload`
3. Frontend: `cd frontend && npm run dev` → open http://localhost:3000 → redirects to /fa
4. Start Phase 3: `/gsd:plan-phase 3`

## Phase Progress

| Phase | Status |
|-------|--------|
| 1 — Infra & Backend Foundation | **COMPLETE** |
| 2 — i18n & Frontend Shell | **COMPLETE** |
| 3 — Authentication | Not started |
| 4 — Onboarding Backend | Not started |
| 5 — Onboarding Frontend | Not started |
| 6 — Voice & Audio | Not started |
| 7 — Nutrition Backend & AI Layer | Not started |
| 8 — Nutrition Frontend & Chat | Not started |
| 9 — Progress & Reports | Not started |
| 10 — Settings, Polish & Remaining UI | Not started |

---
*Last updated: 2026-06-03*
