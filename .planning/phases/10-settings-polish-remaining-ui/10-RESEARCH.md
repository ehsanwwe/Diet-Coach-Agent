# Phase 10: Settings, Polish & Remaining UI — Research

**Researched:** 2026-06-04
**Domain:** Next.js 16 App Router frontend — settings screen, language switching, bottom navigation, loading/empty/error states, RTL audit, mobile viewport safety
**Confidence:** HIGH (codebase fully read; all patterns confirmed from existing source files)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-13 | Settings screen (language, profile, account) | New route + screen component; uses existing AuthGuard + AppBottomNav pattern; backend has UserProfile and UserLanguagePreference models ready |
| UI-14 | Language selector screen | New route OR modal from settings; NEXT_LOCALE cookie write + router push; existing middleware + direction infrastructure already handles the switch |
| UI-16 | Mobile-first layout; desktop shows mobile view centered with max-width | `.app-container` class with `max-width: 430px` already exists in globals.css; audit needed that all 16 screens use it |
| UI-17 | Bottom mobile navigation after onboarding completes | `AppBottomNav` already exists and is used on dashboard, chat, nutrition, and progress pages; settings tab currently `disabled: true` — enable it once settings route exists |
| UI-18 | Loading states for all async operations | Spinner pattern already exists in AuthGuard and ProgressScreen; audit + standardize across all 16 screens |
| UI-19 | Empty states for lists/dashboards with no data | Empty state pattern already exists in ProgressScreen; audit + standardize across all screens |
| UI-20 | Error states with user-friendly messages (no raw API errors) | ApiRequestError pattern already exists; audit + standardize across all screens |
</phase_requirements>

---

## Summary

Phase 10 is the completion pass: it builds the two missing screens (settings + language selector), enables the disabled settings tab in the bottom nav, and performs a global audit/polish pass across all existing screens to enforce consistent loading, empty, and error state patterns.

The codebase has strong foundations in place. The `AppBottomNav` component already exists with the settings icon, but the settings tab is hard-coded `disabled: true`. The middleware and root layout already handle cookie-based locale detection and server-side direction setting — language switching requires writing the `NEXT_LOCALE` cookie from the client and navigating to the new locale path. The `UserLanguagePreference` model and table already exist in the backend; a new `/api/v1/settings/language` endpoint is needed to persist the selection server-side.

The loading/empty/error state audit is the heaviest work item. All the patterns already exist in the codebase (spinner in AuthGuard, empty state in ProgressScreen, `ApiRequestError` in api.ts), but they need to be consistently applied to every screen. The planner should treat this as a screen-by-screen checklist with specific component files to inspect and update.

**Primary recommendation:** Build the two new screens first (settings + language selector), enable the settings nav tab, then do the global audit pass as a final wave.

---

## Project Constraints (from CLAUDE.md)

The following are mandatory directives for this phase (not suggestions):

- **No physical Tailwind spacing classes:** Never use `pl-`, `pr-`, `ml-`, `mr-` — always `ps-`, `pe-`, `ms-`, `me-`
- **No saturated colors / gym palette:** All new components must use `text-brand`, `bg-brand-muted`, `text-ink`, `text-ink-2`, `text-ink-3`, `bg-elevated`, `bg-surface`, `border-line`, `text-error`, `text-success` — no arbitrary hex values
- **No hard-coded text:** All user-facing strings must come from the dictionary. No Persian or English strings in component files
- **UI style:** App-like, not website-like. No horizontal top nav bars, no Bootstrap card grids. Bottom nav, full-bleed screens, soft rounded cards (border-radius >= 16px), subtle shadows
- **Dictionary shape:** `fa.ts` is the source of truth. Any new string added to `fa.ts` must also be added to `en.ts` and `ar.ts` with the same key
- **Continuation files:** After every meaningful commit, update `PROJECT_STATE.md`, `NEXT_STEPS.md`, `DECISIONS.md`, `CHANGELOG.md` at repo root
- **AI config:** All 10 `OPENCLAW_*` vars from backend env only — none of this is relevant to Phase 10 (no AI screens being added)
- **No new npm packages unless strictly necessary:** The installed package set (Framer Motion, Lucide React, Zustand is NOT installed, clsx + tailwind-merge, React Hook Form + Zod) covers everything needed for this phase

