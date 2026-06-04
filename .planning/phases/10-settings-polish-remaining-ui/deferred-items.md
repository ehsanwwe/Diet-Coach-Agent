# Deferred Items — Phase 10 Plan 03

## Pre-existing Build Issues (out of scope)

### 1. Next.js build fails on /fa/onboarding — InvariantError workStore

**Error:** `Error [InvariantError]: Invariant: Expected workStore to be initialized. This is a bug in Next.js.`

**Route:** `/[lang]/onboarding/page` during static generation

**Status:** Pre-existing — present before Plan 03 changes. Not caused by settings/LanguageSelector/AppBottomNav changes. The settings routes build cleanly; only onboarding triggers this.

**Recommended fix:** Export `export const dynamic = 'force-dynamic'` from `/app/[lang]/onboarding/page.tsx` to prevent static prerendering of that route.
