---
phase: 9
slug: progress-reports
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-03
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 1 | PROG-01 | unit | `python -m pytest tests/test_progress.py::test_checkin_create -x -q` | ❌ W0 | ⬜ pending |
| 9-01-02 | 01 | 1 | PROG-01 | unit | `python -m pytest tests/test_progress.py::test_checkin_upsert -x -q` | ❌ W0 | ⬜ pending |
| 9-01-03 | 01 | 1 | PROG-02 | unit | `python -m pytest tests/test_progress.py::test_progress_summary -x -q` | ❌ W0 | ⬜ pending |
| 9-01-04 | 01 | 1 | PROG-03 | unit | `python -m pytest tests/test_progress.py::test_weekly_report -x -q` | ❌ W0 | ⬜ pending |
| 9-02-01 | 02 | 2 | PROG-04 | manual | N/A — frontend behavior wins rendering | N/A | ⬜ pending |
| 9-02-02 | 02 | 2 | PROG-05 | manual | N/A — sparkline renders as SVG | N/A | ⬜ pending |
| 9-02-03 | 02 | 2 | UI-12 | manual | N/A — bottom nav progress tab enabled | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_progress.py` — stubs for PROG-01, PROG-02, PROG-03
- [ ] `backend/tests/conftest.py` — shared fixtures (may already exist)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Behavior wins chips show green highlights | PROG-04 | Frontend rendering, no automated test | Navigate to /fa/progress, submit check-in, verify colored chips for sleep/activity/hunger |
| Sparkline renders as SVG with correct data points | PROG-05 | SVG visual output | Navigate to /fa/progress, verify `<svg>` element with `<polyline>` or `<path>` visible |
| Bottom nav progress tab is clickable and navigates | UI-12 | Navigation behavior | Click progress icon in bottom nav, verify redirect to /fa/progress |
| Empty state renders helpful prompt | PROG-02 | New user flow | Use fresh account with no check-ins, verify non-blank helpful message |
| Weekly report returns after 7 check-ins | PROG-03 | Integration flow | Submit 7 check-ins via API, call GET /api/v1/progress/weekly-report, verify JSON has weight_trend, adherence_trend, focus_suggestion |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
