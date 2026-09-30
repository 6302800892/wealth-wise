"""AC-07: BUY/SELL/HOLD proposal quantities (BR-16) and decision preconditions (BR-18)."""

from decimal import Decimal

import pytest

from src.domain.drift_calculator import compute_drift
from src.domain.rebalancing_proposer import clean_dismiss_reason, ensure_open, propose
from src.types.enums import RebalancingStatus, TradeAction
from src.types.errors import WealthWiseError
from tests.unit.domain.test_drift_calculator import NAVS, ORDER, TARGET_E1, UNITS_E1


def _lines(units, targets=TARGET_E1, navs=NAVS):
    return {line.asset_class_code: line for line in propose(compute_drift(units, navs, targets, ORDER), navs)}


@pytest.mark.ac("AC-07")
def test_portfolio_e1_proposal():
    """AC-07.1: E1 → EQUITY SELL 666.6666 · DEBT BUY 4000.0000 · GOLD HOLD · CASH HOLD."""
    lines = _lines(UNITS_E1)
    assert (lines["EQUITY"].action, lines["EQUITY"].units) == (TradeAction.SELL, Decimal("666.6666"))
    assert (lines["DEBT"].action, lines["DEBT"].units) == (TradeAction.BUY, Decimal("4000.0000"))
    assert (lines["GOLD"].action, lines["GOLD"].units) == (TradeAction.HOLD, Decimal("0.0000"))
    assert (lines["CASH"].action, lines["CASH"].units) == (TradeAction.HOLD, Decimal("0.0000"))
    assert lines["DEBT"].trade_value == Decimal("100000.00")
    assert lines["EQUITY"].drift_pct == Decimal("10.00")


@pytest.mark.ac("AC-07")
def test_units_round_down_to_four_places():
    """AC-07.1 / BR-16: trade units are truncated (ROUND_DOWN) so a proposal never overspends."""
    assert _lines(UNITS_E1)["EQUITY"].units == Decimal("666.6666")


@pytest.mark.ac("AC-07")
def test_sell_is_capped_at_units_held():
    """AC-07.2: an asset class absent from the target is sold, but never more than is held."""
    units = {"EQUITY": Decimal("3.0000"), "GOLD": Decimal("1.0000")}
    navs = {"EQUITY": Decimal("1.0000"), "GOLD": Decimal("1.0000")}
    lines = _lines(units, targets={"EQUITY": Decimal("100.00")}, navs=navs)
    assert (lines["GOLD"].action, lines["GOLD"].units) == (TradeAction.SELL, Decimal("1.0000"))
    assert lines["EQUITY"].action is TradeAction.BUY


def test_tiny_delta_below_one_unit_step_is_hold():
    units = {"EQUITY": Decimal("1.0000"), "DEBT": Decimal("1.0000")}
    navs = {"EQUITY": Decimal("100000.0000"), "DEBT": Decimal("100000.0000")}
    targets = {"EQUITY": Decimal("50.00"), "DEBT": Decimal("50.00")}
    assert all(line.action is TradeAction.HOLD for line in _lines(units, targets, navs).values())


@pytest.mark.ac("AC-07")
@pytest.mark.parametrize("status", [RebalancingStatus.ACCEPTED, RebalancingStatus.DISMISSED, RebalancingStatus.SUPERSEDED])
def test_only_open_recommendations_accept_decisions(status):
    """AC-07.5: accept/dismiss on a non-OPEN recommendation raises RECOMMENDATION_NOT_OPEN."""
    with pytest.raises(WealthWiseError) as exc:
        ensure_open(status)
    assert exc.value.code == "RECOMMENDATION_NOT_OPEN"


def test_open_passes():
    ensure_open(RebalancingStatus.OPEN)


@pytest.mark.ac("AC-07")
def test_dismiss_reason_is_optional_and_bounded():
    """AC-07.4: optional reason, max 500 characters, blank becomes None."""
    assert clean_dismiss_reason(None) is None
    assert clean_dismiss_reason("   ") is None
    assert clean_dismiss_reason(" not now ") == "not now"
    with pytest.raises(WealthWiseError):
        clean_dismiss_reason("x" * 501)
