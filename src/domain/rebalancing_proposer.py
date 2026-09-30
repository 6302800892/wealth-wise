"""BR-16 / BR-18: BUY/SELL/HOLD quantities that restore the target allocation, and decision rules."""

from collections.abc import Mapping
from decimal import ROUND_DOWN, Decimal

from src.domain.drift_calculator import position_value
from src.types.enums import DriftStatus, RebalancingStatus, TradeAction
from src.types.errors import WealthWiseError, validation_error
from src.types.fixed_point import HUNDRED, MONEY_PLACES, UNITS_QUANTUM, ZERO_MONEY, quantize_half_even
from src.types.portfolio import DriftLine, DriftReport, RebalanceLine

ZERO_UNITS = Decimal("0.0000")
MAX_DISMISS_REASON = 500


def _trade_units(delta: Decimal, nav: Decimal | None, held: Decimal) -> Decimal:
    if nav is None or delta == 0:
        return ZERO_UNITS
    units = (abs(delta) / nav).quantize(UNITS_QUANTUM, rounding=ROUND_DOWN)
    return min(units, held) if delta < 0 else units


def _propose_line(line: DriftLine, total: Decimal, navs: Mapping[str, Decimal]) -> RebalanceLine:
    target_value = quantize_half_even(total * line.target_pct / HUNDRED, MONEY_PLACES)
    delta = target_value - line.value
    nav = navs.get(line.asset_class_code)
    units = _trade_units(delta, nav, line.units)
    if units > 0 and delta > 0:
        action = TradeAction.BUY
    elif units > 0 and delta < 0:
        action = TradeAction.SELL
    else:
        action, units = TradeAction.HOLD, ZERO_UNITS
    trade_value = position_value(units, nav) if action is not TradeAction.HOLD else ZERO_MONEY
    return RebalanceLine(asset_class_code=line.asset_class_code, current_pct=line.current_pct,
                         target_pct=line.target_pct, drift_pct=line.drift_pct, action=action,
                         units=units, trade_value=trade_value)


def propose(report: DriftReport, navs: Mapping[str, Decimal]) -> list[RebalanceLine]:
    """One line per asset class: trade units = |target_value − value| / NAV, truncated to 4 dp."""
    if report.status is not DriftStatus.OK:
        raise WealthWiseError("NOT_REBALANCEABLE", f"drift cannot be rebalanced: {report.status.value}")
    return [_propose_line(line, report.total_value, navs) for line in report.lines]


def ensure_open(status: RebalancingStatus) -> None:
    if status is not RebalancingStatus.OPEN:
        raise WealthWiseError("RECOMMENDATION_NOT_OPEN", f"recommendation is {status.value}; only OPEN can change")


def clean_dismiss_reason(reason: str | None) -> str | None:
    if reason is None or not reason.strip():
        return None
    cleaned = reason.strip()
    if len(cleaned) > MAX_DISMISS_REASON:
        raise validation_error("reason", f"reason must be at most {MAX_DISMISS_REASON} characters")
    return cleaned
