---
phase: 10
slug: settings-polish-remaining-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | frontend/vitest.config.ts |
| **Quick run command** | `cd frontend && npm run test -- --run` |
| **Full suite command** | `cd frontend && npm run test -- --run --coverage` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test -- --run`
- **After every plan wave:** Run `cd frontend && npm run test -- --run --coverage`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | UI-13 | unit | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | UI-14 | unit | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | UI-16 | unit | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | UI-17 | unit | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | UI-18 | manual | — | — | ⬜ pending |
| 10-03-02 | 03 | 2 | UI-19 | unit | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |
| 10-03-03 | 03 | 3 | UI-20 | manual | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/settings-screen.test.tsx` — stubs for UI-13, UI-14
- [ ] `frontend/src/__tests__/language-selector.test.tsx` — stubs for UI-16
- [ ] `frontend/src/__tests__/bottom-nav.test.tsx` — stubs for UI-17
- [ ] `frontend/src/__tests__/loading-empty-error-states.test.tsx` — stubs for UI-18, UI-19

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RTL direction flips live on language switch | UI-16 | Requires browser visual verification | Switch language fa→en→ar; observe dir attribute and layout direction change |
| Bottom nav visibility on real mobile viewport | UI-17 | Requires actual device or DevTools viewport | Open Chrome DevTools mobile view; confirm nav bar visible after onboarding |
| Loading states don't flash on fast connections | UI-18 | Timing-sensitive, env-dependent | Throttle network to Slow 3G; navigate between screens; verify loading spinner appears |
| Safe-area insets respected on notched devices | UI-20 | Requires device/emulator with notch | Test on iPhone 14 / Pixel emulator; confirm no content behind notch |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
