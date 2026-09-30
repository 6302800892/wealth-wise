"""AC-09: advisor workbench — portfolio view, audited risk-band override, manual recommendations."""

import pytest

from tests.integration.api.helpers import create_goal, profile_customer


def _customer_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["customer_id"]


def _override(client, auth, customer_id, **fields):
    payload = {"new_band": "CONSERVATIVE", "reason_code": "CHANGE_IN_CIRCUMSTANCES", "note": "Client lost job", **fields}
    return client.post(f"/api/v1/advisor/customers/{customer_id}/risk-band-overrides", json=payload,
                       headers=auth("advisor.one"))


@pytest.mark.ac("AC-09")
def test_override_changes_effective_band_and_is_audited(client, auth, db):
    """AC-09.1: 201; effective band CONSERVATIVE via ADVISOR_OVERRIDE; override stores full audit fields."""
    alpha = auth("customer.alpha")
    customer_id = _customer_id(client, alpha)
    response = _override(client, auth, customer_id)
    assert response.status_code == 201
    body = response.json()
    assert (body["previous_band"], body["new_band"]) == ("MODERATE", "CONSERVATIVE")
    assert body["reason_code"] == "CHANGE_IN_CIRCUMSTANCES"
    assert body["actor_user_id"] and body["created_at"] and body["note"] == "Client lost job"
    profile = client.get("/api/v1/me/risk-profile", headers=alpha).json()
    assert (profile["risk_band"], profile["source"]) == ("CONSERVATIVE", "ADVISOR_OVERRIDE")
    assert db.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'RISK_BAND_OVERRIDDEN' AND entity_id = ?",
                      (customer_id,)).fetchone()[0] == 1


@pytest.mark.ac("AC-09")
@pytest.mark.parametrize(("fields", "code"), [({"note": "   "}, "VALIDATION_FAILED"),
                                              ({"note": "x" * 1001}, "VALIDATION_FAILED"),
                                              ({"reason_code": "WHIM"}, "VALIDATION_FAILED"),
                                              ({"new_band": "MODERATE"}, "BAND_UNCHANGED")])
def test_invalid_overrides_return_422(client, auth, fields, code):
    """AC-09.2: blank / long note, unknown reason → 422; same band → 422 BAND_UNCHANGED."""
    response = _override(client, auth, _customer_id(client, auth("customer.alpha")), **fields)
    assert (response.status_code, response.json()["error"]["code"]) == (422, code)


@pytest.mark.ac("AC-09")
def test_customer_and_admin_cannot_override(client, auth):
    """AC-09.3: CUSTOMER and ADMIN tokens get 403."""
    customer_id = _customer_id(client, auth("customer.alpha"))
    for username in ["customer.alpha", "admin.one"]:
        response = client.post(f"/api/v1/advisor/customers/{customer_id}/risk-band-overrides",
                               json={"new_band": "AGGRESSIVE", "reason_code": "ADVISOR_ASSESSMENT", "note": "n"},
                               headers=auth(username))
        assert response.status_code == 403


@pytest.mark.ac("AC-09")
def test_next_recommendation_uses_overridden_band(client, auth):
    """AC-09.4: after an override the customer's next recommendation uses the new band."""
    beta = auth("customer.beta")
    profile_customer(client, beta)
    create_goal(client, beta, target="2031-06-30")
    assert client.post("/api/v1/me/recommendations", json={}, headers=beta).json()["risk_band"] == "MODERATE"
    _override(client, auth, _customer_id(client, beta), new_band="AGGRESSIVE", reason_code="ADVISOR_ASSESSMENT")
    body = client.post("/api/v1/me/recommendations", json={}, headers=beta).json()
    assert body["risk_band"] == "AGGRESSIVE"
    assert {a["asset_class_code"]: a["target_pct"] for a in body["allocation"]}["EQUITY"] == "70.00"


@pytest.mark.ac("AC-09")
def test_audit_history_newest_first_and_note_hidden_from_customer(client, auth):
    """AC-09.5: advisor sees all overrides newest first; the customer never sees the advisor note."""
    alpha = auth("customer.alpha")
    customer_id = _customer_id(client, alpha)
    _override(client, auth, customer_id, new_band="CONSERVATIVE", note="first")
    _override(client, auth, customer_id, new_band="AGGRESSIVE", reason_code="CUSTOMER_REQUEST", note="second")
    history = client.get(f"/api/v1/advisor/customers/{customer_id}/audit", headers=auth("advisor.one")).json()
    assert [o["note"] for o in history["overrides"]] == ["second", "first"]
    assert "note" not in client.get("/api/v1/me/risk-profile", headers=alpha).text


def test_advisor_portfolio_view_and_customer_list(client, auth):
    advisor = auth("advisor.one")
    customers = client.get("/api/v1/advisor/customers", headers=advisor).json()["items"]
    alpha = next(c for c in customers if c["display_name"] == "Aarav Alpha")
    assert alpha["risk_band"] == "MODERATE" and alpha["open_rebalancing"] == 1
    portfolio = client.get(f"/api/v1/advisor/customers/{alpha['customer_id']}/portfolio", headers=advisor).json()
    assert portfolio["holdings"]["total_value"] == "1000000.00"
    assert portfolio["recommendation"]["risk_band"] == "MODERATE"
    assert len(portfolio["goals"]) == 2


def test_manual_recommendation_is_logged(client, auth):
    customer_id = _customer_id(client, auth("customer.alpha"))
    response = client.post(f"/api/v1/advisor/customers/{customer_id}/manual-recommendations",
                           json={"note": "Consider topping up the emergency fund"}, headers=auth("advisor.one"))
    assert response.status_code == 201
    history = client.get(f"/api/v1/advisor/customers/{customer_id}/audit", headers=auth("advisor.one")).json()
    assert history["manual_recommendations"][0]["note"] == "Consider topping up the emergency fund"


def test_unknown_customer_is_not_found(client, auth):
    assert client.get("/api/v1/advisor/customers/nope/portfolio", headers=auth("advisor.one")).status_code == 404
