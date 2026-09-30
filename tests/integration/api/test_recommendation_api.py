"""AC-02 / AC-04: recommendation by risk band and goal horizon, deterministic and sum-to-100."""

from decimal import Decimal

import pytest

from tests.integration.api.helpers import create_goal, profile_customer


def _recommend(client, headers, goal_id=None):
    return client.post("/api/v1/me/recommendations", json={"goal_id": goal_id}, headers=headers)


@pytest.mark.ac("AC-04")
def test_moderate_long_goal_gets_template_allocation(client, auth):
    """AC-04.1: MODERATE with a goal 120 months away → 60/27/10/3 with versions recorded."""
    headers = auth("customer.beta")
    profile_customer(client, headers)
    create_goal(client, headers, target="2036-09-30")
    response = _recommend(client, headers)
    assert response.status_code == 201
    body = response.json()
    assert body["risk_band"] == "MODERATE"
    assert body["horizon_bucket"] == "LONG"
    assert body["template_version"] == 1
    assert {a["asset_class_code"]: a["target_pct"] for a in body["allocation"]} == {
        "EQUITY": "60.00", "DEBT": "27.00", "GOLD": "10.00", "CASH": "3.00"}


@pytest.mark.ac("AC-02")
def test_recommendation_lines_sum_to_exactly_100(client, auth):
    """AC-02.4: allocation lines sum to exactly "100.00" and include template_version."""
    headers = auth("customer.beta")
    profile_customer(client, headers, scores=(1, 1, 1, 1, 1, 1))
    create_goal(client, headers, target="2028-06-30")
    body = _recommend(client, headers).json()
    assert body["total_pct"] == "100.00"
    assert sum(Decimal(a["target_pct"]) for a in body["allocation"]) == Decimal("100.00")
    assert body["template_version"] == 1


@pytest.mark.ac("AC-04")
def test_same_inputs_return_same_recommendation(client, auth):
    """AC-04.4: a repeated request returns 200 with the same ID, lines and fingerprint."""
    headers = auth("customer.beta")
    profile_customer(client, headers)
    create_goal(client, headers)
    first = _recommend(client, headers)
    second = _recommend(client, headers)
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json() == second.json()


@pytest.mark.ac("AC-04")
def test_explicit_goal_id_uses_that_goals_horizon(client, auth):
    """AC-04: goal_id selects a specific goal instead of the primary goal."""
    headers = auth("customer.beta")
    profile_customer(client, headers)
    create_goal(client, headers, name="Long", target="2045-01-31")
    short = create_goal(client, headers, name="Short", priority="LOW", target="2027-12-31", goal_type="OTHER")
    body = _recommend(client, headers, short["goal_id"]).json()
    assert body["horizon_bucket"] == "SHORT"
    assert body["goal_id"] == short["goal_id"]


@pytest.mark.ac("AC-04")
def test_preconditions_are_enforced(client, auth):
    """AC-04.5: no band → 409 RISK_PROFILE_REQUIRED; no goal → 409 GOAL_REQUIRED; no KYC → 403."""
    beta = auth("customer.beta")
    assert _recommend(client, beta).json()["error"]["code"] == "RISK_PROFILE_REQUIRED"
    profile_customer(client, beta)
    missing_goal = _recommend(client, beta)
    assert (missing_goal.status_code, missing_goal.json()["error"]["code"]) == (409, "GOAL_REQUIRED")
    gamma = _recommend(client, auth("customer.gamma"))
    assert (gamma.status_code, gamma.json()["error"]["code"]) == (403, "KYC_NOT_VERIFIED")


def test_latest_recommendation_for_seeded_customer(client, auth):
    body = client.get("/api/v1/me/recommendations/latest", headers=auth("customer.alpha")).json()
    assert body["risk_band"] == "MODERATE"
    assert body["horizon_bucket"] == "MEDIUM"


def test_latest_without_recommendation_is_404(client, auth):
    assert client.get("/api/v1/me/recommendations/latest", headers=auth("customer.beta")).status_code == 404
