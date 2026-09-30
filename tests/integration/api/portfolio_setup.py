"""Builds a MODERATE/MEDIUM customer (target 50/35/10/5) with chosen holdings for rebalancing tests."""

from tests.integration.api.helpers import create_goal, profile_customer


def moderate_medium_customer(client, headers, holdings: dict[str, str]) -> dict:
    """Profile as MODERATE, add a MEDIUM-horizon goal, recommend, then record `holdings` (units by class)."""
    profile_customer(client, headers)
    goal = create_goal(client, headers, target="2031-06-30")
    recommendation = client.post("/api/v1/me/recommendations", json={}, headers=headers).json()
    assert recommendation["horizon_bucket"] == "MEDIUM"
    for code, units in holdings.items():
        response = client.post("/api/v1/me/holdings", json={"asset_class_code": code, "goal_id": goal["goal_id"],
                                                            "units": units}, headers=headers)
        assert response.status_code == 200, response.text
    return goal


# Total 150,000.00 at day-0 NAVs; EQUITY 55.00% / DEBT 30.00% → max drift exactly 5.00.
AT_THRESHOLD = {"EQUITY": "550.0000", "DEBT": "1800.0000", "GOLD": "300.0000", "CASH": "7500.0000"}
# EQUITY 55.01% / DEBT 29.99% → max drift 5.01.
ABOVE_THRESHOLD = {"EQUITY": "550.1000", "DEBT": "1799.4000", "GOLD": "300.0000", "CASH": "7500.0000"}