---

## Codebase State — What Already Exists

This is a continuation phase. Understanding what is built is essential for planning.

### Screens Already Built (confirmed by reading source files)

| Screen | Route | Component | Bottom Nav? |
|--------|-------|-----------|-------------|
| Splash | `/[lang]/` | `app/[lang]/page.tsx` inline | No |
| Login | `/[lang]/login` | `components/auth/PhoneLoginForm.tsx` | No |
| OTP Verify | `/[lang]/login/verify` | `components/auth/OtpVerifyForm.tsx` | No |
| Onboarding | `/[lang]/onboarding` | `components/onboarding/` | No |
| Dashboard (home) | `/[lang]/dashboard` | `components/nutrition/NutritionDashboard.tsx` | Yes |
| Chat | `/[lang]/chat` | `components/chat/CompanionChat.tsx` | Yes |
| Nutrition Plan | `/[lang]/nutrition/plan` | `components/nutrition/PlanSummary.tsx` | Yes |
| Meal Analysis | `/[lang]/nutrition/meal-analysis` | `components/nutrition/MealAnalysisForm.tsx` | Yes |
| What To Eat | `/[lang]/nutrition/what-to-eat` | `components/nutrition/WhatToEatForm.tsx` | Yes |
| Progress | `/[lang]/progress` | `components/progress/ProgressScreen.tsx` | Yes |
| Clinical Review | (state within nutrition screens) | `components/nutrition/ClinicalReviewState.tsx` | Varies |

### Screens Missing (Phase 10 must build)

| Screen | Route | Requirement |
|--------|-------|-------------|
| Settings | `/[lang]/settings` | UI-13 |
| Language Selector | `/[lang]/settings/language` OR modal | UI-14 |

### AppBottomNav State (confirmed from source)

The `AppBottomNav` component at `frontend/src/components/layout/AppBottomNav.tsx` has 4 tabs:
- Home → `/[locale]/dashboard` — enabled
- Chat → `/[locale]/chat` — enabled
- Progress → `/[locale]/progress` — enabled
- Settings → `/[locale]/settings` — **currently `disabled: true`** — must be enabled in Phase 10

The settings tab already has its icon (SVG gear icon) and dictionary label (`dict.nav.settings`). Only the `disabled: true` flag and the `href` need updating once the route exists.

### Dictionary State (confirmed from `fa.ts`)

Existing dictionary keys relevant to Phase 10:
- `nav.settings` — "تنظیمات" — already present
- `language.select`, `language.fa`, `language.en`, `language.ar`, `language.current`, `language.change` — already present
- `common.loading`, `common.error`, `common.retry`, `common.save`, `common.cancel` — already present
- `errors.notFound`, `errors.offline`, `errors.generic` — already present

**New dictionary keys needed for Phase 10:**
```
settings.title
settings.languageSection
settings.profileSection
settings.accountSection
settings.currentLanguage
settings.changeLanguage
settings.displayName
settings.phoneNumber
settings.logoutBtn
settings.logoutConfirm
settings.logoutCancel
settings.appVersion
settings.deleteAccount (optional - can be omitted for v1)
```

These must be added to all three dictionaries (`fa.ts`, `en.ts`, `ar.ts`) with matching structure.

### Infrastructure Already in Place (HIGH confidence)

**Language switching mechanism (confirmed from source):**
- `middleware.ts` reads `NEXT_LOCALE` cookie and redirects to `/{locale}/...`
- `app/layout.tsx` reads `NEXT_LOCALE` cookie server-side and sets `<html lang dir>` — no flicker
- `lib/i18n.ts` exports `LOCALE_COOKIE = 'NEXT_LOCALE'`, `SUPPORTED_LOCALES`, `isValidLocale`
- `lib/direction.ts` exports `getDirection()`, `isRTL()`, `getSlideX()`, `getIconFlipClass()`
- Switching language = set `NEXT_LOCALE` cookie client-side + navigate to `/{newLocale}/settings`
- The `httpOnly: false` cookie setting (confirmed in middleware.ts) means JS can write it

