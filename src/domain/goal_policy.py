"""Goal field rules (AC-03): positive bounded target amount, future target date, sensible name."""

from datetime import date
from decimal import Decimal

from src.types.errors import validation_error

MAX_TARGET_AMOUNT = Decimal("1000000000.00")
MAX_NAME_LENGTH = 100


def validate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > MAX_NAME_LENGTH:
        raise validation_error("name", f"name must be 1–{MAX_NAME_LENGTH} characters")
    return cleaned


def validate_target_amount(amount: Decimal) -> None:
    if amount <= 0 or amount > MAX_TARGET_AMOUNT:
        raise validation_error("target_amount", "target_amount must be > 0.00 and ≤ 1000000000.00")


def validate_target_date(target: date, today: date) -> None:
    if target <= today:
        raise validation_error("target_date", "target_date must be after today")


def validate_goal(name: str, target_amount: Decimal, target_date: date, today: date) -> str:
    """Validate a new goal and return the cleaned name."""
    cleaned = validate_name(name)
    validate_target_amount(target_amount)
    validate_target_date(target_date, today)
    return cleaned
