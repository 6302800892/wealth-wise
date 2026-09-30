"""BR-08: goal horizon buckets from whole months between the business date and the target date."""

from datetime import date

from src.types.enums import HorizonBucket

SHORT_BELOW_MONTHS = 36
LONG_ABOVE_MONTHS = 84


def months_between(as_of: date, target: date) -> int:
    months = (target.year - as_of.year) * 12 + (target.month - as_of.month)
    if target.day < as_of.day:
        months -= 1
    return months


def horizon_bucket(as_of: date, target: date) -> HorizonBucket:
    months = months_between(as_of, target)
    if months < SHORT_BELOW_MONTHS:
        return HorizonBucket.SHORT
    if months <= LONG_ABOVE_MONTHS:
        return HorizonBucket.MEDIUM
    return HorizonBucket.LONG
