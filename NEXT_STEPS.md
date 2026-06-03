# Next Steps — Diet Coach Agent

**Updated:** 2026-06-04
**Current status:** Phase 9 COMPLETE. Phase 10 (Settings, Polish & Remaining UI) ready to start.

## Immediate Next Action

Run Phase 10 planning:
```
/gsd:plan-phase
```

Phase 10 covers: settings screen, profile editing, notification preferences, polish/animations, PWA install prompt, offline fallback, and any remaining UI gaps.

## Manual Visual Verification (Phase 9 — still required)

The automated tests pass but visual verification of the progress screen is pending:

```
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Navigate to http://localhost:3000/fa/login → OTP 123456 → dashboard → tap پیشرفت tab.

Verify the 7 checks from `.planning/phases/09-progress-reports/09-03-PLAN.md` Task 3.

## Phase 10 Scope (from ROADMAP)
- Settings screen `/[lang]/settings` (currently disabled in bottom nav)
- Profile editing (weight goal, dietary restrictions update)
- Notification preferences
- PWA install prompt + service worker + offline fallback
- App-wide polish: animations, loading states, error boundaries
- Any ROADMAP requirements not covered by phases 1-9
