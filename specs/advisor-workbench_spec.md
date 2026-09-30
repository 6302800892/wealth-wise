# Advisor workbench — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-ADVISOR-WORKBENCH |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-09 |
| Business rules | BR-20 |
| Owning agent / skill | `risk-profiler-agent` / `risk-band-scorer` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Advisors see any customer's portfolio, override a risk band with an enumerated reason and a note (fully audited), and log manual recommendations.

## 2. Business rules

**BR-20.** An override needs all of the following:
- a `new_band` different from the current effective band
- a `reason_code` from `OverrideReason`
- a `note` of 1–1000 characters after trimming

It atomically writes a `risk_band_overrides` row (previous band, new band, reason, note, actor, timestamp), an `ADVISOR_OVERRIDE` assignment that references it, and an `audit_log` row.

## 3. API surface

- `GET /api/v1/advisor/customers`
- `GET /api/v1/advisor/customers/{id}/portfolio`
- `POST /api/v1/advisor/customers/{id}/risk-band-overrides`
- `GET /api/v1/advisor/customers/{id}/audit`
- `POST /api/v1/advisor/customers/{id}/manual-recommendations`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/override_policy.py`
- `src/service/advisor_service.py`
- `src/repository/advisor_repo.py`
- `frontend/src/pages/advisor/`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-09 — Advisor risk-band override with an audit trail
- **AC-09.1** Given a customer whose band is MODERATE, when an advisor overrides it to CONSERVATIVE with `reason_code = CHANGE_IN_CIRCUMSTANCES` and a note, then the response is `201`, the effective band is CONSERVATIVE with `source = ADVISOR_OVERRIDE`, and the override stores previous band, new band, reason, note, `actor_user_id` and `created_at`.
- **AC-09.2** Given a missing reason, a blank or whitespace-only note, or a note over 1000 characters, then the response is `422`. Given `new_band` equal to the current band, the response is `422 BAND_UNCHANGED`.
- **AC-09.3** Given a `CUSTOMER` or `ADMIN` token, when calling the override endpoint, then the response is `403`.
- **AC-09.4** Given an override, when the customer next requests a recommendation, then it uses the overridden band.
- **AC-09.5** Given several overrides, when an advisor views the audit history, then all appear newest first, and the customer view shows the band source but **not** the advisor's note.

## 6. Tests

- `tests/unit/domain/test_override_policy.py`
- `tests/integration/api/test_advisor_api.py`
- `tests/architecture/test_override_requires_audit.py`
- `tests/e2e/test_advisor_admin_journeys.py`
