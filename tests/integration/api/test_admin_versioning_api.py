"""AC-02 / AC-10: admin drafts, validation, publishing, immutability and the in-flight rule."""

import pytest

from tests.integration.api.helpers import answers_payload

TEMPLATES = "/api/v1/admin/allocation-templates"
RULE_SETS = "/api/v1/admin/risk-rule-sets"


def _draft_template(client, admin):
    response = client.post(TEMPLATES, headers=admin)
    assert response.status_code == 201, response.text
    return response.json()


def _with_row(draft, band, horizon, allocations):
    rows = [r for r in draft["rows"] if not (r["risk_band"] == band and r["horizon_bucket"] == horizon)]
    return {"rows": rows + [{"risk_band": band, "horizon_bucket": horizon, "allocations": allocations}]}


V2_MODERATE_MEDIUM = {"EQUITY": "55.00", "DEBT": "30.00", "GOLD": "10.00", "CASH": "5.00"}


@pytest.mark.ac("AC-10")
def test_publish_new_template_version(client, auth):
    """AC-10.1: publishing draft v2 makes it PUBLISHED and active with published_by/at recorded."""
    admin = auth("admin.one")
    draft = _draft_template(client, admin)
    assert (draft["version"], draft["status"]) == (2, "DRAFT")
    published = client.post(f"{TEMPLATES}/2/publish", headers=admin).json()
    assert published["status"] == "PUBLISHED" and published["published_by"] and published["published_at"]
    versions = client.get(TEMPLATES, headers=admin).json()
    assert versions["active_version"] == 2


@pytest.mark.ac("AC-02")
@pytest.mark.parametrize("cash", ["4.00", "5.01"])
def test_publish_rejects_rows_not_summing_to_100(client, auth, cash):
    """AC-02.2: a row summing to 99.00 or 100.01 → 422 ALLOCATION_SUM_INVALID; version stays DRAFT."""
    admin = auth("admin.one")
    draft = _draft_template(client, admin)
    bad = _with_row(draft, "MODERATE", "MEDIUM", {**V2_MODERATE_MEDIUM, "CASH": cash})
    assert client.put(f"{TEMPLATES}/2", json=bad, headers=admin).status_code == 200
    response = client.post(f"{TEMPLATES}/2/publish", headers=admin)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "ALLOCATION_SUM_INVALID")
    assert "MODERATE/MEDIUM" in response.json()["error"]["message"]
    assert client.get(f"{TEMPLATES}/2", headers=admin).json()["status"] == "DRAFT"


@pytest.mark.ac("AC-02")
@pytest.mark.parametrize("equity", ["-1.00", "100.01", 55.0])
def test_saving_out_of_range_percentage_is_rejected(client, auth, equity):
    """AC-02.3: negative, > 100.00 or non-string percentages → 422 VALIDATION_FAILED."""
    admin = auth("admin.one")
    draft = _draft_template(client, admin)
    bad = _with_row(draft, "MODERATE", "MEDIUM", {**V2_MODERATE_MEDIUM, "EQUITY": equity})
    response = client.put(f"{TEMPLATES}/2", json=bad, headers=admin)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")


@pytest.mark.ac("AC-10")
def test_published_version_cannot_be_edited(client, auth):
    """AC-10.2: PUT on published v1 → 409 VERSION_IMMUTABLE."""
    admin = auth("admin.one")
    v1 = client.get(f"{TEMPLATES}/1", headers=admin).json()
    response = client.put(f"{TEMPLATES}/1", json={"rows": v1["rows"]}, headers=admin)
    assert (response.status_code, response.json()["error"]["code"]) == (409, "VERSION_IMMUTABLE")
    assert client.put(f"{RULE_SETS}/1", json=client.get(f"{RULE_SETS}/1", headers=admin).json()["definition"],
                      headers=admin).status_code == 409


