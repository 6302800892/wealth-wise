# TDD discipline — red → green → refactor

## Approach
1. **Spec scenario → test.** Every Given-When-Then scenario (`AC-NN.n` in `specs/app_spec.md` §9) becomes at least one test. The test is tagged `@pytest.mark.ac("AC-NN")` and its docstring starts with the scenario id (`spec-to-test-generator` skill).
2. **Red commit.** The failing tests are committed on their own (`test(<sprint>): … (red)`). The sprint review records the failing run.
3. **Green commit.** The smallest implementation that passes is committed separately (`feat(<sprint>): … (green)`).
4. **Refactor.** Cleanups land with the suite still green, for example removing lazy imports in Sprint 3 and the unused `nav_state_path` in Sprint 6. The coverage ratchet (`.claude/state/coverage-baseline.txt`) must not go down.

## Evidence in git history
| Red commit | Green commit | Scope |
|---|---|---|
| `472e1ed` test(sprint-0) | `000ff23` feat(sprint-0) | fixed point, logging, migrations, health/auth, architecture tests |
| `3c127c1` test(sprint-1) | `0bcbc2b` feat(sprint-1) | AC-01 – AC-04 |
| `0c07b7b` test(sprint-2) | `8ca2165` feat(sprint-2) | AC-05, NAV feed |
| `0a77bc2` test(sprint-3) | `654d4eb` feat(sprint-3) | AC-06 – AC-08 |
| `303732d` test(sprint-4) | `7915710` feat(sprint-4) | AC-09, AC-10 |
| `620b5c2` test(sprint-5) | `f6233d4` feat(sprint-5) | frontend fixed-point helpers, routing, API client |
| `696f17c` test(FL-001) | `314093f` fix(FL-001) | regression: new asset class in drafts |

40 test files were added across these commits: backend unit, service, integration, architecture and E2E, plus 3 Vitest files.

**Honest exception.** The Playwright E2E journeys (`1f6c633`) were written *after* the pages, because the UI's `data-testid` contract settled while the pages were built. The unit layers underneath them were test-first.

## Worked example — AC-02 allocation-sum invariant

**Scenario (AC-02.2).** Given a draft template whose MODERATE/MEDIUM row sums to 99.00 or 100.01, when an admin publishes it, then the response is `422 ALLOCATION_SUM_INVALID` naming the row, and the version stays `DRAFT`.

### Red
The domain test was written first, in `tests/unit/domain/test_allocation_template_validator.py`:
```python
@pytest.mark.ac("AC-02")
@pytest.mark.parametrize("pcts", [("50", "35", "10", "4"), ("50", "35", "10", "5.01")])
def test_row_not_summing_to_100_blocks_publish(pcts):
    """AC-02.2: rows summing to 99.00 or 100.01 fail with ALLOCATION_SUM_INVALID naming the row."""
    rows = template_rows({KEY: _row(*pcts)})
    with pytest.raises(WealthWiseError) as exc:
        check_publishable(rows, ASSET_ORDER)
    assert exc.value.code == "ALLOCATION_SUM_INVALID"
    assert "MODERATE/MEDIUM" in exc.value.message
```
At commit `3c127c1`, collection failed with `ModuleNotFoundError: src.domain.allocation_template_validator`. That is the red state.

### Green
The minimal rule was added in `src/domain/allocation_template_validator.py`: sum each row in `Decimal`, quantise to 0.01, compare with `HUNDRED`, and collect every failing row label into one `ALLOCATION_SUM_INVALID` error. Because the sum uses `Decimal` rather than floats, 50 + 35 + 10 + 5.01 equals exactly 100.01, not 100.00999….

### Layering the same invariant
| Layer | Test / guard | Catches |
|---|---|---|
| Domain | `check_publishable` unit tests | the rule itself |
| API | `test_publish_rejects_rows_not_summing_to_100` (AC-02.2) | the status code, the envelope, and the version staying DRAFT |
| DB | `tests/architecture/test_allocation_sum_invariant.py` | any published row in the database ≠ 10 000 bp |
| Authoring | `.claude/hooks/allocation-sum-invariant-check.js` | a hand-written migration seeding a bad row, before it is committed |
| UI | `sumPct()` in integer basis points (Vitest) and the E2E 99.00 → blocked → 100.00 → published journey | the admin sees the error |

### Refactor
Range checks (0–100, at most 2 dp) were split into `check_row_ranges`, which runs on every draft save. The full coverage and sum check runs on publish only. Drafts can be work in progress, but they can never be published broken. FL-001 then showed that drafts also need every active asset class, which led to a new regression test and fix.