**CSS / layout infrastructure (confirmed from globals.css):**
- `.app-container` — `max-width: 430px; margin-inline: auto; min-height: 100dvh; display: flex; flex-direction: column` — the mobile centering class
- `.pb-safe` — `padding-bottom: env(safe-area-inset-bottom, 16px)` — iOS safe area
- `.pt-safe` — `padding-top: env(safe-area-inset-top, 0px)`
- `body { min-height: 100dvh }` — dynamic viewport height already applied at root
- All color tokens defined in `@theme {}` block

**Backend language preference model (confirmed from source):**
- `UserLanguagePreference` table exists with `user_id`, `language_code`, `created_at`, `updated_at`
- `User.language_preference` relationship exists with `lazy="raise"` (must be explicitly loaded)
- No backend endpoint for settings currently exists — one needs to be created

---

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| Next.js | ^16.0.0 | App Router, pages, routing | Installed |
| React | ^19.0.0 | UI runtime | Installed |
| TypeScript | ^5.6.0 | Type safety | Installed |
| Tailwind CSS | ^4.0.0 | Styling with logical properties | Installed |
| Framer Motion | ^12.40.0 | Animations (if needed for transitions) | Installed |
| Lucide React | ^1.17.0 | Icons | Installed |
| clsx + tailwind-merge | ^2.1.1 / ^3.6.0 | Class composition | Installed |

### No New Packages Needed

Phase 10 requires zero new `npm install` commands. All functionality (settings form, language switcher, loading spinners, empty states, error messages) is achievable with existing stack.

The one edge case: if a settings page needs a confirmation dialog for logout, that's built with React state + existing Tailwind classes — not a modal library.

---

## Architecture Patterns

### Recommended Project Structure for New Files

```
frontend/src/
├── app/[lang]/
│   └── settings/
│       ├── page.tsx               # Settings screen page (authenticated)
│       └── language/
│           └── page.tsx           # Language selector page (authenticated)
├── components/
│   └── settings/
│       ├── SettingsScreen.tsx     # Client component — settings UI
│       └── LanguageSelector.tsx   # Client component — language list
└── dictionaries/
    ├── fa.ts                      # Add settings.* keys
    ├── en.ts                      # Add settings.* keys
    └── ar.ts                      # Add settings.* keys
```

Backend additions:
```
backend/app/api/v1/endpoints/
└── settings.py                    # GET /settings/profile, PATCH /settings/language

backend/app/schemas/
└── settings.py                    # Request/response schemas

backend/app/services/
└── settings_service.py            # Business logic: upsert language preference, get profile
```

### Pattern 1: Page File Structure (mirrors existing screens)

All authenticated pages follow this pattern exactly (confirmed from dashboard, progress, chat pages):

```typescript
// app/[lang]/settings/page.tsx
import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import SettingsScreen from '@/components/settings/SettingsScreen'

type Props = { params: Promise<{ lang: string }> }

export default async function SettingsPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <SettingsScreen dict={dict} locale={locale} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
```

**Key constraint:** `<div className="app-container">` wraps everything. `AppBottomNav` always appears at the bottom of the app-container. Content scrolls via `flex-1 overflow-y-auto` on the inner element with `pb-28` to clear the nav bar.

### Pattern 2: Language Switching (client-side)

Language switching is pure client-side: write the `NEXT_LOCALE` cookie and navigate. The middleware and root layout handle the rest server-side with zero flicker.

```typescript
// components/settings/LanguageSelector.tsx — key logic
'use client'
import { useRouter } from 'next/navigation'
import { LOCALE_COOKIE, SUPPORTED_LOCALES, type Locale } from '@/lib/i18n'

function switchLocale(newLocale: Locale, currentLocale: Locale, router: ReturnType<typeof useRouter>) {
  // Write the cookie (httpOnly:false so JS can write it)
  document.cookie = `${LOCALE_COOKIE}=${newLocale}; path=/; max-age=${60 * 60 * 24 * 365}; SameSite=Lax`
  // Navigate to same page in new locale
  router.push(`/${newLocale}/settings/language`)
}
```

