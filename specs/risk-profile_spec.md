# Risk profile — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-RISK-PROFILE |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-01 |
| Business rules | BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-07 |
| Owning agent / skill | `risk-profiler-agent` / `risk-band-scorer` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Customers answer a versioned questionnaire. A deterministic score assigns CONSERVATIVE, MODERATE or AGGRESSIVE.

## 2. Business rules

**BR-01.** A rule set MUST contain at least 6 questions. Each question has 5 options scored 1–5.

| # | Question | Options (score) |
|---|---|---|
| Q1 | What is your age? | 60+ (1) · 50–59 (2) · 40–49 (3) · 30–39 (4) · under 30 (5) |
| Q2 | When will you need most of this money? | < 1 yr (1) · 1–3 yrs (2) · 3–5 yrs (3) · 5–10 yrs (4) · > 10 yrs (5) |
| Q3 | How stable is your income? | Very unstable (1) · Unstable (2) · Moderately stable (3) · Stable (4) · Very stable, several sources (5) |
| Q4 | Your portfolio falls 20% in a month. You… | Sell everything (1) · Sell some (2) · Do nothing (3) · Buy a little more (4) · Buy a lot more (5) |
| Q5 | Your investing experience? | None (1) · Savings/FDs only (2) · Mutual funds (3) · Stocks and mutual funds (4) · Advanced products (5) |
| Q6 | Your main objective? | Protect capital (1) · Regular income (2) · Balanced (3) · Growth (4) · Maximum growth (5) |

**BR-02.** `total_score` is the sum of the chosen option scores. Range for v1: 6–30.

**BR-03.** Band thresholds for v1. They are inclusive, contiguous and non-overlapping.

| Band | Score range |
|---|---|
| CONSERVATIVE | 6 – 13 |
| MODERATE | 14 – 22 |
| AGGRESSIVE | 23 – 30 |

**BR-04.** A submission MUST contain exactly one answer for every question in the named rule-set version, and every option ID MUST belong to its question. Anything else is rejected and nothing is saved.

**BR-05.** A customer's effective band is the `risk_band` of their **latest** `risk_band_assignments` row, whatever its source.

**BR-06.** A questionnaire submission creates one `risk_assessments` row and one assignment with `source = QUESTIONNAIRE`.

**BR-07.** An assignment with `source = ADVISOR_OVERRIDE` MUST reference a `risk_band_overrides` row (enforced by a DB `CHECK` constraint plus a service rule).

## 3. API surface

- `GET /api/v1/questionnaire`
- `POST /api/v1/me/risk-assessments`
- `GET /api/v1/me/risk-profile`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/risk_band_scorer.py`
- `src/service/risk_profile_service.py`
- `src/repository/risk_repo.py`
- `frontend/src/pages/customer/RiskProfilePage.jsx`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-01 — Risk-profile questionnaire assigns a deterministic risk band
- **AC-01.1** Given rule set v1 is active, when a customer requests the questionnaire, then the response contains `rule_set_version = 1` and 6 questions, each with 5 options.
- **AC-01.2** Given a customer answers all 6 questions with options scoring 3,3,3,3,2,2, when they submit, then `total_score = 16`, `risk_band = MODERATE`, the response is `201`, and one assessment plus one `QUESTIONNAIRE` assignment are saved.
- **AC-01.3** Given scores totalling 6, 13, 14, 22, 23 and 30, when scored, then the bands are CONSERVATIVE, CONSERVATIVE, MODERATE, MODERATE, AGGRESSIVE and AGGRESSIVE.
- **AC-01.4** Given a submission with a missing question, a duplicate answer, or an option that belongs to another question, when submitted, then the response is `422 INVALID_ANSWERS` and nothing is saved.
- **AC-01.5** Given every one of the 5⁶ = 15,625 answer combinations, when scored twice, then each maps to exactly one band and both runs give identical results.
- **AC-01.6** Given a customer has submitted the questionnaire, when they view their risk profile, then they see `risk_band`, `source = QUESTIONNAIRE`, `rule_set_version` and `assigned_at`.

## 6. Tests

- `tests/unit/domain/test_risk_band_scorer.py`
- `tests/integration/api/test_risk_profile_api.py`
- `tests/e2e/test_customer_journey.py`
