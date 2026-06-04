---
phase: 10-settings-polish-remaining-ui
plan: "03"
subsystem: frontend/settings
tags: [settings, language-selector, bottom-nav, RTL, i18n, auth]
dependency_graph:
  requires: [10-01]
  provides: [settings-screen, language-selector, settings-nav-tab]
  affects: [frontend/src/components/layout/AppBottomNav.tsx]
tech_stack:
  added: []
  patterns:
    - "api.patch() fire-and-forget for NEXT_LOCALE cookie → backend persist"
    - "Canonical UNAUTHORIZED pattern: err.message === 'UNAUTHORIZED' FIRST"
    - "getIconFlipClass(locale) for RTL-aware chevron icons"
    - "Inline logout confirmation — expand/collapse without modal"
key_files:
  created:
    - frontend/src/components/settings/LanguageSelector.tsx
    - frontend/src/components/settings/SettingsScreen.tsx
    - frontend/src/app/[lang]/settings/page.tsx
    - frontend/src/app/[lang]/settings/language/page.tsx
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/components/layout/AppBottomNav.tsx
decisions:
  - "Language route page intentionally excludes AppBottomNav — it is a sub-screen of Settings"
  - "Phone number display uses dir='ltr' — phone numbers are technical identifiers, render LTR even in RTL layouts"
  - "Logout failure (server 401/500) is silently swallowed — clearToken + redirect is always the correct fallback"
  - "TypeScript verification used tsc --noEmit via symlinked node_modules (worktree has no local node_modules)"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-04"
  tasks_completed: 3
  files_created: 4
  files_modified: 2
---

# Phase 10 Plan 03: Settings Screens + Nav Tab Summary

Settings + Language Selector screens implemented with RTL-aware UI, canonical auth patterns, and inline logout confirmation; Settings tab enabled in bottom nav.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | LanguageSelector + language route + api.patch | 4925be4 | api.ts, LanguageSelector.tsx, settings/language/page.tsx |
| 2 | SettingsScreen + settings page route | 5a37cc6 | SettingsScreen.tsx, settings/page.tsx |
| 3 | Enable settings tab in AppBottomNav | 41a65ab | AppBottomNav.tsx |

## New Files Created

- `frontend/src/components/settings/LanguageSelector.tsx` — Language list client component; writes `NEXT_LOCALE` cookie via `document.cookie`, fires `PATCH /api/v1/settings/language` fire-and-forget, navigates to `/${newLocale}/settings/language`
- `frontend/src/components/settings/SettingsScreen.tsx` — Settings UI client component; fetches `/api/v1/auth/me`, displays Language nav row, Profile (phone read-only), Account (logout with inline confirmation)
- `frontend/src/app/[lang]/settings/page.tsx` — Settings route page: `AuthGuard` + `app-container` + `SettingsScreen` + `AppBottomNav`
- `frontend/src/app/[lang]/settings/language/page.tsx` — Language selector route page: `AuthGuard` + `app-container` + `LanguageSelector` (no `AppBottomNav` by design — sub-screen)

## Modified Files

### `frontend/src/lib/api.ts` — Added `patch` method

```typescript
patch: <T>(path: string, body: unknown, auth = false) =>
  request<ApiSuccess<T>>(path, {
    method: 'PATCH',
    body: JSON.stringify(body),
    auth,
  }),
```

### `frontend/src/components/layout/AppBottomNav.tsx` — 2-line change

```typescript
// Before:
active: false,
disabled: true,

// After:
active: isActive('settings'),
disabled: false,
```

## Grep Audit Results

| Audit | Command | Result |
|-------|---------|--------|
| No `disabled: true` in AppBottomNav | `grep "disabled: true" AppBottomNav.tsx` | 0 matches — PASS |
| No physical Tailwind classes | `grep -rn "pl-\|pr-\|ml-\|mr-"` in settings/ | 0 matches — PASS |
| No documentElement.dir mutation | `grep -rn "documentElement.dir"` in settings/ | 0 matches — PASS |
| app-container on both new pages | `grep -rn "app-container"` in settings/ | 2 matches — PASS |
| Canonical UNAUTHORIZED pattern | `grep "err.message === 'UNAUTHORIZED'"` in SettingsScreen.tsx | Line 43 — PASS |
| TypeScript | `tsc --noEmit` | 0 errors — PASS |

## Manual QA Notes

### How to verify language switch (fa → en → ar):

1. Navigate to `/{locale}/settings`
2. Tap "تغییر زبان" (Language row)
3. On language selector screen, tap "English"
4. Expect: `NEXT_LOCALE=en` cookie written, navigation to `/en/settings/language`
5. Page re-renders with LTR direction (`<html dir="ltr">`)
6. Tap back, tap "العربية"
7. Expect: `NEXT_LOCALE=ar` cookie, navigation to `/ar/settings/language`, RTL direction

### How to verify Settings tab highlight:

1. Navigate to any screen (e.g., dashboard)
2. Settings tab in bottom nav should NOT be highlighted
3. Navigate to `/fa/settings`
4. Settings icon in bottom nav should be `text-brand` (highlighted)
5. Navigate to `/fa/settings/language` — settings tab remains highlighted (pathname includes `/settings`)

### How to verify logout flow:

1. Navigate to `/{locale}/settings`
2. Tap "خروج از حساب" (Logout button)
3. Inline confirmation expands — no modal
4. Tap "ماندن" (Cancel) — confirmation collapses
5. Tap "خروج از حساب" again, then confirm button
6. Expect: `diet_coach_token` removed from localStorage, redirect to `/{locale}/login`

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Infrastructure Note

The worktree (`agent-aeefa3a20af83a892`) was initialized at an old commit (`cd165f9`). Plans 01 and 02 were merged from `main` before execution via `git merge main`. This is expected parallel execution behavior — the merge brought in all prerequisite files (dictionary `settings.*` namespace, AppBottomNav, AuthGuard, etc.).

A symlink was created `frontend/node_modules → /d/ai_agent/Diet-Coach-Agent/frontend/node_modules` to enable `tsc --noEmit` without reinstalling dependencies.

## Deferred Items

One pre-existing build failure (unrelated to this plan):

- `/fa/onboarding` static prerendering fails with `InvariantError: Expected workStore to be initialized` — a Next.js issue in the onboarding page. Documented in `deferred-items.md`. Fix: add `export const dynamic = 'force-dynamic'` to onboarding page.

## Known Stubs

None — all data is wired: profile loaded from `/api/v1/auth/me`, logout calls `/api/v1/auth/logout`, language PATCH calls `/api/v1/settings/language`.

## Self-Check: PASSED

All created files exist on disk. All commits present in git history:
- `4925be4` feat(10-03): build LanguageSelector component + language page route
- `5a37cc6` feat(10-03): build SettingsScreen component + settings page route
- `41a65ab` feat(10-03): enable settings tab in AppBottomNav (UI-17)
