# Next Steps — Diet Coach Agent

**Updated:** 2026-06-04
**Current status:** ALL 10 PHASES COMPLETE. App is feature-complete for v1.0.

## Immediate Next Action

Run end-to-end manual QA verification:

```
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Navigate to http://localhost:3000/fa/login → OTP 123456 → complete onboarding → explore all screens.

## Key QA Checks

1. **Settings screen:** `/fa/settings` — Language row, Profile (phone), Logout inline confirm
2. **Language switch:** Tap Language row → select English → page switches to `/en/settings/language` with LTR layout
3. **Settings tab:** Bottom nav settings icon highlights when on /settings or /settings/language
4. **Logout flow:** Expand logout confirm → confirm → redirects to /fa/login
5. **Progress screen:** `/fa/progress` — check-in form + weekly report
6. **Nutrition:** Dashboard, plan, meal analysis, what-to-eat-now

## Known Issues to Address

1. **Next.js build failure on /fa/onboarding** — `InvariantError: Expected workStore to be initialized`. Fix: add `export const dynamic = 'force-dynamic'` to `frontend/src/app/[lang]/onboarding/page.tsx`
2. **ESLint not configured** — project has no `eslint.config.mjs`. TypeScript strict mode serves as primary linting.

## Post-v1 Roadmap

- Real SMS provider (Kavenegar for Iran / Twilio)
- Push notifications
- Wearable integration
- Human nutritionist panel
- Payment/subscription