**Why this works:** The root `app/layout.tsx` reads the `NEXT_LOCALE` cookie server-side on every request. After the cookie is updated and the route changes, the server re-renders with the new `lang` and `dir` attributes on `<html>`. No client-side context mutation needed.

**Pitfall:** Do NOT try to mutate `<html dir>` directly in a client component. Let the server handle it via the layout cookie read. Direct DOM mutation for `dir` creates hydration mismatches and direction flicker.

### Pattern 3: Loading State (standardized spinner)

The existing spinner pattern from `AuthGuard.tsx` and `ProgressScreen.tsx` is the standard:

```typescript
// Standard loading state — use this in ALL async screens
if (loading) {
  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div
        role="status"
        aria-label={dict.common.loading}
        className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin"
      />
    </div>
  )
}
```

**Audit target:** Every Client Component that does async data fetching must implement this pattern before rendering content. The planner must check these components:
- `NutritionDashboard.tsx` — async nutrition data
- `CompanionChat.tsx` — async chat history
- `PlanSummary.tsx` — async plan data
- `MealAnalysisForm.tsx` — async analysis result
- `WhatToEatForm.tsx` — async suggestion result

### Pattern 4: Empty State (standardized)

The existing empty state pattern from `ProgressScreen.tsx` is the standard:

```typescript
// Standard empty state — adapt icon and text per screen context
if (data && !data.hasContent) {
  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28">
      <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-4">
        <div className="mx-auto w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center">
          <span className="text-3xl">{contextIcon}</span>
        </div>
        <h2 className="text-xl font-bold text-ink">{dict.section.emptyTitle}</h2>
        <p className="text-sm text-ink-2 leading-relaxed">{dict.section.emptyDesc}</p>
        <button
          type="button"
          onClick={primaryAction}
          className="w-full py-4 rounded-2xl bg-brand text-elevated font-bold text-sm"
        >
          {dict.section.emptyCta}
        </button>
      </div>
    </div>
  )
}
```

**Empty state coverage needed:**
- Chat history with no messages → `companionChat.emptyTitle` / `companionChat.emptyDesc` already in dict
- Nutrition plan not yet generated → `plan.noPlanTitle` / `plan.noPlanDesc` already in dict
- Dashboard with no onboarding → `dashboard.noOnboarding` already in dict
- Progress with no check-ins → `progress.emptyTitle` already in dict
- Meal analysis before first use → no form submission yet — handled by initial form state (not empty state needed)

### Pattern 5: Error State (standardized)

```typescript
// Standard error state with retry — use in ALL screens where data fetch can fail
if (loadError) {
  return (
    <div className="flex-1 px-5 pt-6 pb-28">
      <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-3">
        <p className="text-sm text-error">{loadError}</p>
        <button
          type="button"
          onClick={() => void reload()}
          className="px-4 py-2 rounded-2xl bg-brand text-elevated font-bold text-sm"
        >
          {dict.common.retry}
        </button>
      </div>
    </div>
  )
}
```

**ApiRequestError handling:** The `api.ts` client throws `ApiRequestError` with `.status`, `.message`, `.detail`. Client components must catch these and map to dictionary strings. The `UNAUTHORIZED` (401) case must redirect to login — this pattern already exists in `ProgressScreen.tsx` and should be replicated everywhere.

```typescript
// Standard error catch pattern
} catch (err) {
  if (err instanceof Error && err.message === 'UNAUTHORIZED') {
    router.replace(`/${locale}/login`)
    return
  }
  setLoadError(err instanceof Error ? err.message : dict.section.errLoadFailed)
}
```

### Pattern 6: dvh + safe-area-inset (confirmed working)

The `.app-container` class uses `min-height: 100dvh` (dynamic viewport height). The `body` also has `min-height: 100dvh`. The `.pb-safe` utility applies `env(safe-area-inset-bottom, 16px)`.

