"""AC-04: goal horizon buckets from months to target date (BR-08)."""

from datetime import date

import pytest

from src.domain.horizon_resolver import horizon_bucket, months_between
from src.types.enums import HorizonBucket

AS_OF = date(2026, 9, 30)


@pytest.mark.ac("AC-04")
@pytest.mark.parametrize(
    ("target", "months", "bucket"),
    [
        (date(2029, 9, 29), 35, HorizonBucket.SHORT),
        (date(2029, 9, 30), 36, HorizonBucket.MEDIUM),
        (date(2033, 9, 30), 84, HorizonBucket.MEDIUM),
        (date(2033, 10, 30), 85, HorizonBucket.LONG),
        (date(2036, 9, 30), 120, HorizonBucket.LONG),
    ],
)
def test_horizon_boundaries(target, months, bucket):
    """AC-04.2: 35 → SHORT, 36 → MEDIUM, 84 → MEDIUM, 85 → LONG."""
    assert months_between(AS_OF, target) == months
    assert horizon_bucket(AS_OF, target) is bucket


@pytest.mark.ac("AC-04")
def test_past_due_goal_is_short():
    """AC-04: a target date already passed resolves to SHORT."""
    assert months_between(AS_OF, date(2025, 1, 1)) < 0
    assert horizon_bucket(AS_OF, date(2025, 1, 1)) is HorizonBucket.SHORT


def test_same_month_later_day_counts_zero_months():
    assert months_between(date(2026, 9, 1), date(2026, 9, 30)) == 0
