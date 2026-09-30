# Evaluator review — Sprint 4 (Advisor workbench + admin policy versioning)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-4.json` |
| Branch | `sprint-4/advisor-admin` |
| ACs | AC-09, AC-10, AC-02.2, AC-02.3 |
| Verdict | **PASS**. Ratchet advanced from 93% to 94% |

## Layer 1 — Tests
- `pytest`: **295 passed**, 0 failed
- Coverage (`src/`): **94%**
- `test_ac_traceability.py`: all 10 ACs have tagged tests, and no tag references an unknown AC.
- `test_pii_not_logged.py`: full journeys with sentinel names, emails, amounts and notes produce **no leaks** in the JSON logs.

## Layer 2 — Live API checks
**9/9 PASS** (`sprint-4-api-evaluation.md`). Draft cloning works, single-draft is enforced, v1 is immutable, and the in-flight customer stays on v1 after v2 is published.

## Layer 3 — Architecture
| Check | Result |
|---|---|
| `ADVISOR_OVERRIDE` assignment without an override record | Rejected by CHECK; a dangling id is rejected by FK |
| Override writes override + assignment + audit in one transaction | PASS |
| Advisor note visible to the advisor, hidden from the customer | PASS (AC-09.5) |
| `manual_recommendations` append-only | PASS |

## Findings
1. **Design choice.** `reason_code` is accepted as a string at the API edge and validated in the domain (`override_policy`). An unknown reason then returns the same `VALIDATION_FAILED` envelope with a helpful list of allowed values.
2. **Open item for Sprint 5.** The UI and Playwright E2E are still to build, and the evaluator's Playwright MCP checks start in Sprint 5.
