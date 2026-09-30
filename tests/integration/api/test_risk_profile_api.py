"""AC-01 / AC-10.4: questionnaire, assessment submission and risk-profile view over HTTP."""

import pytest

from src.repository.db import connect
from tests.integration.api.helpers import answers_payload


@pytest.mark.ac("AC-01")
def test_questionnaire_has_six_questions_with_five_options(client, auth):
    """AC-01.1: active rule set v1 exposes 6 questions × 5 options (scores hidden)."""
    body = client.get("/api/v1/questionnaire", headers=auth("customer.beta")).json()
    assert body["rule_set_version"] == 1
    assert len(body["questions"]) == 6
    for question in body["questions"]:
        assert len(question["options"]) == 5
        assert all("score" not in option for option in question["options"])


@pytest.mark.ac("AC-01")
def test_submission_assigns_band_and_persists_records(client, auth, settings):
    """AC-01.2: 3,3,3,3,2,2 → score 16, MODERATE, 201, one assessment + one QUESTIONNAIRE assignment."""
    headers = auth("customer.beta")
    response = client.post("/api/v1/me/risk-assessments", json=answers_payload(3, 3, 3, 3, 2, 2), headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["total_score"] == 16
    assert body["risk_band"] == "MODERATE"
    conn = connect(settings.db_path)
    customer_id = client.get("/api/v1/auth/me", headers=headers).json()["customer_id"]
    assessments = conn.execute("SELECT COUNT(*) FROM risk_assessments WHERE customer_id = ?", (customer_id,)).fetchone()[0]
    sources = conn.execute("SELECT source FROM risk_band_assignments WHERE customer_id = ?", (customer_id,)).fetchall()
    assert assessments == 1
    assert [row[0] for row in sources] == ["QUESTIONNAIRE"]


@pytest.mark.ac("AC-01")
def test_invalid_submission_returns_422_and_saves_nothing(client, auth, settings):
    """AC-01.4: a missing question yields 422 INVALID_ANSWERS and nothing is persisted."""
    headers = auth("customer.beta")
    payload = answers_payload(3, 3, 3, 3, 2, 2)
    payload["answers"].pop()
    response = client.post("/api/v1/me/risk-assessments", json=payload, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ANSWERS"
    customer_id = client.get("/api/v1/auth/me", headers=headers).json()["customer_id"]
    count = connect(settings.db_path).execute(
        "SELECT COUNT(*) FROM risk_assessments WHERE customer_id = ?", (customer_id,)).fetchone()[0]
    assert count == 0


@pytest.mark.ac("AC-01")
def test_customer_sees_assigned_band(client, auth):
    """AC-01.6: risk profile shows band, source, rule_set_version and assigned_at."""
    headers = auth("customer.beta")
    client.post("/api/v1/me/risk-assessments", json=answers_payload(5, 5, 5, 5, 5, 5), headers=headers)
    profile = client.get("/api/v1/me/risk-profile", headers=headers).json()
    assert profile["risk_band"] == "AGGRESSIVE"
    assert profile["source"] == "QUESTIONNAIRE"
    assert profile["rule_set_version"] == 1
    assert profile["assigned_at"]


def test_profile_without_assessment_is_empty(client, auth):
    profile = client.get("/api/v1/me/risk-profile", headers=auth("customer.beta")).json()
    assert profile["risk_band"] is None


@pytest.mark.ac("AC-10")
def test_submission_against_inactive_version_is_rejected(client, auth):
    """AC-10.4: answers for a version that is not active return 409 RULE_SET_NOT_ACTIVE."""
    response = client.post("/api/v1/me/risk-assessments", json=answers_payload(3, 3, 3, 3, 3, 3, version=99),
                           headers=auth("customer.beta"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RULE_SET_NOT_ACTIVE"
