# Next Steps — Diet Coach Agent

**Updated:** 2026-06-03
**Current status:** Phase 1 COMPLETE. Phase 2 ready to start.

## Immediate Next Action

**Start Phase 2: i18n & Frontend Shell**

Command: `/gsd:plan-phase 2` (then `/gsd:execute-phase 2`)

## What Phase 2 Builds

Phase 2 goal: Complete i18n foundation — fa/en/ar dictionaries, RTL direction from cookie (zero flicker), all CSS using Tailwind v4 logical properties, direction-aware utilities, PWA manifest + service worker, muted/pale/app-like style system.

### First files to touch in Phase 2:
1. `frontend/src/middleware.ts` — locale detection from cookie/Accept-Language, redirect to /[lang]
2. `frontend/src/app/[lang]/dictionaries/fa.json` — Persian dictionary (all UI strings)
3. `frontend/src/app/[lang]/dictionaries/en.json` — English dictionary
4. `frontend/src/app/[lang]/dictionaries/ar.json` — Arabic dictionary
5. `frontend/src/app/[lang]/layout.tsx` — add `lang` and `dir` attributes from server-side locale

### First command to run:
```bash
cd frontend && npm install  # if not already done
# Then execute Phase 2 plans
```

## If Phase 2 is Already Done

Read `.planning/phases/02-*/02-*-SUMMARY.md` files to understand what was built.
Then check `ROADMAP.md` for Phase 3 (Authentication).

## Phase Order Reminder

1. ✅ Infra & Backend Foundation (COMPLETE)
2. → i18n & Frontend Shell (NEXT)
3. Authentication (after Phase 2)
4. Onboarding Backend (after Phase 3)
5. Onboarding Frontend (after Phase 4)
6. Voice & Audio (after Phase 5)
7. Nutrition Backend & AI Layer (after Phase 4)
8. Nutrition Frontend & Chat (after Phase 7)
9. Progress & Reports (after Phase 8)
10. Settings, Polish & Remaining UI (after Phase 9)

---
*Last updated: 2026-06-03*