The bottom nav already uses `pb-safe`:
```typescript
// AppBottomNav.tsx — confirmed
<nav className="fixed bottom-0 inset-x-0 z-50 pb-safe bg-elevated border-t border-line">
```

Content that scrolls behind the nav uses `pb-28` to add bottom padding. This is the standard pattern — no additional setup needed.

**DVH note:** `100dvh` vs `100vh` — `dvh` (dynamic viewport height) is the correct choice on mobile because it excludes the browser chrome that appears/disappears on scroll. All screens already use `min-h-dvh` at the body level (confirmed in globals.css). No changes needed to this infrastructure.

### Anti-Patterns to Avoid

- **Direct `<html dir>` mutation from client component:** Creates hydration mismatch. Use cookie + server render.
- **Physical Tailwind classes `pl-*`, `pr-*`, `ml-*`, `mr-*`:** Breaks RTL. Use `ps-*`, `pe-*`, `ms-*`, `me-*`.
- **Hard-coded text in JSX:** Every user-facing string must come from `dict.*`.
- **Inline error display with raw `.message`:** Map errors to dictionary strings before displaying.
- **Missing `pb-28` on scrollable content:** Content disappears behind bottom nav without this padding.
- **Missing `flex-1 overflow-y-auto` on content area:** Content either doesn't scroll or doesn't flex to fill the container.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cookie write for locale switch | Custom cookie API | `document.cookie = ...` (vanilla) | One-liner; httpOnly:false cookie is already configured |
| Direction switching | Client-side `<html>` mutation | Cookie write + router.push → server re-render | Avoids hydration mismatch; server already handles it in root layout |
| Toast/notification for success | Third-party toast library | React state + `setTimeout` clear | Same pattern already in ProgressScreen (`successMsg` state) |
| Confirmation dialog (logout) | Modal library | Inline state + conditional render | Simple boolean state; no library needed |
| Settings form | React Hook Form + Zod (full validation) | Simple controlled inputs | Settings has minimal validation (language select is just a link click; name edit is optional) |

---

## Backend Work Required

### New Endpoint: Settings

The backend needs a minimal settings API. The `UserLanguagePreference` model and table already exist.

**Endpoint:** `GET /api/v1/settings/profile` — returns user profile summary for display on settings screen (name, phone, onboarding status). This can reuse the existing `GET /api/v1/auth/me` endpoint — **no new endpoint needed** for read.

**Endpoint needed:** `PATCH /api/v1/settings/language` — upserts `UserLanguagePreference` for the current user.

```python
# backend/app/api/v1/endpoints/settings.py
@router.patch("/language", response_model=SuccessResponse[LanguagePreferenceResponse])
def update_language_preference(
    body: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SuccessResponse[LanguagePreferenceResponse]:
    ...
```

**Schema:**
```python
class UpdateLanguageRequest(BaseModel):
    language_code: Literal["fa", "en", "ar"]

class LanguagePreferenceResponse(BaseModel):
    language_code: str
    updated_at: datetime
```

**Why persist to backend:** The `NEXT_LOCALE` cookie handles the browser-side state. The backend persistence exists so that if the user logs in from a new device, their preferred language can be read from the server and set as the initial cookie. This is a "nice to have" for v1 — the planner can treat it as optional and note the fallback is cookie-only (which is sufficient for the phase success criteria).

**Important:** The success criterion says "persists the choice across sessions" — the cookie already handles this (1 year expiry). Backend persistence is enhancement-level for v1.

---

## Common Pitfalls

### Pitfall 1: Settings Tab Enable Sequence
**What goes wrong:** Developer enables the settings tab in `AppBottomNav.tsx` before the `/[lang]/settings` route exists, causing a 404 when users click it.
**Why it happens:** The tab and the route are in different files.
**How to avoid:** Create the settings page file first, verify it returns 200, then enable the tab.
**Warning signs:** 404 on settings click; `disabled: false` in nav but no page file.

