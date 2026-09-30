"""NFR-01: fixed-point helpers never use floating point."""

from decimal import Decimal

import pytest

from src.types.errors import WealthWiseError
from src.types.fixed_point import (
    MONEY_PLACES,
    UNITS_PLACES,
    from_scaled_int,
    parse_fixed,
    to_scaled_int,
    to_wire,
)


def test_money_round_trips_through_scaled_integer():
    assert to_scaled_int(Decimal("600000.00"), MONEY_PLACES) == 60_000_000
    assert from_scaled_int(60_000_000, MONEY_PLACES) == Decimal("600000.00")


def test_units_keep_four_decimal_places():
    assert to_scaled_int(Decimal("666.6666"), UNITS_PLACES) == 6_666_666
    assert to_wire(from_scaled_int(6_666_666, UNITS_PLACES)) == "666.6666"


def test_zero_is_rendered_with_scale():
    assert to_wire(from_scaled_int(0, MONEY_PLACES)) == "0.00"


def test_parse_fixed_accepts_strings_within_scale():
    assert parse_fixed("2000000.5", MONEY_PLACES, "target_amount") == Decimal("2000000.50")


@pytest.mark.parametrize("raw", ["1.234", "abc", "", "1e5", " 12", "--1"])
def test_parse_fixed_rejects_bad_text(raw):
    with pytest.raises(WealthWiseError) as exc:
        parse_fixed(raw, MONEY_PLACES, "target_amount")
    assert exc.value.code == "VALIDATION_FAILED"


@pytest.mark.parametrize("raw", [12.5, 12, True, None])
def test_parse_fixed_rejects_non_strings(raw):
    with pytest.raises(WealthWiseError):
        parse_fixed(raw, MONEY_PLACES, "target_amount")


def test_to_scaled_int_rejects_excess_precision():
    with pytest.raises(WealthWiseError):
        to_scaled_int(Decimal("1.001"), MONEY_PLACES)
