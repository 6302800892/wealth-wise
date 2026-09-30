"""AC-05 / AC-06: valuation, current allocation and drift in fixed point (BR-12 – BR-15)."""

from decimal import Decimal

import pytest

from src.domain.drift_calculator import compute_drift, exceeds_threshold, position_value
from src.types.enums import DriftStatus
from src.types.errors import WealthWiseError

ORDER = ["EQUITY", "DEBT", "GOLD", "CASH"]
NAVS = {"EQUITY": Decimal("150.0000"), "DEBT": Decimal("25.0000"), "GOLD": Decimal("50.0000"), "CASH": Decimal("1.0000")}
TARGET_E1 = {"EQUITY": Decimal("50.00"), "DEBT": Decimal("35.00"), "GOLD": Decimal("10.00"), "CASH": Decimal("5.00")}
UNITS_E1 = {"EQUITY": Decimal("4000.0000"), "DEBT": Decimal("10000.0000"), "GOLD": Decimal("2000.0000"),
            "CASH": Decimal("50000.0000")}


def _by_code(report):
    return {line.asset_class_code: line for line in report.lines}


@pytest.mark.ac("AC-05")
def test_portfolio_e1_values_and_total():
    """AC-05.1: E1 values 600,000 / 250,000 / 100,000 / 50,000, total 1,000,000.00."""
    report = compute_drift(UNITS_E1, NAVS, TARGET_E1, ORDER)
    lines = _by_code(report)
    assert [lines[c].value for c in ORDER] == [Decimal("600000.00"), Decimal("250000.00"),
                                              Decimal("100000.00"), Decimal("50000.00")]
    assert report.total_value == Decimal("1000000.00")


@pytest.mark.ac("AC-05")
def test_portfolio_e1_current_pct_and_drift():
    """AC-05.2: current% 60/25/10/5 and drift 10/10/0/0."""
    report = compute_drift(UNITS_E1, NAVS, TARGET_E1, ORDER)
    lines = _by_code(report)
    assert [lines[c].current_pct for c in ORDER] == [Decimal("60.00"), Decimal("25.00"), Decimal("10.00"), Decimal("5.00")]
    assert [lines[c].drift_pct for c in ORDER] == [Decimal("10.00"), Decimal("10.00"), Decimal("0.00"), Decimal("0.00")]
    assert report.max_drift_pct == Decimal("10.00")
    assert report.status is DriftStatus.OK


@pytest.mark.ac("AC-05")
def test_rounding_is_half_even_on_decimal():
    """AC-05.3: one-third shares quantise to 33.33 / 66.67 using ROUND_HALF_EVEN, Decimal only."""
    units = {"EQUITY": Decimal("1.0000"), "DEBT": Decimal("2.0000")}
    navs = {"EQUITY": Decimal("1.0000"), "DEBT": Decimal("1.0000")}
    report = compute_drift(units, navs, {"EQUITY": Decimal("50.00"), "DEBT": Decimal("50.00")}, ORDER)
    lines = _by_code(report)
    assert lines["EQUITY"].current_pct == Decimal("33.33")
    assert lines["DEBT"].current_pct == Decimal("66.67")
    assert all(isinstance(line.current_pct, Decimal) for line in report.lines)


def test_position_value_rounds_half_even():
    assert position_value(Decimal("0.0005"), Decimal("10.0000")) == Decimal("0.00")
    assert position_value(Decimal("0.0015"), Decimal("10.0000")) == Decimal("0.02")


@pytest.mark.ac("AC-05")
def test_no_holdings_reports_no_drift():
    """AC-05.4: zero total → total 0.00, drift None, status NO_HOLDINGS."""
    report = compute_drift({}, NAVS, TARGET_E1, ORDER)
    assert report.total_value == Decimal("0.00")
    assert report.max_drift_pct is None
    assert report.status is DriftStatus.NO_HOLDINGS
    assert all(line.drift_pct is None for line in report.lines)


@pytest.mark.ac("AC-05")
def test_held_class_missing_from_target_has_zero_target():
    """AC-05 / BR-14: a held asset class absent from the target counts as target 0.00."""
    report = compute_drift({"EQUITY": Decimal("1.0000"), "GOLD": Decimal("1.0000")},
                           {"EQUITY": Decimal("1.0000"), "GOLD": Decimal("1.0000")},
                           {"EQUITY": Decimal("100.00")}, ORDER)
    gold = _by_code(report)["GOLD"]
    assert gold.target_pct == Decimal("0.00")
    assert gold.drift_pct == Decimal("50.00")


def test_without_target_status_is_no_recommendation():
    report = compute_drift(UNITS_E1, NAVS, None, ORDER)
    assert report.status is DriftStatus.NO_RECOMMENDATION
    assert _by_code(report)["EQUITY"].current_pct == Decimal("60.00")
    assert report.max_drift_pct is None


def test_missing_nav_for_held_class_is_an_error():
    with pytest.raises(WealthWiseError) as exc:
        compute_drift({"EQUITY": Decimal("1.0000")}, {}, TARGET_E1, ORDER)
    assert exc.value.code == "NAV_UNAVAILABLE"


@pytest.mark.ac("AC-06")
@pytest.mark.parametrize(("max_drift", "threshold", "expected"), [
    (Decimal("5.00"), Decimal("5.00"), False),
    (Decimal("5.01"), Decimal("5.00"), True),
    (Decimal("10.00"), Decimal("12.00"), False),
    (None, Decimal("5.00"), False),
])
def test_threshold_is_strictly_greater_than(max_drift, threshold, expected):
    """AC-06.2 / AC-06.3: trigger only when max drift is strictly above the threshold."""
    assert exceeds_threshold(max_drift, threshold) is expected
