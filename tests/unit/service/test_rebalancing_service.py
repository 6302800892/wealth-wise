"""AC-06 / AC-08: configurable threshold, refresh-driven evaluation and goal snapshots (service level)."""

import dataclasses
from decimal import Decimal

import pytest

from src.service import goal_progress_service, nav_service, rebalancing_service
from src.service.context import open_context


def _customer_id(db, username):
    return db.execute("SELECT customer_id FROM users WHERE username = ?", (username,)).fetchone()[0]


@pytest.mark.ac("AC-06")
def test_higher_threshold_suppresses_recommendation(settings, clock, db):
    """AC-06.3: E1 (max drift 10.00) with threshold 12.00 → nothing created."""
    strict = dataclasses.replace(settings, drift_threshold_pct=Decimal("12.00"))
    with open_context(strict, clock) as ctx:
        result = rebalancing_service.evaluate(ctx, _customer_id(db, "customer.alpha"))
    assert result["triggered"] is False
    assert result["threshold_pct"] == "12.00"


@pytest.mark.ac("AC-06")
def test_nav_refresh_evaluates_every_eligible_customer(settings, clock, db):
    """AC-06.5: a refresh cycle evaluates each KYC-verified customer with holdings and a recommendation."""
    with open_context(settings, clock) as ctx:
        summary = nav_service.run_refresh_cycle(ctx)
    assert summary["rebalancing_evaluated"] == 1  # only alpha is eligible in the seed
    assert summary["rebalancing_created"] == 1
    alpha = _customer_id(db, "customer.alpha")
    assert db.execute("SELECT COUNT(*) FROM rebalancing_recommendations WHERE customer_id = ?",
                      (alpha,)).fetchone()[0] >= 1


@pytest.mark.ac("AC-08")
def test_nav_refresh_snapshots_goal_progress_once_per_day(settings, clock, db):
    """AC-08.2 / AC-08.3: each refresh snapshots every active goal once for its nav_date."""
    with open_context(settings, clock) as ctx:
        summary = nav_service.run_refresh_cycle(ctx)
        repeated = goal_progress_service.snapshot_all(ctx, summary["nav_date"])
    assert summary["goal_snapshots"] == 2  # alpha's two goals
    assert repeated == 0
    rows = db.execute("SELECT COUNT(*) FROM goal_progress_snapshots WHERE nav_date = ?",
                      (summary["nav_date"],)).fetchone()[0]
    assert rows == 2


def test_kyc_unverified_customer_cannot_evaluate(settings, clock, db):
    with open_context(settings, clock) as ctx, pytest.raises(Exception) as exc:
        rebalancing_service.evaluate(ctx, _customer_id(db, "customer.gamma"))
    assert getattr(exc.value, "code", None) == "KYC_NOT_VERIFIED"
