# Nightly Test Report

## Run Metadata

- Date: 2026-05-12
- Start time: 2026-05-12T14:00:00
- End time: 
- Operator: opencode-agent
- Branch / commit: main
- Environment: Windows local dev
- Report status: `draft`
- Final recommendation: `pending`

## Scope

- Included checks:
  - Backend boot and public endpoints (`test_basic_endpoints.py`)
  - Auth flow (`test_full.py`)
  - Image recognition regression (`test_image.py`)
  - External provider check (`test_stepfun.py`)
  - Frontend build (`npm run build`)
- Excluded checks: None
- Notes on environment or data setup: Full nightly regression run

## Test Matrix

| Area | Command / Script | Status | Evidence | Notes |
|------|------------------|--------|----------|-------|
| Backend boot | `python test_basic_endpoints.py` | `pass` | Status 200, 4 workflow types returned | Backend starts OK |
| Public endpoints | `python test_basic_endpoints.py` | `pass` | /api/workflow/types returns 200 | Public endpoint works |
| Auth flow | manual register/login/me test | `pass` | Register 200, Login 200, Auth request 200 | Deviation: replaced unsafe test_full.py |
| Image recognition | manual test with 海报.jpeg | `pass` | Status 200, latency 3.5s, fallback to demo data | Graceful degradation works |
| External provider | `python -B test_stepfun.py` | `not_run` | | |
| Frontend build | `npm run build` | `not_run` | | |

## Findings

### Blocker

- None recorded.

### High

- None recorded.

### Medium

- None recorded.

### Low

- None recorded.

## Risks And Unknowns

- List skipped checks and why they were skipped.
- Record flaky behavior separately from confirmed failures.
- Note any scripts that are unsafe for shared local environments.

## Follow-Up Actions

- [ ] Assign owners for failed or skipped critical checks
- [ ] Decide whether another run is required
- [ ] Archive logs or screenshots if applicable

## Executive Summary

- Overall result:
- Ship recommendation:
- Key reason: