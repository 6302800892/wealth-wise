---
name: rebalancing-quantity-proposer
description: How WealthWise computes BUY/SELL/HOLD quantities and handles proposal decisions (AC-07, BR-16 – BR-18). Load before editing rebalancing_proposer.py, rebalancing_service.py or rebalancing_repo.py.
---

# Rebalancing Quantity Proposer Skill

## Per asset class
```
target_value = total × target% / 100           → 0.01, ROUND_HALF_EVEN
delta        = target_value − value
units        = |delta| / NAV                   → 0.0001, ROUND_DOWN   (never overspend)
SELL units   = min(units, units held)
action       = BUY if delta > 0 and units > 0 · SELL if delta < 0 and units > 0 · otherwise HOLD (units 0.0000)
trade_value  = units × NAV                     → 0.01, ROUND_HALF_EVEN
```
CASH has NAV 1.0000, so the portfolio funds itself: sells fund buys through cash.

## E1 expected lines (AC-07.1)
EQUITY `SELL 666.6666` (₹99,999.99) · DEBT `BUY 4000.0000` (₹1,00,000.00) · GOLD `HOLD` · CASH `HOLD`

## Lifecycle
```
evaluate ──► supersede every OPEN proposal ──► create new OPEN one if max drift > threshold
OPEN ──accept──► ACCEPTED + one STUB_SUBMITTED order per BUY/SELL line (holdings unchanged)
OPEN ──dismiss(reason ≤ 500)──► DISMISSED
anything else ──► 409 RECOMMENDATION_NOT_OPEN ; another customer's proposal ──► 404
```
- Decisions are append-only rows in `rebalancing_decisions`. `UNIQUE(rebalancing_id)` makes a second decision impossible, even under a race.
- Every decision writes `audit_log` with the actor and a timestamp. Details hold IDs and flags only; the dismissal reason text never goes to the audit or the logs.

## Tests to keep green
`tests/unit/domain/test_rebalancing_proposer.py`, `tests/integration/api/test_rebalancing_api.py`, `tests/unit/service/test_rebalancing_service.py`, `tests/e2e/test_rebalancing_journey.py`.
