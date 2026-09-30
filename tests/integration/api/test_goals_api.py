"""AC-03: customers create and manage multiple financial goals."""

import pytest

from tests.integration.api.helpers import create_goal, goal_payload


@pytest.mark.ac("AC-03")
def test_create_goal_echoes_values(client, auth):
    """AC-03.1: POST /me/goals returns 201 with the goal ID and echoed fields."""
    goal = create_goal(client, auth("customer.beta"))
    assert goal["goal_id"]
    assert goal["name"] == "Home"
    assert goal["goal_type"] == "HOME"
    assert goal["target_amount"] == "2000000.00"
    assert goal["target_date"] == "2031-06-30"
    assert goal["priority"] == "HIGH"


@pytest.mark.ac("AC-03")
def test_multiple_goals_are_listed_by_priority_then_date(client, auth):
    """AC-03.2: three goals are listed ordered by priority, then target_date."""
    headers = auth("customer.beta")
    create_goal(client, headers, name="Car", priority="LOW", target="2028-01-31", goal_type="OTHER")
    create_goal(client, headers, name="School", priority="HIGH", target="2035-06-30", goal_type="EDUCATION")
    create_goal(client, headers, name="Retire", priority="HIGH", target="2050-03-31", goal_type="RETIREMENT")
    names = [g["name"] for g in client.get("/api/v1/me/goals", headers=headers).json()["items"]]
    assert names == ["School", "Retire", "Car"]


@pytest.mark.ac("AC-03")
@pytest.mark.parametrize("amount", ["0.00", "1000000000.01", "10.123", 2000000.0, 2000000])
def test_invalid_target_amount_returns_422(client, auth, amount):
    """AC-03.3: bad amounts, excess precision and JSON numbers are rejected with 422."""
    payload = goal_payload()
    payload["target_amount"] = amount
    response = client.post("/api/v1/me/goals", json=payload, headers=auth("customer.beta"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


@pytest.mark.ac("AC-03")
@pytest.mark.parametrize(("field", "value"), [("target_date", "2026-09-30"), ("priority", "URGENT")])
def test_invalid_date_or_priority_returns_422(client, auth, field, value):
    """AC-03.4: target_date on/before today or an unknown priority is rejected."""
    payload = goal_payload()
    payload[field] = value
    assert client.post("/api/v1/me/goals", json=payload, headers=auth("customer.beta")).status_code == 422


@pytest.mark.ac("AC-03")
def test_other_customers_goal_is_not_found(client, auth):
    """AC-03.5: customer B cannot read customer A's goal (404, not 403)."""
    goal = create_goal(client, auth("customer.beta"))
    response = client.get(f"/api/v1/me/goals/{goal['goal_id']}", headers=auth("customer.alpha"))
    assert response.status_code == 404


def test_update_and_archive_goal(client, auth):
    headers = auth("customer.beta")
    goal = create_goal(client, headers)
    updated = client.patch(f"/api/v1/me/goals/{goal['goal_id']}", json={"target_amount": "2500000.00"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["target_amount"] == "2500000.00"
    archived = client.patch(f"/api/v1/me/goals/{goal['goal_id']}", json={"archived": True}, headers=headers)
    assert archived.json()["archived"] is True
    assert client.get("/api/v1/me/goals", headers=headers).json()["items"] == []
