# Nightly Test Execution Checklist

This checklist is for a manual nightly pass on the current MealMate repository.

## 1. Pre-Run

- [ ] Confirm current branch and commit are recorded
- [ ] Confirm `backend/.env` exists if provider or authenticated flows are in scope
- [ ] Confirm Python environment is usable
- [ ] Confirm frontend dependencies are installed in `frontend/`
- [ ] Create a new report from `reports/templates/nightly-test-report.md`

## 2. Environment Risk Check

- [ ] Review scripts before running them
- [ ] Call out that `test_full.py` uses `taskkill /F /IM python.exe` and may kill unrelated Python processes
- [ ] Decide whether to run destructive or broad local-process scripts as-is
- [ ] If unsafe, replace with a narrower manual equivalent and document the deviation

## 3. Backend Smoke

- [ ] Run `python test_basic_endpoints.py`
- [ ] Verify backend boots on `127.0.0.1:8000`
- [ ] Verify `/api/workflow/types` responds
- [ ] Verify unauthenticated workflow execution is rejected as expected

## 4. Auth And Core API Happy Path

- [ ] Run `python test_full.py` only if killing all `python.exe` processes is acceptable in the current environment
- [ ] If `test_full.py` is unsafe, run a narrower auth smoke manually and record the substitution
- [ ] Verify register and login succeed
- [ ] Verify token-bearing requests are accepted

## 5. Image Recognition Regression

- [ ] Run `python test_image.py`
- [ ] Verify authenticated image recognition returns a non-error response
- [ ] Record latency or timeout concerns if observed

## 6. External Provider Check

- [ ] Run `python -B test_stepfun.py` only when `STEPFUN_API_KEY` is configured
- [ ] If not configured, mark as `not_run`
- [ ] Record whether the failure is provider, credential, network, or payload related

## 7. Frontend Release Check

- [ ] Run `npm run build` in `frontend/`
- [ ] Verify build completes successfully
- [ ] Record warnings that affect confidence

## 8. Reporting

- [ ] Update the test matrix after each check
- [ ] Promote every real failure into the Findings section with severity
- [ ] Document skipped checks under Risks And Unknowns
- [ ] Set final recommendation to `pass`, `pass_with_risks`, or `fail`

## 9. Exit Criteria

- [ ] No blocker remains open for a `pass`
- [ ] Any skipped critical check downgrades at least to `pass_with_risks`
- [ ] If backend boot, auth, or core image flow fails, mark the run `fail`
