# Rebalancing — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-REBALANCING |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-06, AC-07 |
| Business rules | BR-15, BR-16, BR-17, BR-18 |
| Owning agent / skill | `rebalancing-agent` / `rebalancing-quantity-proposer` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

When max drift exceeds the configured threshold, propose BUY/SELL quantities that restore the target. The customer accepts (which places stub orders) or dismisses, and either decision is audited.

## 2. Business rules

**BR-15. Trigger.** A rebalancing recommendation is generated when `max(drift) > threshold`. The comparison is **strictly greater than**. The threshold comes from config `WEALTHWISE_DRIFT_THRESHOLD_PCT` (default `5.00`) and is recorded on each recommendation.

**BR-16. Quantities.** For each asset class:
- `target_value = total × target% / 100`, quantised to 0.01 (`HALF_EVEN`)
- `delta = target_value − value`
- `units = abs(delta) / NAV`, quantised to 0.0001 (`ROUND_DOWN`)
- Action is `BUY` if `delta > 0` and `units > 0`, `SELL` if `delta < 0` and `units > 0`, otherwise `HOLD`.
- `SELL` units are capped at the units currently held.
- `CASH` always has NAV `1.0000`.

**BR-17. Evaluation lifecycle.** Evaluation runs after every NAV refresh, for each KYC-verified customer who has holdings and a portfolio recommendation. It also runs on demand. Each evaluation first marks any `OPEN` rebalancing recommendation for that customer as `SUPERSEDED`, then creates a new one only if BR-15 triggers.

**BR-18. Decisions.** Only an `OPEN` recommendation can be accepted or dismissed, and only by its own customer.
- Accepting creates one `stub_orders` row per BUY/SELL line with status `STUB_SUBMITTED`. Holdings do **not** change, because execution is out of scope.
- Every decision writes a `rebalancing_decisions` row and an `audit_log` row, both with actor and timestamp.

## 3. API surface

- `POST /api/v1/me/rebalancing/evaluate`
- `GET /api/v1/me/rebalancing`
- `POST /api/v1/me/rebalancing/{id}/accept`
- `POST /api/v1/me/rebalancing/{id}/dismiss`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/rebalancing_proposer.py`
- `src/service/rebalancing_service.py`
- `src/repository/rebalancing_repo.py`
- `frontend/src/pages/customer/RebalancingPage.jsx`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-06 — Rebalancing triggered when drift exceeds the threshold
- **AC-06.1** Given portfolio E1 and threshold 5.00, when rebalancing is evaluated, then an `OPEN` rebalancing recommendation is created with `max_drift = 10.00`.
- **AC-06.2** Given a portfolio whose largest drift is exactly 5.00, when evaluated, then nothing is created. Given 5.01, one is created.
- **AC-06.3** Given portfolio E1 and threshold 12.00, when evaluated, then nothing is created.
- **AC-06.4** Given an existing `OPEN` recommendation, when evaluation runs again, then the old one becomes `SUPERSEDED` and at most one `OPEN` recommendation exists.
- **AC-06.5** Given a NAV refresh, when it completes, then evaluation has run for every eligible customer (BR-17).

### AC-07 — BUY/SELL proposal with accept or dismiss and audit
- **AC-07.1** Given portfolio E1, when the proposal is generated, then it has a UUID `recommendation_id` and lines EQUITY `SELL 666.6666` · DEBT `BUY 4000.0000` · GOLD `HOLD 0.0000` · CASH `HOLD 0.0000`.
- **AC-07.2** Given a computed SELL larger than the units held, when proposed, then SELL units equal the units held.
- **AC-07.3** Given an `OPEN` recommendation, when the customer accepts it, then its status is `ACCEPTED`, 2 stub orders exist with `STUB_SUBMITTED`, holdings are unchanged, and the decision and audit rows record actor and timestamp.
- **AC-07.4** Given an `OPEN` recommendation, when the customer dismisses it with an optional reason (≤ 500 chars), then its status is `DISMISSED` with actor and timestamp audited.
- **AC-07.5** Given an `ACCEPTED`, `DISMISSED` or `SUPERSEDED` recommendation, when accept or dismiss is attempted, then the response is `409 RECOMMENDATION_NOT_OPEN`. Given another customer's recommendation, the response is `404`.

## 6. Tests

- `tests/unit/domain/test_rebalancing_proposer.py`
- `tests/unit/service/test_rebalancing_service.py`
- `tests/integration/api/test_rebalancing_api.py`
- `tests/e2e/test_rebalancing_journey.py`