### Pitfall 2: Language Switch Direction Flicker
**What goes wrong:** Switching from fa (RTL) to en (LTR) briefly shows RTL layout before re-rendering.
**Why it happens:** If the client tries to update `<html dir>` directly, React hydration fights with the server-rendered value.
**How to avoid:** Write the cookie and navigate. Never call `document.documentElement.dir = '...'` in a React component. The root layout reads the cookie on the next request and sets the correct `dir` server-side.
**Warning signs:** Flash of RTL content on locale switch; Tailwind logical property classes rendering backwards.

### Pitfall 3: AppBottomNav Covering Content
**What goes wrong:** The bottom nav overlaps the last row of content on a screen.
**Why it happens:** `AppBottomNav` is `position: fixed` with `bottom: 0`. Without bottom padding on the content area, content scrolls behind it invisibly.
**How to avoid:** All scrollable content areas must have `pb-28` (standard in existing screens). New screens must follow the same pattern.
**Warning signs:** Last button or text on a screen is partially hidden; visible when scrolled all the way down.

### Pitfall 4: Missing `app-container` on New Screens
**What goes wrong:** New settings/language screens don't constrain to `max-width: 430px` on desktop.
**Why it happens:** Developer forgets the wrapper class.
**How to avoid:** All page files wrap content in `<div className="app-container">`. This is the `UI-16` requirement.
**Warning signs:** Settings screen stretches full width on desktop; looks different from other screens.

### Pitfall 5: Empty State Missing from Chat Screen
**What goes wrong:** Chat screen shows a blank white area when the user has no messages yet.
**Why it happens:** `CompanionChat.tsx` checks for messages but may not have a designed empty state.
**How to avoid:** Check `CompanionChat.tsx` explicitly. The dict key `companionChat.emptyTitle` and `companionChat.emptyDesc` already exist — they just need to be rendered when the messages array is empty.
**Warning signs:** Blank content area with only the composer at the bottom.

### Pitfall 6: RTL Audit Missing Physical CSS in Existing Components
**What goes wrong:** Screens look broken in Arabic or English-LTR because a component uses `pl-4` instead of `ps-4`.
**Why it happens:** Earlier phases may have introduced physical Tailwind classes under time pressure.
**How to avoid:** Run a grep audit as part of the RTL pass: `grep -r "pl-\|pr-\|ml-\|mr-" frontend/src/components/` and fix all matches. Exception: these physical classes are intentional only when explicitly styling a non-directional layout element (e.g., a centered icon with equal padding).
**Warning signs:** Padding looks asymmetric in RTL; cards have inconsistent spacing between fa and en views.

---

## Code Examples

### Language Switcher (client component pattern)

```typescript
// Source: confirmed from middleware.ts cookie logic + existing locale infrastructure
'use client'
import { useRouter } from 'next/navigation'
import { LOCALE_COOKIE, SUPPORTED_LOCALES, type Locale } from '@/lib/i18n'
import type { Dictionary } from '@/dictionaries/fa'
import { cn } from '@/lib/cn'

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'language' | 'common'>
}

export default function LanguageSelector({ locale, dict }: Props) {
  const router = useRouter()

  function handleSelect(newLocale: Locale) {
    if (newLocale === locale) return
    // Write cookie (httpOnly:false — confirmed in middleware.ts)
    document.cookie = `${LOCALE_COOKIE}=${newLocale}; path=/; max-age=${60 * 60 * 24 * 365}; SameSite=Lax`
    // Navigate to the same page in the new locale
    router.push(`/${newLocale}/settings/language`)
  }

  return (
    <div className="space-y-2">
      {SUPPORTED_LOCALES.map((loc) => (
        <button
          key={loc}
          type="button"
          onClick={() => handleSelect(loc)}
          className={cn(
            'w-full flex items-center justify-between px-4 py-4 rounded-2xl transition-colors',
            loc === locale
              ? 'bg-brand-muted text-brand font-bold'
              : 'bg-elevated text-ink font-medium',
          )}
        >
          <span>{dict.language[loc]}</span>
          {loc === locale && <span className="text-brand text-sm">{dict.language.current}</span>}
        </button>
      ))}
    </div>
  )
}
```

