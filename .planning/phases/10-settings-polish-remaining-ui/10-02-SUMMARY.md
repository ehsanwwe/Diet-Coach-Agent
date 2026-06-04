---
phase: 10-settings-polish-remaining-ui
plan: 02
subsystem: frontend-polish
tags: [error-handling, loading-states, empty-states, rtl, ux-polish]
dependency_graph:
  requires: []
  provides: [canonical-error-patterns, standardized-loading-spinner, empty-state-cards, app-container-coverage]
  affects: [MealAnalysisForm, WhatToEatForm, PhoneLoginForm, OtpVerifyForm, CompanionChat, PlanSummary, NutritionDashboard, onboarding/page]
tech_stack:
  added: []
  patterns: [canonical-unauthorized-short-circuit, dictionary-mapped-errors, standard-loading-spinner, standard-empty-state-card, ApiRequestError-catch-mapping]
key_files:
  created: []
  modified:
    - frontend/src/components/nutrition/MealAnalysisForm.tsx
    - frontend/src/components/nutrition/WhatToEatForm.tsx
    - frontend/src/components/auth/PhoneLoginForm.tsx
    - frontend/src/components/auth/OtpVerifyForm.tsx
    - frontend/src/app/[lang]/nutrition/meal-analysis/page.tsx
    - frontend/src/app/[lang]/nutrition/what-to-eat/page.tsx
    - frontend/src/components/chat/CompanionChat.tsx
    - frontend/src/components/nutrition/PlanSummary.tsx
    - frontend/src/components/nutrition/NutritionDashboard.tsx
    - frontend/src/app/[lang]/nutrition/plan/page.tsx
    - frontend/src/app/[lang]/onboarding/page.tsx
decisions:
  - "PlanSummary transformed to accept optional plan+loading+loadError props from parent — avoids duplicating data fetching while satisfying state-management requirements"
  - "plan/page.tsx upgraded to useCallback reload pattern with canonical UNAUTHORIZED + dict.errors.generic error mapping"
  - "CompanionChat empty state refactored to early-return pattern — previously rendered inline inside the messages list which was only suitable for the non-empty state rendering path"
metrics:
  duration: 8m 28s
  completed: 2026-06-04
  tasks_completed: 3
  files_modified: 11
---

# Phase 10 Plan 02: Error State Polish & app-container Audit Summary

Polish pass replacing raw `err.message` display with dictionary-mapped errors, standardizing loading/empty/error state patterns across 3 list-style components, and ensuring every authenticated screen page wraps in `app-container`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace raw err.message with dictionary-mapped errors in 4 form components + wire locale prop | 99d7e29 | MealAnalysisForm, WhatToEatForm, PhoneLoginForm, OtpVerifyForm, meal-analysis/page, what-to-eat/page |
| 2 | Enforce loading + empty + error states in 3 list-style components | 8bef2b0 | CompanionChat, PlanSummary, NutritionDashboard, plan/page |
| 3 | Audit & patch app-container wrapper across all screen pages | 7e80766 | onboarding/page |

## Verification Results (All 12 Points Passing)

1. `setError(err.message)` removed from all 4 form components — 0 raw err.message in setError calls
2. `setError(err instanceof Error ? err.message : ...)` removed from MealAnalysisForm and WhatToEatForm
3. `ApiRequestError` import present in all 4 form files (2 imports each)
4. `err.message === 'UNAUTHORIZED'` canonical pattern: 5 matches across nutrition + chat components
5. `err.status === 401` status-based check: 0 matches — only canonical string check used
6. `locale={locale}` wired in meal-analysis/page.tsx line 33 and what-to-eat/page.tsx line 21
7. `plan.noPlanTitle` in PlanSummary.tsx (context-specific empty-state key)
8. `plan.noPlanDesc` in PlanSummary.tsx
9. `dashboard.noOnboarding` in NutritionDashboard.tsx
10. `dashboard.noOnboardingCta` in NutritionDashboard.tsx
11. `companionChat.emptyTitle` in CompanionChat.tsx
12. `animate-spin` in all 3 list-style components (CompanionChat, PlanSummary, NutritionDashboard)
13. `app-container` in all 10 authenticated screen pages including now-patched onboarding/page.tsx
14. No RTL physical classes (`pl-`, `pr-`, `ml-`, `mr-`) in any patched component

