"""AC-08: goal progress reporting and snapshots on each NAV refresh."""

import pytest


def _goal_by_name(client, headers, name):
    return next(g for g in client.get("/api/v1/me/goals", headers=headers).json()["items"] if g["name"] == name)


@pytest.mark.ac("AC-08")
def test_seeded_home_goal_progress(client, auth):
    """AC-08.1: alpha's home goal (EQUITY 2000 u + DEBT 8000 u, target 2,000,000.00) is 25.00% complete."""
    headers = auth("customer.alpha")
    goal = _goal_by_name(client, headers, "Home down-payment")
    body = client.get(f"/api/v1/me/goals/{goal['goal_id']}/progress", headers=headers).json()
    assert body["current_value"] == "500000.00"
    assert body["percent_complete"] == "25.00"
    assert body["status"] == "IN_PROGRESS"


@pytest.mark.ac("AC-08")
def test_nav_refresh_updates_progress_and_records_snapshot(client, auth):
    """AC-08.2: after refresh EQUITY = 153.0000 → 506,000.00 and 25.30%, with a snapshot for that nav_date."""
    headers = auth("customer.alpha")
    goal = _goal_by_name(client, headers, "Home down-payment")
    refreshed = client.post("/api/v1/admin/nav/refresh", headers=auth("admin.one")).json()
    assert refreshed["nav_date"] == "2026-10-01"
    body = client.get(f"/api/v1/me/goals/{goal['goal_id']}/progress", headers=headers).json()
    assert body["nav_date"] == "2026-10-01"
    assert body["current_value"] == "506080.00"  # DEBT also moved to 25.0100 in the seed feed
    assert body["percent_complete"] == "25.30"
    assert [s["nav_date"] for s in body["history"]] == ["2026-10-01"]


@pytest.mark.ac("AC-08")
def test_progress_history_has_one_snapshot_per_refresh(client, auth):
    """AC-08.3: two refreshes → two snapshots (one per nav_date)."""
    admin = auth("admin.one")
    client.post("/api/v1/admin/nav/refresh", headers=admin)
    client.post("/api/v1/admin/nav/refresh", headers=admin)
    headers = auth("customer.alpha")
    goal = _goal_by_name(client, headers, "Retirement")
    history = client.get(f"/api/v1/me/goals/{goal['goal_id']}/progress", headers=headers).json()["history"]
    assert [s["nav_date"] for s in history] == ["2026-10-02", "2026-10-01"]


def test_progress_for_foreign_goal_is_not_found(client, auth):
    goal = _goal_by_name(client, auth("customer.alpha"), "Retirement")
    assert client.get(f"/api/v1/me/goals/{goal['goal_id']}/progress", headers=auth("customer.beta")).status_code == 404