### Standard Screen Content Wrapper

```typescript
// Source: confirmed from ProgressScreen.tsx, NutritionDashboard.tsx patterns
// All scrollable screen content uses this wrapper
<div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
  {/* Screen content here */}
</div>
```

### Bottom Nav Enable Patch (AppBottomNav.tsx)

```typescript
// Change in AppBottomNav.tsx — enable settings tab once /settings route exists
{
  href: `/${locale}/settings`,
  label: dict.nav.settings,
  icon: SettingsIcon,
  active: isActive('settings'),
  disabled: false,  // was: true
},
```

---

## RTL Audit Checklist

The planner must include a dedicated RTL audit task. This is the checklist:

### Structural Checks (every component file)
- [ ] No `pl-`, `pr-`, `ml-`, `mr-` Tailwind classes (use `ps-`, `pe-`, `ms-`, `me-`)
- [ ] No `left:`, `right:` physical CSS in style props or globals
- [ ] Directional icons (chevrons, arrows) use `getIconFlipClass(locale)` from `lib/direction.ts`
- [ ] Framer Motion slide animations use `getSlideX(locale, direction)` from `lib/direction.ts`

### Visual Checks (render in fa and en)
- [ ] Text alignment is natural (RTL text right-aligns in fa/ar; LTR left-aligns in en)
- [ ] Form labels appear on the correct side
- [ ] Cards and list items have symmetric or logical padding
- [ ] The bottom nav icons and labels are correctly positioned in both directions
- [ ] Input fields and placeholders align correctly

### Automated Grep Audit
```bash
# Run from frontend/ directory — any output is a violation
grep -r "pl-\|pr-\|ml-\|mr-" src/components/ src/app/ --include="*.tsx" --include="*.ts"
```

---

## Environment Availability

Step 2.6: SKIPPED — Phase 10 is purely frontend code changes with no new external dependencies. All tools (Node, npm, Next.js dev server) are confirmed working from Phase 9 completion.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | TypeScript compiler (`tsc --noEmit`) + ESLint |
| Config file | `frontend/tsconfig.json`, `frontend/eslint.config.mjs` |
| Quick run command | `cd frontend && npm run type-check` |
| Full suite command | `cd frontend && npm run type-check && npm run lint` |

No Jest/Vitest test framework is installed. Phase 10 verification relies on:
1. TypeScript compilation with no errors
2. ESLint clean run
3. Manual visual QA against the success criteria checklist

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| UI-13 | Settings screen renders for authenticated users | smoke | `npm run type-check` (catches component type errors) | ❌ Wave 0 |
| UI-14 | Language switch updates cookie and re-renders with correct direction | manual | Visual QA in browser | N/A |
| UI-16 | All screens use `.app-container` class | grep audit | `grep -r "app-container" src/app/\[lang\]/ --include="*.tsx"` | ✅ |
| UI-17 | Bottom nav visible + settings tab enabled after onboarding | manual | Visual QA + type-check | ❌ modified |
| UI-18 | Every async screen has loading spinner | grep audit | `grep -rn "animate-spin" src/components/` | partial |
| UI-19 | Every list screen has empty state | grep audit | `grep -rn "emptyTitle\|emptyDesc" src/components/` | partial |
| UI-20 | No raw error messages shown to user | grep audit | `grep -rn "err\.message\|error\.message" src/components/` | partial |

### Wave 0 Gaps
- [ ] `frontend/src/components/settings/SettingsScreen.tsx` — covers UI-13
- [ ] `frontend/src/components/settings/LanguageSelector.tsx` — covers UI-14
- [ ] `frontend/src/app/[lang]/settings/page.tsx` — route for UI-13, UI-16, UI-17
- [ ] `frontend/src/app/[lang]/settings/language/page.tsx` — route for UI-14
- [ ] Dictionary additions in `fa.ts`, `en.ts`, `ar.ts` — settings.* keys
- [ ] `backend/app/api/v1/endpoints/settings.py` — language preference persistence

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `100vh` for mobile viewport | `100dvh` (dynamic viewport height) | ~2023 CSS spec, widely supported 2024 | Fixes content hidden behind browser chrome on mobile scroll |
| `padding-left`/`right` for layout | CSS logical properties (`padding-inline-start`) | Tailwind v4 default | RTL layout works without `rtl:` prefix classes |
| `rtl:` Tailwind variant | Tailwind v4 logical properties by default | Tailwind v4 | Physical `pl-/pr-` still exist but should not be used |
| `document.documentElement.dir` mutation | Cookie-driven server-side direction on `<html>` | Next.js App Router pattern | Zero hydration flicker on direction change |

