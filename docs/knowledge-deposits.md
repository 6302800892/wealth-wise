# Knowledge deposits

Recurring mistakes and surprises, and where each lesson was encoded so agents do not repeat it.

| ID | What went wrong / was learned | Encoded into |
|---|---|---|
| KD-01 | import-linter `forbidden` contracts flag **indirect** imports by default, so legitimate chains like `api → service → repository` failed. | `pyproject.toml` (`allow_indirect_imports = true` on forbidden contracts; the layers contract still checks indirect upward imports). `archtest-author-agent` catalogue. |
| KD-02 | FastAPI 0.142 nests included routers (`_IncludedRouter`), so introspecting `app.routes` found no `APIRoute`s. | `tests/architecture/test_routes_have_auth.py` is **behavioural**: it calls every OpenAPI operation with no token and with wrong roles. `archtest-author-agent` rule 2. |
| KD-03 | Tests opened SQLite connections without closing them, causing `ResourceWarning` under coverage. | Closing `db` fixture in `tests/conftest.py`. The `spec-to-test-generator` skill fixture table. |
| KD-04 | Speculative config (`nav_state_path`) was added before it was needed and never used. | Removed in Sprint 6. `doc-writer` checks settings against the spec's environment variables. |
| KD-05 | Enum validation at the API edge gave generic pydantic errors for override reasons. | `reason_code` is a string at the edge and validated in `override_policy` with the allowed values listed. `risk-profiler-agent` rule 3. |
| KD-06 | The phone layout hides `thead`, so one ARIA snapshot cannot serve both viewports. | Per-viewport baselines `*-{desktop,mobile}.aria.yml`. The evaluator notes in `.claude/agents/evaluator.md`. |
| KD-07 | **FL-001.** Template drafts cloned the active version verbatim, so a newly added asset class made every draft unpublishable. | Fix in `policy_admin_service._with_active_classes`. Regression test. `policy-version-validator` skill. `allocation-sum-invariant-check` hook message. Spec BR-21. |
| KD-08 | **PM-001.** Harness hooks read `/dev/stdin`, which throws `ENOENT` on Windows Node, so every hook silently exited 0. | All hooks read `fs.readFileSync(0)`. New hooks follow that pattern, and `tests/architecture/test_substrate_hooks.py` proves they block. |
| KD-09 | The Windows console (cp1252) crashed on `→` when the evaluator printed its report. | Scripts write UTF-8 bytes (`sys.stdout.buffer`). CI sets `PYTHONUTF8=1`. |
| KD-10 | Git Bash (MSYS) rewrote `"/.claude/"` into a Windows path, which broke `git sparse-checkout set`. | Use cone mode (`git sparse-checkout set --cone .claude`), or set `MSYS_NO_PATHCONV=1`. Recorded in PM-001. |
| KD-11 | A dashboard progress bar used `Number()` on a percentage string, which is float maths on financial data in the UI. | `capPct()` in integer basis points with a Vitest test. Spec §7.3 says the UI never does arithmetic on amounts. |
