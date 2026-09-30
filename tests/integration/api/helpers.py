"""Shared helpers for API integration tests."""

from tests.factories import answers_for_scores


def answers_payload(*scores: int, version: int = 1) -> dict:
    return {
        "rule_set_version": version,
        "answers": [{"question_id": q, "option_id": o} for q, o in answers_for_scores(*scores)],
    }


def goal_payload(name="Home", goal_type="HOME", amount="2000000.00", target="2031-06-30", priority="HIGH") -> dict:
    return {"name": name, "goal_type": goal_type, "target_amount": amount, "target_date": target, "priority": priority}


def profile_customer(client, headers, scores=(3, 3, 3, 3, 2, 2)):
    response = client.post("/api/v1/me/risk-assessments", json=answers_payload(*scores), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_goal(client, headers, **fields):
    response = client.post("/api/v1/me/goals", json=goal_payload(**fields), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()