---

## Open Questions

1. **Backend language persistence — required or optional for v1?**
   - What we know: The `NEXT_LOCALE` cookie (1-year expiry) satisfies "persists across sessions" per success criterion 4
   - What's unclear: Whether the planner wants a `PATCH /settings/language` backend call in addition to the cookie, or cookie-only is sufficient
   - Recommendation: Implement cookie-only for the language switch. The `UserLanguagePreference` table already exists and can be written in Phase 10 as a background `fire-and-forget` call (ignore errors) so it doesn't block the UX. This way the model is populated but not critical path.

2. **Settings screen profile edit — read-only or editable?**
   - What we know: UI-13 says "language, profile, account" — profile section and account section scope is unspecified
   - What's unclear: Whether the user can edit their name/phone from settings, or just view it
   - Recommendation: Read-only display of name and phone number in v1 (from `GET /api/v1/auth/me`). Editable profile fields are a Phase 2 / v2 enhancement. This keeps Phase 10 focused.

3. **Language selector — separate screen or modal?**
   - What we know: Both patterns work; requirement says "language selector screen" (UI-14)
   - What's unclear: Whether "screen" means a separate route (`/settings/language`) or a full-screen overlay
   - Recommendation: Separate route at `/[lang]/settings/language` — consistent with the App Router pattern, easily shareable URL, and simpler than a modal with its accessibility requirements.

---

## Sources

### Primary (HIGH confidence)
- `frontend/src/components/layout/AppBottomNav.tsx` — confirmed disabled settings tab, existing nav structure
- `frontend/src/app/globals.css` — confirmed `.app-container`, `.pb-safe`, `100dvh`, color tokens
- `frontend/src/middleware.ts` — confirmed cookie name `NEXT_LOCALE`, `httpOnly: false`
- `frontend/src/app/layout.tsx` — confirmed server-side cookie read + `<html lang dir>` setting
- `frontend/src/lib/i18n.ts` — confirmed `LOCALE_COOKIE`, `SUPPORTED_LOCALES`, `getDictionary`
- `frontend/src/lib/direction.ts` — confirmed `getDirection`, `isRTL`, `getSlideX`, `getIconFlipClass`
- `frontend/src/dictionaries/fa.ts` — confirmed all existing dictionary keys including `nav.settings`, `language.*`
- `frontend/src/components/progress/ProgressScreen.tsx` — confirmed loading/empty/error state patterns
- `frontend/src/components/auth/AuthGuard.tsx` — confirmed auth guard + loading spinner pattern
- `frontend/src/lib/api.ts` — confirmed `ApiRequestError` structure
- `backend/app/models/audit.py` — confirmed `UserLanguagePreference` model with `language_code` field
- `backend/app/models/user.py` — confirmed `language_preference` relationship with `lazy="raise"`
- `frontend/package.json` — confirmed all installed package versions

### Secondary (MEDIUM confidence)
- `frontend/src/app/[lang]/dashboard/page.tsx`, `progress/page.tsx` — confirmed page structure pattern
- `frontend/src/components/nutrition/` listing — confirmed screens already built in Phase 8

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages confirmed from package.json
- Architecture: HIGH — all patterns confirmed from existing source files
- Pitfalls: HIGH — derived from reading actual implementation code, not theory
- RTL audit: HIGH — confirmed existing infrastructure; grep command verified
- Backend settings API: MEDIUM — model confirmed; endpoint does not yet exist

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 (stable architecture; only invalidated by major refactor of existing screens)
