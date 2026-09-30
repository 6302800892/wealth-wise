"""AC-05: holdings, valuation and per-asset-class drift over HTTP (seeded portfolio E1 for alpha)."""

import pytest

from tests.integration.api.helpers import create_goal


def _lines(body):
    return {line["asset_class_code"]: line for line in body["lines"]}


@pytest.mark.ac("AC-05")
def test_seeded_portfolio_e1_values(client, auth):
    """AC-05.1: alpha's holdings are valued 600,000 / 250,000 / 100,000 / 50,000 = 1,000,000.00."""
    body = client.get("/api/v1/me/holdings", headers=auth("customer.alpha")).json()
    lines = _lines(body)
    assert body["total_value"] == "1000000.00"
    assert [lines[c]["value"] for c in ["EQUITY", "DEBT", "GOLD", "CASH"]] == [
        "600000.00", "250000.00", "100000.00", "50000.00"]
    assert body["nav_date"] == "2026-09-30"


@pytest.mark.ac("AC-05")
def test_seeded_portfolio_e1_drift(client, auth):
    """AC-05.2: current% 60/25/10/5 vs target 50/35/10/5 → drift 10/10/0/0, flagged above threshold."""
    body = client.get("/api/v1/me/holdings", headers=auth("customer.alpha")).json()
    lines = _lines(body)
    assert [lines[c]["current_pct"] for c in ["EQUITY", "DEBT", "GOLD", "CASH"]] == ["60.00", "25.00", "10.00", "5.00"]
    assert [lines[c]["drift_pct"] for c in ["EQUITY", "DEBT", "GOLD", "CASH"]] == ["10.00", "10.00", "0.00", "0.00"]
    assert body["max_drift_pct"] == "10.00"
    assert body["threshold_pct"] == "5.00"
    assert lines["EQUITY"]["exceeds_threshold"] is True
    assert lines["GOLD"]["exceeds_threshold"] is False


@pytest.mark.ac("AC-05")
def test_customer_without_holdings(client, auth):
    """AC-05.4: no holdings → total "0.00", drift null, drift_status NO_HOLDINGS."""
    body = client.get("/api/v1/me/holdings", headers=auth("customer.beta")).json()
    assert body["total_value"] == "0.00"
    assert body["max_drift_pct"] is None
    assert body["drift_status"] in {"NO_HOLDINGS", "NO_RECOMMENDATION"}


@pytest.mark.ac("AC-05")
def test_record_holding_updates_valuation(client, auth):
    """AC-05: recording a holding (string units) is reflected in the valuation."""
    headers = auth("customer.beta")
    goal = create_goal(client, headers)
    response = client.post("/api/v1/me/holdings", json={"asset_class_code": "EQUITY", "goal_id": goal["goal_id"],
                                                        "units": "10.5000"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert _lines(body)["EQUITY"]["units"] == "10.5000"
    assert body["total_value"] == "1575.00"


@pytest.mark.ac("AC-05")
@pytest.mark.parametrize("payload", [
    {"asset_class_code": "EQUITY", "units": 10.5},
    {"asset_class_code": "EQUITY", "units": "-1.0000"},
    {"asset_class_code": "EQUITY", "units": "1.00001"},
    {"asset_class_code": "CRYPTO", "units": "1.0000"},
])
def test_invalid_holdings_are_rejected(client, auth, payload):
    """AC-05 / NFR-01: float units, negative or over-precise units and unknown classes are rejected."""
    response = client.post("/api/v1/me/holdings", json=payload, headers=auth("customer.beta"))
    assert response.status_code in {404, 422}


def test_holding_for_another_customers_goal_is_not_found(client, auth):
    goal = create_goal(client, auth("customer.beta"))
    response = client.post("/api/v1/me/holdings", json={"asset_class_code": "EQUITY", "goal_id": goal["goal_id"],
                                                        "units": "1.0000"}, headers=auth("customer.alpha"))
    assert response.status_code == 404


def test_admin_can_trigger_nav_refresh_and_read_latest(client, auth):
    headers = auth("admin.one")
    before = client.get("/api/v1/admin/nav/latest", headers=headers).json()
    refreshed = client.post("/api/v1/admin/nav/refresh", headers=headers)
    assert refreshed.status_code == 200
    assert refreshed.json()["nav_date"] > before["nav_date"]
    assert client.get("/api/v1/admin/nav/latest", headers=headers).json()["nav_date"] == refreshed.json()["nav_date"]
