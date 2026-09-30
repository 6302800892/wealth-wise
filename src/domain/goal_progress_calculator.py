"""BR-19: percent_complete = current_goal_value / target_amount × 100 (not capped)."""

from collections.abc import Iterable, Mapping
from decimal import Decimal

from src.domain.drift_calculator import position_value
from src.types.enums import GoalStatus
from src.types.errors import WealthWiseError
from src.types.fixed_point import HUNDRED, PERCENT_PLACES, ZERO_MONEY, quantize_half_even


def goal_value(positions: Iterable[tuple[str, Decimal]], navs: Mapping[str, Decimal]) -> Decimal:
    """Sum the value of the holdings tagged to one goal."""
    total = ZERO_MONEY
    for code, units in positions:
        if units == 0:
            continue
        if code not in navs:
            raise WealthWiseError("NAV_UNAVAILABLE", f"no NAV available for asset class {code}")
        total += position_value(units, navs[code])
    return total


def percent_complete(current_value: Decimal, target_amount: Decimal) -> Decimal:
    return quantize_half_even(current_value * HUNDRED / target_amount, PERCENT_PLACES)


def goal_status(percent: Decimal) -> GoalStatus:
    return GoalStatus.ACHIEVED if percent >= HUNDRED else GoalStatus.IN_PROGRESS
