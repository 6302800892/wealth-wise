"""Fixed-point helpers (NFR-01, spec §7.3). All maths uses Decimal; storage uses scaled integers."""

import re
from decimal import ROUND_HALF_EVEN, Decimal

from src.types.errors import validation_error

MONEY_PLACES = 2
PERCENT_PLACES = 2
UNITS_PLACES = 4
NAV_PLACES = 4

MONEY_QUANTUM = Decimal("0.01")
PERCENT_QUANTUM = Decimal("0.01")
UNITS_QUANTUM = Decimal("0.0001")
NAV_QUANTUM = Decimal("0.0001")

HUNDRED = Decimal("100")
ZERO_MONEY = Decimal("0.00")

_NUMBER_TEXT = re.compile(r"^-?\d+(\.(\d+))?$")


def quantum(places: int) -> Decimal:
    return Decimal(1).scaleb(-places)


def quantize_half_even(value: Decimal, places: int) -> Decimal:
    return value.quantize(quantum(places), rounding=ROUND_HALF_EVEN)


def to_scaled_int(value: Decimal, places: int) -> int:
    """Convert a Decimal with at most `places` decimals into its scaled integer form."""
    exact = value.quantize(quantum(places))
    if exact != value:
        raise validation_error("value", f"value has more than {places} decimal places")
    return int(exact.scaleb(places))


def from_scaled_int(raw: int, places: int) -> Decimal:
    return Decimal(raw).scaleb(-places)


def to_wire(value: Decimal) -> str:
    """Render a Decimal as a plain JSON string (never scientific notation)."""
    return format(value, "f")


def to_wire_or_none(value: Decimal | None) -> str | None:
    return None if value is None else to_wire(value)


def parse_fixed(raw: object, places: int, field: str) -> Decimal:
    """Parse client input. Only strings are accepted, so JSON numbers (floats) never enter the system."""
    if not isinstance(raw, str):
        raise validation_error(field, f"{field} must be a decimal string, e.g. \"100.00\"")
    match = _NUMBER_TEXT.match(raw)
    if match is None:
        raise validation_error(field, f"{field} is not a valid decimal number")
    fraction = match.group(2) or ""
    if len(fraction) > places:
        raise validation_error(field, f"{field} allows at most {places} decimal places")
    return Decimal(raw).quantize(quantum(places))
