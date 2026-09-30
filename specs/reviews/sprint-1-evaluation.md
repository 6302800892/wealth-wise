# Evaluator review — Sprint 1 (Risk profile + recommendation)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-1.json` |
| Branch | `sprint-1/risk-profile-recommendation` |
| ACs | AC-01, AC-02, AC-03, AC-04, AC-10.4 |
| Verdict | **PASS**. Ratchet advanced from 82% to 90% |

## Layer 1 — Tests
- `pytest`: **159 passed**, 0 failed, 0 warnings
- Coverage (`src/`): **90%**
- Red → green: `test(sprint-1): failing tests …` precedes `feat(sprint-1): …`
- Determinism: `test_every_answer_combination_maps_to_exactly_one_band_deterministically` scores all 15,625 answer combinations twice.

## Layer 2 — Live API checks
**11/11 PASS** (`sprint-1-api-evaluation.md`), against a fresh server with seed data.

## Layer 3 — Architecture
| Check | Result |
|---|---|
| import-linter contracts | 5 KEPT |
| Every published template row sums to 10 000 bp | PASS |
| Raw SQL UPDATE/DELETE/INSERT on published v1 aborted by triggers | PASS (7 statements) |
| Append-only tables (7) guarded by triggers | PASS |
| An `ADVISOR_OVERRIDE` assignment without `override_id` violates the table CHECK | Enforced in `0006_risk_profile.sql`; test lands in Sprint 4 |

## Findings
1. **Fixed.** Tests left SQLite connections open, causing `ResourceWarning` under coverage. Added a closing `db` fixture. Knowledge deposit KD-03.
2. **Fixed.** The evaluator's console output failed on Windows cp1252 for `→`. It now writes raw UTF-8 bytes.
3. **Observation.** Seeding replays real use cases (questionnaire → goals → recommendation) inside one outer transaction. `transaction()` is now re-entrant, so the seed is atomic.
