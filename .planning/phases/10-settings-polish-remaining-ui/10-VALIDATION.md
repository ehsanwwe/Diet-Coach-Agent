---
phase: 10
slug: settings-polish-remaining-ui
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-04
revised: 2026-06-04
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript + ESLint (tsc --noEmit + eslint) + pytest (backend) |
| **Config files** | frontend/tsconfig.json, frontend/eslint.config.mjs, backend/pyproject.toml |
| **Quick run command (frontend)** | `cd frontend && npx tsc --noEmit` |
| **Full suite command (frontend)** | `cd frontend && npx tsc --noEmit && npm run lint` |
| **Backend command** | `cd backend && python -m pytest tests/test_settings.py -x -q` |
| **Estimated runtime** | ~15–25 seconds (tsc) + ~5 seconds (lint) + ~10 seconds (pytest) |

**Rationale for tsc+lint over vitest:** vitest is not installed in the frontend (per RESEARCH.md; no `frontend/vitest.config.ts` exists, no `vitest` in package.json). Phase 10 work is structural (dictionary type extensions, component patches, page wiring). The relevant correctness signals are:
- **Type safety** — `tsc --noEmit` catches missing dict keys, locale type mismatches, prop wiring errors
- **Lint compliance** — `npm run lint` catches RTL physical-class usage if a custom rule exists, plus standard React hooks/Next.js issues
- **Backend behavior** — pytest covers PATCH /settings/language 200/401/422/upsert cases
- **Grep audits** — per-task `<verify>` includes grep checks for canonical patterns (e.g., `err.message === 'UNAUTHORIZED'`, `app-container`, dict key usage)

Vitest stub creation is explicitly out of scope for Phase 10; if behavioral unit tests become needed later, install vitest in a future phase and add stubs then.

---

## Sampling Rate

- **After every task commit:** Run the task's `<verify>` command (typically `cd frontend && npx tsc --noEmit` for frontend tasks, `cd backend && python -m pytest tests/test_settings.py -x -q` for backend task)
- **After every plan wave:** Run `cd frontend && npx tsc --noEmit && npm run lint` (frontend) and `cd backend && python -m pytest -x -q` (full backend)
- **Before `/gsd:verify-work`:** Full frontend (tsc + lint + `npm run build`) and full backend pytest suite must be green
- **Max feedback latency:** ~25 seconds (tsc)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Verify Type | Automated Command | Status |
|---------|------|------|-------------|-------------|-------------------|--------|
| 10-01-01 | 01 | 1 | UI-13, UI-14 (dict keys) | tsc | `cd frontend && npx tsc --noEmit` | ⬜ pending |
| 10-01-02 | 01 | 1 | UI-13, UI-14 (backend) | pytest | `cd backend && python -m pytest tests/test_settings.py -x -q` | ⬜ pending |
| 10-02-01 | 02 | 1 | UI-20 (form error mapping) | tsc + grep | `cd frontend && npx tsc --noEmit` + grep audits in `<verify>` | ⬜ pending |
| 10-02-02 | 02 | 1 | UI-18, UI-19, UI-20 (list states) | tsc + lint + grep | `cd frontend && npx tsc --noEmit && npm run lint` + grep audits | ⬜ pending |
| 10-02-03 | 02 | 1 | UI-16 (app-container audit) | grep | grep audit confirming every existing screen page has app-container | ⬜ pending |
| 10-03-01 | 03 | 2 | UI-14, UI-16 (LanguageSelector) | tsc + grep | `cd frontend && npx tsc --noEmit` + grep audits | ⬜ pending |
| 10-03-02 | 03 | 2 | UI-13, UI-16 (SettingsScreen) | tsc + grep | `cd frontend && npx tsc --noEmit` + grep audits | ⬜ pending |
| 10-03-03 | 03 | 2 | UI-17 (bottom nav enable) | tsc + grep | `cd frontend && npx tsc --noEmit` + grep audits | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Notes:**
- "grep audits" refers to grep-based acceptance checks embedded directly in each task's `<verify>` and `<acceptance_criteria>` blocks. These confirm canonical patterns (dict key presence, `app-container` wrapper, RTL-class absence, anti-pattern absence) without requiring a test runner.
- Backend pytest tests created in Task 10-01-02 are the only behavioral tests written this phase; they cover the PATCH /settings/language endpoint end-to-end.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RTL direction flips live on language switch | UI-16 | Requires browser visual verification | Switch language fa→en→ar; observe dir attribute and layout direction change |
| Bottom nav visibility on real mobile viewport | UI-17 | Requires actual device or DevTools viewport | Open Chrome DevTools mobile view; confirm nav bar visible after onboarding |
| Loading states don't flash on fast connections | UI-18 | Timing-sensitive, env-dependent | Throttle network to Slow 3G; navigate between screens; verify loading spinner appears |
| Safe-area insets respected on notched devices | UI-20 | Requires device/emulator with notch | Test on iPhone 14 / Pixel emulator; confirm no content behind notch |
| Logout flow end-to-end | UI-13 | Requires authenticated session + redirect verification | Sign in → Settings → Logout → confirm — confirm redirect to /{locale}/login and token cleared from storage |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify backed by tsc/lint/pytest/grep — no MISSING references
- [x] Sampling continuity: every task has an automated check (no 3-task gaps)
- [x] Wave 0 stub creation NOT required — no vitest dependency; per-task grep audits cover behavioral signals not catchable by tsc
- [x] No watch-mode flags
- [x] Feedback latency < 30s (tsc ~15-25s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved — verification strategy realigned with installed tooling (tsc + ESLint + pytest + grep audits). Vitest infrastructure deferred to a future phase if behavioral unit tests become necessary.
