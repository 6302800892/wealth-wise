"""AC-08: goal progress = current_goal_value / target_amount (BR-19)."""

from decimal import Decimal

import pytest

from src.domain.goal_progress_calculator import goal_status, goal_value, percent_complete
from src.types.enums import GoalStatus

NAVS = {"EQUITY": Decimal("150.0000"), "DEBT": Decimal("25.0000")}


@pytest.mark.ac("AC-08")
def test_goal_value_and_percent_complete():
    """AC-08.1: EQUITY 2000 u @150 + DEBT 8000 u @25 = 500,000.00 → 25.00% of 2,000,000.00."""
    value = goal_value([("EQUITY", Decimal("2000.0000")), ("DEBT", Decimal("8000.0000"))], NAVS)
    assert value == Decimal("500000.00")
    assert percent_complete(value, Decimal("2000000.00")) == Decimal("25.00")


@pytest.mark.ac("AC-08")
def test_new_nav_changes_progress():
    """AC-08.2: EQUITY at 153.0000 → 506,000.00 → 25.30%."""
    navs = {**NAVS, "EQUITY": Decimal("153.0000")}
    value = goal_value([("EQUITY", Decimal("2000.0000")), ("DEBT", Decimal("8000.0000"))], navs)
    assert value == Decimal("506000.00")
    assert percent_complete(value, Decimal("2000000.00")) == Decimal("25.30")


@pytest.mark.ac("AC-08")
def test_goal_without_holdings_is_zero():
    """AC-08.4: no tagged holdings → 0.00%."""
    assert percent_complete(goal_value([], NAVS), Decimal("100.00")) == Decimal("0.00")
    assert goal_status(Decimal("0.00")) is GoalStatus.IN_PROGRESS


@pytest.mark.ac("AC-08")
def test_progress_above_target_is_not_capped_and_achieved():
    """AC-08.4: value above target reports > 100.00 and status ACHIEVED."""
    pct = percent_complete(Decimal("150.00"), Decimal("100.00"))
    assert pct == Decimal("150.00")
    assert goal_status(pct) is GoalStatus.ACHIEVED
    assert goal_status(Decimal("100.00")) is GoalStatus.ACHIEVED


def test_percent_complete_rounds_half_even():
    assert percent_complete(Decimal("1.00"), Decimal("3.00")) == Decimal("33.33")