@pytest.mark.ac("AC-10")
def test_in_flight_customers_keep_their_version(client, auth):
    """AC-10.3: after v2 changes MODERATE/MEDIUM, alpha's drift still uses v1 until a new recommendation."""
    admin, alpha = auth("admin.one"), auth("customer.alpha")
    draft = _draft_template(client, admin)
    client.put(f"{TEMPLATES}/2", json=_with_row(draft, "MODERATE", "MEDIUM", V2_MODERATE_MEDIUM), headers=admin)
    assert client.post(f"{TEMPLATES}/2/publish", headers=admin).status_code == 200
    holdings = client.get("/api/v1/me/holdings", headers=alpha).json()
    assert holdings["template_version"] == 1
    assert {ln["asset_class_code"]: ln["target_pct"] for ln in holdings["lines"]}["EQUITY"] == "50.00"
    fresh = client.post("/api/v1/me/recommendations", json={}, headers=alpha)
    assert fresh.status_code == 201 and fresh.json()["template_version"] == 2
    after = client.get("/api/v1/me/holdings", headers=alpha).json()
    assert {ln["asset_class_code"]: ln["target_pct"] for ln in after["lines"]}["EQUITY"] == "55.00"


@pytest.mark.ac("AC-10")
def test_questionnaire_version_bump_rejects_stale_answers(client, auth):
    """AC-10.4: after rule set v2 is published, v1 answers → 409 RULE_SET_NOT_ACTIVE; v2 answers work."""
    admin = auth("admin.one")
    assert client.post(RULE_SETS, headers=admin).status_code == 201
    assert client.post(f"{RULE_SETS}/2/publish", headers=admin).status_code == 200
    beta = auth("customer.beta")
    stale = client.post("/api/v1/me/risk-assessments", json=answers_payload(3, 3, 3, 3, 3, 3), headers=beta)
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "RULE_SET_NOT_ACTIVE")
    fresh = client.post("/api/v1/me/risk-assessments", json=answers_payload(3, 3, 3, 3, 3, 3, version=2), headers=beta)
    assert fresh.status_code == 201


@pytest.mark.ac("AC-10")
def test_rule_set_with_overlapping_thresholds_stays_draft(client, auth):
    """AC-10.5: overlapping bands → 422 on publish, version remains DRAFT."""
    admin = auth("admin.one")
    definition = client.post(RULE_SETS, headers=admin).json()["definition"]
    definition["bands"][0]["max_score"] = 14
    assert client.put(f"{RULE_SETS}/2", json=definition, headers=admin).status_code == 200
    response = client.post(f"{RULE_SETS}/2/publish", headers=admin)
    assert response.status_code == 422
    assert client.get(f"{RULE_SETS}/2", headers=admin).json()["status"] == "DRAFT"


def test_only_one_draft_at_a_time(client, auth):
    admin = auth("admin.one")
    _draft_template(client, admin)
    second = client.post(TEMPLATES, headers=admin)
    assert (second.status_code, second.json()["error"]["code"]) == (409, "DRAFT_ALREADY_EXISTS")


def test_asset_class_master(client, auth):
    admin = auth("admin.one")
    created = client.post("/api/v1/admin/asset-classes", json={"code": "REIT", "name": "Real estate",
                                                               "display_order": 5}, headers=admin)
    assert created.status_code == 201
    updated = client.patch("/api/v1/admin/asset-classes/REIT", json={"is_active": False}, headers=admin)
    assert updated.json()["is_active"] is False
    in_use = client.patch("/api/v1/admin/asset-classes/EQUITY", json={"is_active": False}, headers=admin)
    assert (in_use.status_code, in_use.json()["error"]["code"]) == (409, "ASSET_CLASS_IN_USE")
    codes = [a["code"] for a in client.get("/api/v1/admin/asset-classes", headers=admin).json()["items"]]
    assert codes[:4] == ["EQUITY", "DEBT", "GOLD", "CASH"]
