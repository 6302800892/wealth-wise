"""NFR-08 / AC-09: a risk-band reassignment by override cannot exist without its override audit record."""

import pytest


def _ids(db):
    customer = db.execute("SELECT id FROM customers LIMIT 1").fetchone()[0]
    user = db.execute("SELECT id FROM users WHERE role = 'ADVISOR'").fetchone()[0]
    return customer, user


@pytest.mark.ac("AC-09")
def test_override_assignment_without_override_record_is_rejected(db):
    """AC-09: ADVISOR_OVERRIDE assignment with NULL override_id violates the table CHECK."""
    customer, user = _ids(db)
    with pytest.raises(Exception, match="CHECK"):
        db.execute(
            "INSERT INTO risk_band_assignments (id, customer_id, risk_band, source, assessment_id, override_id,"
            " rule_set_version, assigned_by, assigned_at) VALUES ('x1', ?, 'AGGRESSIVE', 'ADVISOR_OVERRIDE',"
            " NULL, NULL, NULL, ?, '2026-09-30T00:00:00Z')", (customer, user))


@pytest.mark.ac("AC-09")
def test_override_assignment_with_dangling_override_id_is_rejected(db):
    """AC-09: override_id must reference an existing risk_band_overrides row (foreign key)."""
    customer, user = _ids(db)
    with pytest.raises(Exception, match="FOREIGN KEY"):
        db.execute(
            "INSERT INTO risk_band_assignments (id, customer_id, risk_band, source, assessment_id, override_id,"
            " rule_set_version, assigned_by, assigned_at) VALUES ('x2', ?, 'AGGRESSIVE', 'ADVISOR_OVERRIDE',"
            " NULL, 'missing', NULL, ?, '2026-09-30T00:00:00Z')", (customer, user))


def test_questionnaire_assignment_requires_assessment(db):
    customer, user = _ids(db)
    with pytest.raises(Exception, match="CHECK"):
        db.execute(
            "INSERT INTO risk_band_assignments (id, customer_id, risk_band, source, assessment_id, override_id,"
            " rule_set_version, assigned_by, assigned_at) VALUES ('x3', ?, 'MODERATE', 'QUESTIONNAIRE',"
            " NULL, NULL, 1, ?, '2026-09-30T00:00:00Z')", (customer, user))


def test_every_override_assignment_in_db_links_to_an_override(client, auth, db):
    customer_id = client.get("/api/v1/auth/me", headers=auth("customer.alpha")).json()["customer_id"]
    client.post(f"/api/v1/advisor/customers/{customer_id}/risk-band-overrides",
                json={"new_band": "AGGRESSIVE", "reason_code": "ADVISOR_ASSESSMENT", "note": "reviewed"},
                headers=auth("advisor.one"))
    orphans = db.execute(
        "SELECT COUNT(*) FROM risk_band_assignments a LEFT JOIN risk_band_overrides o ON o.id = a.override_id"
        " WHERE a.source = 'ADVISOR_OVERRIDE' AND o.id IS NULL").fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM risk_band_assignments WHERE source = 'ADVISOR_OVERRIDE'").fetchone()[0]
    assert (orphans, total) == (0, 1)