## Per-File Changes

### Task 1: Form Components

**MealAnalysisForm.tsx**
- Added `locale: Locale` to Props interface
- Added imports: `useRouter` from next/navigation, `Locale` from @/lib/i18n, `ApiRequestError` from @/lib/api
- Added `const router = useRouter()` inside component
- `catch (err)` block changed from: `setError(err instanceof Error ? err.message : dict.common.error)` to: UNAUTHORIZED short-circuit + ApiRequestError check + `dict.errors.generic` fallback
- Props type extended: `Pick<Dictionary, 'mealAnalysis' | 'common' | 'errors'>`

**WhatToEatForm.tsx**
- Same pattern as MealAnalysisForm — locale prop, router, ApiRequestError import, canonical catch block
- Props type: `Pick<Dictionary, 'whatToEat' | 'common' | 'errors'>`

**PhoneLoginForm.tsx**
- `catch (err) { if (err instanceof ApiRequestError) { setError(err.message) } }` replaced with status-mapped: 422 → `dict.phoneError`, >=500 → `dict.networkError`, other → `dict.networkError`
- Previously had `ApiRequestError` import already; no new imports needed

**OtpVerifyForm.tsx**
- `verifyOtp catch`: `err.status === 400 ? dict.invalidOtp : err.message` replaced with: 400/401 → `dict.invalidOtp`, 410 → `dict.otpExpired`, other → `dict.networkError`
- `requestOtp catch` (resend): `setError(err.message)` replaced with `dict.networkError` for all ApiRequestError cases

**meal-analysis/page.tsx** — Added `locale={locale}` to `<MealAnalysisForm>` on line 33

**what-to-eat/page.tsx** — Added `locale={locale}` to `<WhatToEatForm>` on line 21

### Task 2: List-Style Components

**CompanionChat.tsx**
- Loading spinner: added `role="status"` and `aria-label={dict.common.loading}`; changed container to `min-h-[60vh]`
- Error state: upgraded from simple centered `<p>` to standard error card (`rounded-2xl bg-elevated p-6 shadow-sm`)
- Empty state: refactored from inline render-inside-messages-list to early-return before main messages container; uses standard `rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-4` card format with 💬 icon, `companionChat.emptyTitle`, `companionChat.emptyDesc`
- Load UNAUTHORIZED check: upgraded from `err?.message === 'UNAUTHORIZED'` (optional chaining) to canonical `err instanceof Error && err.message === 'UNAUTHORIZED'`

**PlanSummary.tsx**
- Transformed from pure display component to state-aware component
- Now accepts optional props: `plan?: NutritionPlanResponse | null`, `loading?: boolean`, `loadError?: string | null`, `onRetry?: () => void`
- Added loading state: standard spinner with `role="status"` and `aria-label={dict.common.loading}`
- Added error state: standard error card with retry button (calls `onRetry` if provided)
- Added empty state: standard card with 🍽️ icon, `dict.plan.noPlanTitle`, `dict.plan.noPlanDesc`
- Props type: `Pick<Dictionary, 'plan' | 'errors' | 'common'>`
- Added `'use client'` directive (was previously a server component — needed since it now receives potentially-mutable props from a client parent)

