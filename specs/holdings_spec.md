# Holdings and drift — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-HOLDINGS |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-05 |
| Business rules | BR-12, BR-13, BR-14, BR-25 |
| Owning agent / skill | `rebalancing-agent` / `drift-calculator` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Value goal-tagged holdings at the latest stub NAV and report per-asset-class drift against the customer's latest recommendation. All maths is fixed point.

## 2. Business rules

**BR-12.** `value = units × NAV` for the latest `nav_date`, quantised to 0.01 (`ROUND_HALF_EVEN`). `total = Σ value`.

**BR-13.** `current% = value × 100 / total`, quantised to 0.01 (`ROUND_HALF_EVEN`). If `total = 0`, drift is not computed and the status is `NO_HOLDINGS`.

**BR-14.** `drift = abs(current% − target%)` in percentage points, where `target%` comes from the customer's **latest portfolio recommendation**, using the template version recorded on it. An asset class that is held but missing from the target has `target% = 0.00`.

**BR-25.** The NAV feed stub reads `seed/nav_feed.csv` (`nav_date, asset_class_code, nav`).
- Each refresh ingests the next `nav_date` that has not been processed yet.
- When the file runs out, it carries the last NAVs forward to the next calendar day.
- Schedule: `WEALTHWISE_NAV_REFRESH_INTERVAL_SECONDS` (default `0`, meaning disabled; trigger it manually).
- One refresh runs these steps in order: ingest NAV → goal snapshots (BR-19) → rebalancing evaluation (BR-17).

## 3. API surface

- `GET /api/v1/me/holdings`
- `POST /api/v1/me/holdings`
- `POST /api/v1/admin/nav/refresh`
- `GET /api/v1/admin/nav/latest`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/drift_calculator.py`
- `src/service/holdings_service.py`
- `src/service/nav_service.py`
- `src/repository/holdings_repo.py`
- `src/repository/nav_repo.py`
- `frontend/src/pages/customer/HoldingsPage.jsx`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-05 — Holdings valuation and per-asset-class drift
- **AC-05.1** Given portfolio E1, when holdings are viewed, then values are 600,000.00 / 250,000.00 / 100,000.00 / 50,000.00 and the total is 1,000,000.00.
- **AC-05.2** Given portfolio E1, when drift is calculated, then current% is 60.00 / 25.00 / 10.00 / 5.00 and drift is 10.00 / 10.00 / 0.00 / 0.00.
- **AC-05.3** Given holdings whose current% rounds (for example 1/3 of the total), when calculated, then results are quantised to 0.01 with `ROUND_HALF_EVEN` using `Decimal` only.
- **AC-05.4** Given a customer with no holdings, when holdings are viewed, then total is `"0.00"`, drift is `null` and `drift_status = NO_HOLDINGS`.

## 6. Tests

- `tests/unit/domain/test_drift_calculator.py`
- `tests/unit/service/test_nav_service.py`
- `tests/integration/api/test_holdings_api.py`
- `tests/e2e/test_rebalancing_journey.py`
