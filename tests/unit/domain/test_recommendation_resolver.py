"""AC-04: primary goal selection, allocation resolution and deterministic fingerprints (BR-10, BR-11)."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain.recommendation_resolver import input_fingerprint, resolve_allocation, select_primary_goal
from src.types.enums import GoalPriority, HorizonBucket, RiskBand
from src.types.errors import WealthWiseError
from src.types.goals import GoalRef
from tests.factories import template_set_v1


def _goal(goal_id, priority, target, created="2026-01-01T00:00:00Z"):
    return GoalRef(id=goal_id, priority=priority, target_date=target, created_at=created)


@pytest.mark.ac("AC-04")
def test_moderate_long_resolves_to_template_row():
    """AC-04.1: MODERATE + LONG → EQUITY 60 · DEBT 27 · GOLD 10 · CASH 3."""
    allocation = resolve_allocation(template_set_v1(), RiskBand.MODERATE, HorizonBucket.LONG)
    assert allocation == {"EQUITY": Decimal("60.00"), "DEBT": Decimal("27.00"),
                          "GOLD": Decimal("10.00"), "CASH": Decimal("3.00")}
    assert sum(allocation.values()) == Decimal("100.00")


@pytest.mark.ac("AC-04")
def test_high_priority_goal_is_primary_even_if_later():
    """AC-04.3: a HIGH goal in 2040 beats a MEDIUM goal in 2028."""
    goals = [_goal("medium", GoalPriority.MEDIUM, date(2028, 1, 1)), _goal("high", GoalPriority.HIGH, date(2040, 1, 1))]
    assert select_primary_goal(goals).id == "high"


@pytest.mark.ac("AC-04")
def test_ties_break_by_target_date_then_created_at_then_id():
    """AC-04.3: tie-breakers are earliest target_date, then created_at, then id."""
    goals = [
        _goal("b", GoalPriority.HIGH, date(2030, 1, 1), "2026-01-02T00:00:00Z"),
        _goal("c", GoalPriority.HIGH, date(2030, 1, 1), "2026-01-01T00:00:00Z"),
        _goal("a", GoalPriority.HIGH, date(2030, 1, 1), "2026-01-01T00:00:00Z"),
        _goal("z", GoalPriority.HIGH, date(2031, 1, 1), "2025-01-01T00:00:00Z"),
    ]
    assert select_primary_goal(goals).id == "a"


def test_no_goals_means_no_primary():
    assert select_primary_goal([]) is None


@pytest.mark.ac("AC-04")
def test_fingerprint_is_deterministic_and_input_sensitive():
    """AC-04.4: identical inputs give identical fingerprints; any change alters it."""
    first = input_fingerprint(RiskBand.MODERATE, HorizonBucket.LONG, 1, "g1")
    assert first == input_fingerprint(RiskBand.MODERATE, HorizonBucket.LONG, 1, "g1")
    assert len(first) == 64
    assert first != input_fingerprint(RiskBand.MODERATE, HorizonBucket.LONG, 2, "g1")
    assert first != input_fingerprint(RiskBand.AGGRESSIVE, HorizonBucket.LONG, 1, "g1")


def test_missing_template_row_is_an_error():
    template = template_set_v1()
    rows = dict(template.rows)
    del rows[(RiskBand.MODERATE, HorizonBucket.LONG)]
    with pytest.raises(WealthWiseError):
        resolve_allocation(type(template)(version=1, rows=rows), RiskBand.MODERATE, HorizonBucket.LONG)
