# Evaluator review — Sprint 2 (Holdings + drift)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-2.json` |
| Branch | `sprint-2/holdings-drift` |
| ACs | AC-05 (plus NFR-01 and the BR-25 feed stub) |
| Verdict | **PASS**. Ratchet advanced from 90% to 91% |

## Layer 1 — Tests
- `pytest`: **192 passed**, 0 failed
- Coverage (`src/`): **91%**
- Red → green: `test(sprint-2): …` precedes `feat(sprint-2): …`

## Layer 2 — Live API checks
**8/8 PASS** (`sprint-2-api-evaluation.md`):
- The seeded portfolio E1 is valued at exactly 1,000,000.00 with max drift 10.00.
- The next refresh ingests 2026-10-01.
- Float units are rejected.

## Layer 3 — Architecture
| Check | Result |
|---|---|
| No float in `types/domain/repository/service` (AST scan) | PASS (includes the new drift calculator) |
| `nav_prices` append-only | PASS |
| Holdings keyed uniquely by (customer, goal, class), with an expression index so NULL goals dedupe | PASS |

## Findings
1. **Design check.** Drift targets come from the recommendation's own stored lines, not the active template. The in-flight rule (AC-10.3) therefore holds by construction. Verified again in Sprint 4.
2. **Observation.** The NAV feed position comes from `MAX(nav_date)` in the DB, so no separate cursor file is needed. `nav_state_path` is unused. Remove it in a later cleanup (KD-04).
