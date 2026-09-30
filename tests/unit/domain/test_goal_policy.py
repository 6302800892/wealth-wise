"""AC-03: goal field validation (target amount, date, name)."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain.goal_policy import validate_goal
from src.types.errors import WealthWiseError

TODAY = date(2026, 9, 30)


@pytest.mark.ac("AC-03")
def test_valid_goal_passes_and_name_is_trimmed():
    """AC-03.1: a valid goal is accepted."""
    assert validate_goal("  Home down-payment ", Decimal("2000000.00"), date(2031, 6, 30), TODAY) == "Home down-payment"


@pytest.mark.ac("AC-03")
@pytest.mark.parametrize("amount", ["0.00", "-5.00", "1000000000.01"])
def test_target_amount_bounds(amount):
    """AC-03.3: target_amount must be > 0 and ≤ 1,000,000,000.00."""
    with pytest.raises(WealthWiseError) as exc:
        validate_goal("Goal", Decimal(amount), date(2031, 6, 30), TODAY)
    assert exc.value.details["field"] == "target_amount"


@pytest.mark.ac("AC-03")
@pytest.mark.parametrize("target", [date(2026, 9, 30), date(2026, 1, 1)])
def test_target_date_must_be_in_future(target):
    """AC-03.4: target_date on or before today is rejected."""
    with pytest.raises(WealthWiseError) as exc:
        validate_goal("Goal", Decimal("100.00"), target, TODAY)
    assert exc.value.details["field"] == "target_date"


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_name_length(name):
    with pytest.raises(WealthWiseError):
        validate_goal(name, Decimal("100.00"), date(2031, 6, 30), TODAY)


def test_maximum_amount_is_allowed():
    validate_goal("Goal", Decimal("1000000000.00"), date(2031, 6, 30), TODAY)