**NutritionDashboard.tsx**
- Added `loadError` state (`const [loadError, setLoadError] = useState<string | null>(null)`)
- Converted `useEffect` to `useCallback reload` pattern for retry support
- UNAUTHORIZED check: upgraded from `err?.message === 'UNAUTHORIZED'` to `err instanceof Error && err.message === 'UNAUTHORIZED'`
- Added `setLoadError(dict.errors.generic)` for non-UNAUTHORIZED errors (previously silently swallowed)
- Loading spinner: added `role="status"` and `aria-label={dict.common.loading}`, changed container to `min-h-[60vh]`
- Added loadError early-return state: standard error card with retry button calling `void reload()`
- Added `useCallback` import

**plan/page.tsx** (updated to pass new PlanSummary props)
- Added `loadError` state
- Converted `useEffect` to `useCallback reload` pattern
- UNAUTHORIZED check upgraded to `err instanceof Error && err.message === 'UNAUTHORIZED'`
- Added `setLoadError(dict.errors.generic)` for non-UNAUTHORIZED errors
- PlanSummary call updated: `<PlanSummary plan={plan?.has_plan ? plan : null} loading={loading} loadError={loadError} onRetry={() => void reload()} dict={dict} />`
- Removed now-redundant inline empty state (delegated to PlanSummary)
- Added `useCallback` import

### Task 3: app-container Audit

**onboarding/page.tsx** — Added `<div className="app-container">` wrapper between `<AuthGuard>` and `<OnboardingWizard>`. No other changes. All 10 authenticated screen pages now have app-container.

## Dict Keys Used (Context-Specific)

| Component | Key Used | Confirmed Present |
|-----------|----------|-------------------|
| CompanionChat | `dict.companionChat.emptyTitle` | fa.ts line 935 |
| CompanionChat | `dict.companionChat.emptyDesc` | fa.ts line 936 |
| PlanSummary | `dict.plan.noPlanTitle` | fa.ts line 848 |
| PlanSummary | `dict.plan.noPlanDesc` | fa.ts line 849 |
| NutritionDashboard | `dict.dashboard.noOnboarding` | fa.ts line 831 |
| NutritionDashboard | `dict.dashboard.noOnboardingCta` | fa.ts line 832 |
| NutritionDashboard | `dict.dashboard.noPlanTitle` | fa.ts line 827 (inline in existing plan summary card) |
| NutritionDashboard | `dict.dashboard.noPlanDesc` | fa.ts line 828 (inline in existing plan summary card) |

No generic fallbacks were needed — all context-specific keys were confirmed present before implementation.

## Deviations from Plan

### Deviation 1: PlanSummary Architecture

**Found during:** Task 2

**Issue:** Plan said to add `if (loading) return <Spinner />` to PlanSummary, but PlanSummary was a pure display component receiving `plan: NutritionPlanResponse` as a required prop. It couldn't have its own loading state without duplicating the data fetch that plan/page.tsx already performs.

**Fix:** Made plan, loading, loadError optional props on PlanSummary so the parent (plan/page.tsx) manages the data fetching but delegates state rendering to PlanSummary. Updated plan/page.tsx to pass these props and use the useCallback reload pattern.

**Rule applied:** Rule 1 (auto-fix bug/impediment) — the existing architecture would prevent the task from being completed without this adaptation.

**Files modified:** PlanSummary.tsx, plan/page.tsx

### Deviation 2: Merge main into worktree branch

**Found at start of execution**

**Issue:** The worktree branch (`worktree-agent-aa17272817d792a4d`) was behind main by many commits. The source files required by the plan did not exist in the worktree.

**Fix:** Fast-forward merged main into the worktree branch before execution. The merge was clean with no conflicts.

**Rule applied:** Rule 3 (auto-fix blocking issue) — source files didn't exist so no task could begin without this.

## Known Stubs

None — all components are wired to real data sources and use dictionary strings throughout.

## Self-Check: PASSED

All modified files confirmed present. All 3 task commits verified in git log:
- 99d7e29 — Task 1: form component error handling
- 8bef2b0 — Task 2: list-style component states
- 7e80766 — Task 3: app-container audit
