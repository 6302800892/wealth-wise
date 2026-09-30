# Goals and goal tracker — Feature Specification

| Field | Value |
|---|---|
| Spec ID | SPEC-GOAL-TRACKER |
| Parent | `specs/app_spec.md` (the root spec wins on any conflict) |
| Acceptance criteria | AC-03, AC-08 |
| Business rules | BR-19 |
| Owning agent / skill | `rebalancing-agent` / `spec-to-test-generator` |
| Status | Implemented (see `specs/reviews/`) |

## 1. Purpose

Customers keep several goals, each with a target amount, date and priority. Progress is computed from goal-tagged holdings and snapshotted on every NAV refresh.

## 2. Business rules

**BR-19.** `current_goal_value = Σ value` of the holdings tagged with that `goal_id`. `percent_complete = current_goal_value × 100 / target_amount`, quantised to 0.01 (`HALF_EVEN`).
- The value is not capped. At 100.00 or above, the goal status is `ACHIEVED`.
- Each NAV refresh writes one snapshot per non-archived goal for that `nav_date`. Running it again for the same date is a no-op.

## 3. API surface

- `POST /api/v1/me/goals`
- `GET /api/v1/me/goals`
- `GET|PATCH /api/v1/me/goals/{goal_id}`
- `GET /api/v1/me/goals/{goal_id}/progress`

All money, units, NAV and percentage fields are decimal **strings**. Errors use the envelope in root spec §10.1.

## 4. Implementation map

- `src/domain/goal_policy.py`
- `src/domain/goal_progress_calculator.py`
- `src/service/goal_service.py`
- `src/service/goal_progress_service.py`
- `frontend/src/pages/customer/GoalsPage.jsx`
- `frontend/src/pages/customer/DashboardPage.jsx`

## 5. Acceptance Criteria

Each scenario is written as Given-When-Then. Its tests carry `@pytest.mark.ac("AC-NN")` and a docstring that starts with the scenario id.

### AC-03 — Customers create multiple financial goals
- **AC-03.1** Given a customer, when they create a goal with `name`, `goal_type = HOME`, `target_amount = "2000000.00"`, `target_date = 2031-06-30` and `priority = HIGH`, then the response is `201` with the goal ID and the same values echoed back.
- **AC-03.2** Given a customer who already has one goal, when they create a second and a third, then listing returns all three, ordered by priority, then target_date.
- **AC-03.3** Given `target_amount` ≤ 0, above `1000000000.00`, with more than 2 dp, or sent as a JSON number, when submitted, then the response is `422`.
- **AC-03.4** Given a `target_date` on or before today, or a priority outside the enum, when submitted, then the response is `422`.
- **AC-03.5** Given customer A's goal ID, when customer B requests it, then the response is `404`.

### AC-08 — Goal progress updated on each daily NAV refresh
- **AC-08.1** Given a goal with target 2,000,000.00 and tagged holdings EQUITY 2000 u @150.0000 plus DEBT 8000 u @25.0000, when progress is computed, then `current_goal_value = 500000.00` and `percent_complete = 25.00`.
- **AC-08.2** Given that goal, when a NAV refresh sets EQUITY to 153.0000, then a new snapshot for that `nav_date` shows 506,000.00 and 25.30.
- **AC-08.3** Given the refresh for the same `nav_date` runs twice, then exactly one snapshot per goal exists for that date.
- **AC-08.4** Given a goal with no tagged holdings, then `percent_complete = 0.00`. Given a value at or above the target, then the status is `ACHIEVED` and the percentage is not capped.

## 6. Tests

- `tests/unit/domain/test_goal_policy.py`
- `tests/unit/domain/test_goal_progress_calculator.py`
- `tests/integration/api/test_goals_api.py`
- `tests/integration/api/test_goal_progress_api.py`
