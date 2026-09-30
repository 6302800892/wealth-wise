# Admin policy versioning — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-ADMIN-POLICY |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-10 |
| Business rules | BR-21, BR-22, BR-23 |
| Owning agent / skill | `policy-version-validator-agent` / `policy-version-validator` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Admins manage the asset-class master and publish new versions of risk rule sets and allocation templates. Published versions are immutable, and in-flight customers keep their version.

## 2. Business rules

**BR-21.** Rule sets and template sets each have integer versions: 1, 2, 3 and so on.
- At most one `DRAFT` of each type can exist at a time. It is created by cloning the active version.
- A template draft also contains every **active** asset class that the active version lacks, at `0.00`, so the draft can always be edited into a publishable state (FL-001).
- The **active** version is the highest `PUBLISHED` version.

**BR-22. Publish validation.**
- Templates: BR-09 holds for all 9 (band × horizon) rows, and every active asset class is present.
- Rule sets: BR-01 holds, and the band thresholds are contiguous, non-overlapping and cover the full score range [min, max].

**BR-23.** A `PUBLISHED` version and its child rows are **immutable**. The API returns `409 VERSION_IMMUTABLE`, and SQLite triggers `RAISE(ABORT)` on any `UPDATE` or `DELETE`.
- Existing assessments and recommendations keep the version they recorded. Drift and rebalancing always use the template version on the customer's latest recommendation (the in-flight rule).
- A questionnaire submitted against a version that is no longer active returns `409 RULE_SET_NOT_ACTIVE`.

## 3. API surface

- `GET|POST /api/v1/admin/risk-rule-sets`
- `GET|PUT /api/v1/admin/risk-rule-sets/{version}`
- `POST /api/v1/admin/risk-rule-sets/{version}/publish`
- `GET|POST /api/v1/admin/allocation-templates`
- `GET|PUT /api/v1/admin/allocation-templates/{version}`
- `POST /api/v1/admin/allocation-templates/{version}/publish`
- `GET|POST|PATCH /api/v1/admin/asset-classes`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/version_policy.py`
- `src/service/policy_admin_service.py`
- `src/service/asset_class_service.py`
- `src/repository/policy_repo.py`
- `migrations/0003_policy_versions.sql`
- `frontend/src/pages/admin/`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-10 — Versioned rules and templates, immutable once published, with the in-flight rule
- **AC-10.1** Given a template draft v2, when an admin publishes it, then v2 is `PUBLISHED`, active, and records `published_by` and `published_at`.
- **AC-10.2** Given published v1, when an admin tries to edit it through the API, then the response is `409 VERSION_IMMUTABLE`. When a raw SQL `UPDATE` or `DELETE` targets it, then SQLite aborts.
- **AC-10.3** Given a customer with a recommendation on template v1, when v2 (with different MODERATE/MEDIUM percentages) is published, then that customer's drift and rebalancing still use v1 targets until they request a new recommendation, which uses v2.
- **AC-10.4** Given rule set v2 was published after a customer loaded v1, when they submit v1 answers, then the response is `409 RULE_SET_NOT_ACTIVE`.
- **AC-10.5** Given a rule-set draft with overlapping or gapped band thresholds, when published, then the response is `422` and it stays `DRAFT`.

## 6. Tests

- `tests/unit/domain/test_version_policy.py`
- `tests/integration/api/test_admin_versioning_api.py`
- `tests/architecture/test_published_immutable.py`
- `tests/e2e/test_advisor_admin_journeys.py`
