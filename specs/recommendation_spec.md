# Portfolio recommendation — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-RECOMMENDATION |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-02, AC-04 |
| Business rules | BR-08, BR-09, BR-10, BR-11, BR-24 |
| Owning agent / skill | `policy-version-validator-agent` / `policy-version-validator` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Map the effective risk band and the primary goal's horizon to a versioned allocation template. Identical inputs return the identical recommendation.

## 2. Business rules

**BR-08.**
`months = (target.year − as_of.year) × 12 + (target.month − as_of.month) − (1 if target.day < as_of.day else 0)`

| Bucket | Months |
|---|---|
| SHORT | months < 36 (includes past-due goals, where months ≤ 0) |
| MEDIUM | 36 ≤ months ≤ 84 |
| LONG | months > 84 |

**BR-09.** Every (band, horizon) row MUST list every asset class in the template set. Each percentage MUST be 0.00–100.00, and the row MUST sum to **exactly 100.00**.

| Band | Horizon | EQUITY | DEBT | GOLD | CASH | Sum |
|---|---|---|---|---|---|---|
| CONSERVATIVE | SHORT | 10 | 60 | 10 | 20 | 100 |
| CONSERVATIVE | MEDIUM | 20 | 60 | 10 | 10 | 100 |
| CONSERVATIVE | LONG | 30 | 55 | 10 | 5 | 100 |
| MODERATE | SHORT | 30 | 50 | 10 | 10 | 100 |
| MODERATE | MEDIUM | 50 | 35 | 10 | 5 | 100 |
| MODERATE | LONG | 60 | 27 | 10 | 3 | 100 |
| AGGRESSIVE | SHORT | 45 | 40 | 10 | 5 | 100 |
| AGGRESSIVE | MEDIUM | 70 | 20 | 7 | 3 | 100 |
| AGGRESSIVE | LONG | 80 | 12 | 5 | 3 | 100 |

**BR-10. Primary goal.** Among the customer's non-archived goals, pick the one with the highest priority (`HIGH` > `MEDIUM` > `LOW`). Break ties by earliest `target_date`, then earliest `created_at`, then lowest `id`. A request can name a specific `goal_id` instead.

**BR-11.** The allocation is the template row (effective band, horizon of the goal, **active** template version), where `as_of` is the injected business date. The `input_fingerprint` is SHA-256 of canonical JSON `{risk_band, horizon_bucket, template_version, goal_id}`.
- If the customer's latest recommendation has the same fingerprint, the existing recommendation is returned (`200`) and no new row is created.
- Otherwise a new recommendation is created (`201`).
- The same inputs therefore always produce identical output.

**BR-24.** `customers.kyc_verified` is a stub flag. If it is `false`, recommendation and rebalancing endpoints return `403 KYC_NOT_VERIFIED`. The questionnaire and goals remain available.

## 3. API surface

- `POST /api/v1/me/recommendations`
- `GET /api/v1/me/recommendations/latest`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/horizon_resolver.py`
- `src/domain/recommendation_resolver.py`
- `src/domain/allocation_template_validator.py`
- `src/domain/eligibility_policy.py`
- `src/service/recommendation_service.py`
- `frontend/src/pages/customer/RecommendationPage.jsx`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-02 — Versioned allocation templates that always sum to 100
- **AC-02.1** Given template set v1, when it is loaded, then it contains 9 (band × horizon) rows covering EQUITY, DEBT, GOLD and CASH, and every row sums to exactly `100.00`.
- **AC-02.2** Given a draft template whose row sums to 99.00 or 100.01, when an admin publishes it, then the response is `422 ALLOCATION_SUM_INVALID` naming the failing row, and the version stays `DRAFT`.
- **AC-02.3** Given a draft with a negative percentage or one above 100.00, when saved, then the response is `422 VALIDATION_FAILED`.
- **AC-02.4** Given a recommendation is returned, when its lines are summed, then the total is exactly `"100.00"` and the response includes `template_version`.

### AC-04 — Deterministic recommendation by risk band and goal horizon
- **AC-04.1** Given band MODERATE and a primary goal 120 months away (horizon LONG), when a recommendation is requested, then the allocation is EQUITY 60.00 · DEBT 27.00 · GOLD 10.00 · CASH 3.00, and it records `template_version`, `horizon_bucket` and `risk_band`.
- **AC-04.2** Given as_of = 2026-09-30 and target dates 2029-09-29, 2029-09-30, 2033-09-30 and 2033-10-30, when the horizon is resolved, then the buckets are SHORT, MEDIUM, MEDIUM and LONG.
- **AC-04.3** Given a HIGH goal due in 2040 and a MEDIUM goal due in 2028, when no `goal_id` is supplied, then the HIGH goal is primary (BR-10).
- **AC-04.4** Given identical inputs, when a recommendation is requested twice, then the second call returns `200` with the same recommendation ID, lines and fingerprint, and no new row is created.
- **AC-04.5** Given a customer with no risk band, no goals, or `kyc_verified = false`, when a recommendation is requested, then the response is `409 RISK_PROFILE_REQUIRED`, `409 GOAL_REQUIRED` or `403 KYC_NOT_VERIFIED` respectively.

## 6. Tests

- `tests/unit/domain/test_horizon_resolver.py`
- `tests/unit/domain/test_recommendation_resolver.py`
- `tests/unit/domain/test_allocation_template_validator.py`
- `tests/integration/api/test_recommendation_api.py`
- `tests/architecture/test_allocation_sum_invariant.py`
