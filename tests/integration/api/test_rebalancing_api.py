"""AC-06 / AC-07: drift-triggered rebalancing proposals, accept/dismiss with audit, append-only decisions."""

import pytest

from tests.integration.api.portfolio_setup import ABOVE_THRESHOLD, AT_THRESHOLD, moderate_medium_customer


def _evaluate(client, headers):
    response = client.post("/api/v1/me/rebalancing/evaluate", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _open(client, headers):
    items = client.get("/api/v1/me/rebalancing", headers=headers).json()["items"]
    return [item for item in items if item["status"] == "OPEN"]


@pytest.mark.ac("AC-06")
def test_portfolio_e1_triggers_open_recommendation(client, auth):
    """AC-06.1: E1 with threshold 5.00 → OPEN rebalancing recommendation with max_drift 10.00."""
    body = _evaluate(client, auth("customer.alpha"))
    assert body["triggered"] is True
    assert body["rebalancing"]["status"] == "OPEN"
    assert body["rebalancing"]["max_drift_pct"] == "10.00"
    assert body["rebalancing"]["threshold_pct"] == "5.00"


@pytest.mark.ac("AC-06")
def test_drift_exactly_at_threshold_does_not_trigger(client, auth):
    """AC-06.2: max drift exactly 5.00 → nothing created."""
    headers = auth("customer.beta")
    moderate_medium_customer(client, headers, AT_THRESHOLD)
    body = _evaluate(client, headers)
    assert body["max_drift_pct"] == "5.00"
    assert body["triggered"] is False
    assert _open(client, headers) == []


@pytest.mark.ac("AC-06")
def test_drift_just_above_threshold_triggers(client, auth):
    """AC-06.2: max drift 5.01 → one OPEN recommendation."""
    headers = auth("customer.beta")
    moderate_medium_customer(client, headers, ABOVE_THRESHOLD)
    body = _evaluate(client, headers)
    assert body["max_drift_pct"] == "5.01"
    assert body["triggered"] is True
    assert len(_open(client, headers)) == 1


@pytest.mark.ac("AC-06")
def test_re_evaluation_supersedes_previous_open(client, auth):
    """AC-06.4: a second evaluation marks the old OPEN recommendation SUPERSEDED; one OPEN remains."""
    headers = auth("customer.alpha")
    first = _evaluate(client, headers)["rebalancing"]["recommendation_id"]
    _evaluate(client, headers)
    statuses = {i["recommendation_id"]: i["status"] for i in client.get("/api/v1/me/rebalancing", headers=headers).json()["items"]}
    assert statuses[first] == "SUPERSEDED"
    assert list(statuses.values()).count("OPEN") == 1


@pytest.mark.ac("AC-07")
def test_proposal_lines_for_e1(client, auth):
    """AC-07.1: UUID recommendation_id and lines SELL 666.6666 EQUITY / BUY 4000.0000 DEBT / HOLD others."""
    rebalancing = _evaluate(client, auth("customer.alpha"))["rebalancing"]
    assert len(rebalancing["recommendation_id"]) == 36
    lines = {line["asset_class_code"]: (line["action"], line["units"]) for line in rebalancing["lines"]}
    assert lines == {"EQUITY": ("SELL", "666.6666"), "DEBT": ("BUY", "4000.0000"),
                     "GOLD": ("HOLD", "0.0000"), "CASH": ("HOLD", "0.0000")}


@pytest.mark.ac("AC-07")
def test_accept_creates_stub_orders_and_audit(client, auth, db):
    """AC-07.3: accept → ACCEPTED, 2 STUB_SUBMITTED orders, holdings unchanged, audit with actor + timestamp."""
    headers = auth("customer.alpha")
    before = client.get("/api/v1/me/holdings", headers=headers).json()["positions"]
    rec_id = _evaluate(client, headers)["rebalancing"]["recommendation_id"]
    body = client.post(f"/api/v1/me/rebalancing/{rec_id}/accept", headers=headers).json()
    assert body["status"] == "ACCEPTED"
    assert sorted((o["asset_class_code"], o["action"], o["status"]) for o in body["stub_orders"]) == [
        ("DEBT", "BUY", "STUB_SUBMITTED"), ("EQUITY", "SELL", "STUB_SUBMITTED")]
    assert body["decision"]["actor_user_id"] and body["decision"]["decided_at"]
    assert client.get("/api/v1/me/holdings", headers=headers).json()["positions"] == before
    audit = db.execute("SELECT actor_user_id, created_at FROM audit_log WHERE action = 'REBALANCING_ACCEPTED'"
                       " AND entity_id = ?", (rec_id,)).fetchone()
    assert audit["actor_user_id"] == body["decision"]["actor_user_id"] and audit["created_at"]


@pytest.mark.ac("AC-07")
def test_dismiss_with_reason_is_audited(client, auth, db):
    """AC-07.4: dismiss with reason → DISMISSED, actor and timestamp audited."""
    headers = auth("customer.alpha")
    rec_id = _evaluate(client, headers)["rebalancing"]["recommendation_id"]
    body = client.post(f"/api/v1/me/rebalancing/{rec_id}/dismiss", json={"reason": "market too volatile"},
                       headers=headers).json()
    assert body["status"] == "DISMISSED"
    assert body["decision"]["reason"] == "market too volatile"
    assert db.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'REBALANCING_DISMISSED' AND entity_id = ?",
                      (rec_id,)).fetchone()[0] == 1


@pytest.mark.ac("AC-07")
def test_second_decision_and_foreign_access_are_rejected(client, auth):
    """AC-07.5: acting on a non-OPEN recommendation → 409; another customer's → 404."""
    headers = auth("customer.alpha")
    rec_id = _evaluate(client, headers)["rebalancing"]["recommendation_id"]
    assert client.post(f"/api/v1/me/rebalancing/{rec_id}/accept", headers=headers).status_code == 200
    again = client.post(f"/api/v1/me/rebalancing/{rec_id}/dismiss", json={}, headers=headers)
    assert (again.status_code, again.json()["error"]["code"]) == (409, "RECOMMENDATION_NOT_OPEN")
    foreign = client.post(f"/api/v1/me/rebalancing/{rec_id}/accept", headers=auth("customer.beta"))
    assert foreign.status_code == 404


@pytest.mark.ac("AC-07")
def test_decisions_are_append_only(client, auth, db):
    """AC-07 / NFR-02: decision rows cannot be updated or deleted."""
    headers = auth("customer.alpha")
    rec_id = _evaluate(client, headers)["rebalancing"]["recommendation_id"]
    client.post(f"/api/v1/me/rebalancing/{rec_id}/accept", headers=headers)
    with pytest.raises(Exception, match="append-only"):
        db.execute("UPDATE rebalancing_decisions SET status = 'DISMISSED' WHERE rebalancing_id = ?", (rec_id,))


def test_evaluate_requires_recommendation_and_kyc(client, auth):
    beta = client.post("/api/v1/me/rebalancing/evaluate", headers=auth("customer.beta"))
    assert (beta.status_code, beta.json()["error"]["code"]) == (409, "RECOMMENDATION_REQUIRED")
    assert client.post("/api/v1/me/rebalancing/evaluate", headers=auth("customer.gamma")).status_code == 403
