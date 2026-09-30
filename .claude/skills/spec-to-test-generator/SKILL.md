---
name: spec-to-test-generator
description: Converts Given-When-Then acceptance scenarios from specs/*_spec.md into AC-tagged pytest / Playwright tests, committed red before implementation. Load at the start of every story.
---

# Spec-to-Test Generator Skill

## Input → output
| Spec line | Test |
|---|---|
| `- **AC-05.2** Given portfolio E1, when drift is calculated, then …` | `@pytest.mark.ac("AC-05")` + docstring `"""AC-05.2: …"""` |

## Where each kind of scenario goes
| Scenario is about… | Location | Fixture |
|---|---|---|
| a pure rule (score, horizon, drift, quantities) | `tests/unit/domain/test_<rule_file>.py` | `tests/factories.py` builders |
| orchestration / transactions / refresh cycle | `tests/unit/service/` | `settings`, `clock`, `db`, `open_context` |
| HTTP status, envelope, role, persistence | `tests/integration/api/test_<feature>_api.py` | `client`, `auth`, `db` |
| a structural invariant | `tests/architecture/` | `db`, `app` |
| a user-visible journey | `tests/e2e/` with `pytestmark = pytest.mark.e2e` | `ui` (both viewports), `check_aria` |

## Rules
1. **Tag everything.** The marker must match an `### AC-NN` heading in `specs/app_spec.md`. `test_ac_traceability.py` fails on unknown or missing ACs.
2. **Red first.** Commit the tests (`test(<sprint>): … (red)`) before the implementation commit, and show the failing run in the sprint review.
3. **Use spec numbers verbatim.** Worked examples such as E1, score 16 and the horizon boundaries at 35/36/84/85 months are assertions, not illustrations.
4. **Determinism.** Fixed clock 2026-09-30, a temp SQLite DB per test, and no sleeps. E2E starts a fresh server per module.
5. **Money in tests.** Send strings (`"2000000.00"`). Also add one negative test that sends a JSON number and expects 422.
