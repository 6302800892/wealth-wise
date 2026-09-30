# Evaluator review — Sprint 3 (Rebalancing + goal tracker)

| Field | Value |
|---|---|
| Contract | `sprint-contracts/sprint-3.json` |
| Branch | `sprint-3/rebalancing-goal-tracker` |
| ACs | AC-06, AC-07, AC-08 |
| Verdict | **PASS**. Ratchet advanced from 91% to 93% |

## Layer 1 — Tests
- `pytest`: **236 passed**, 0 failed
- Coverage (`src/`): **93%**
- Boundary evidence: max drift exactly `5.00` does not trigger; `5.01` does (`test_rebalancing_api.py`).
- E1 proposal: `SELL 666.6666 EQUITY`, `BUY 4000.0000 DEBT`, `HOLD` for GOLD and CASH.

## Layer 2 — Live API checks
**7/7 PASS** (`sprint-3-api-evaluation.md`). The refresh cycle writes 2 goal snapshots, evaluates 1 eligible customer and advances one day per call.

## Layer 3 — Architecture
| Check | Result |
|---|---|
| 12 append-only tables guarded | PASS |
| One decision per proposal enforced by `UNIQUE(rebalancing_id)`; a second decision maps to `409 RECOMMENDATION_NOT_OPEN` | PASS |
| Stub orders never touch holdings | PASS (`test_accept_creates_stub_orders_and_audit`) |
| Audit rows carry IDs only (`has_reason` flag, never the reason text) | PASS |

## Findings
1. **Refactor.** Lazy imports in `nav_service` and `scheduler` were unnecessary because there is no import cycle. They are now top-level imports, so import-linter can see the dependency.
2. **Note.** The refresh cycle is one transaction (ingest → snapshots → evaluation). A failure in any step rolls back the NAV day, so the next attempt retries the same date.
