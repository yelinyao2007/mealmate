# Nightly Test Report

## Run Metadata

- Date:
- Start time:
- End time:
- Operator:
- Branch / commit:
- Environment:
- Report status: `draft`
- Final recommendation: `pass | pass_with_risks | fail`

## Scope

- Included checks:
- Excluded checks:
- Notes on environment or data setup:

## Test Matrix

| Area | Command / Script | Status | Evidence | Notes |
|------|------------------|--------|----------|-------|
| Backend boot | `python test_basic_endpoints.py` | `not_run` | | |
| Public endpoints | `python test_basic_endpoints.py` | `not_run` | | |
| Auth flow | `python test_full.py` | `not_run` | | |
| Image recognition | `python test_image.py` | `not_run` | | |
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
