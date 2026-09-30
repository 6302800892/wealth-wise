"""BR-12 – BR-15: position valuation, current allocation and drift — Decimal fixed point only (NFR-01)."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from src.types.enums import DriftStatus
from src.types.errors import WealthWiseError
from src.types.fixed_point import (
    HUNDRED,
    MONEY_PLACES,
    PERCENT_PLACES,
    UNITS_QUANTUM,
    ZERO_MONEY,
    quantize_half_even,
)
from src.types.portfolio import DriftLine, DriftReport

ZERO_PCT = Decimal("0.00")


def position_value(units: Decimal, nav: Decimal) -> Decimal:
    return quantize_half_even(units * nav, MONEY_PLACES)


def _ordered_codes(held: Mapping[str, Decimal], targets: Mapping[str, Decimal] | None,
                   order: Sequence[str]) -> list[str]:
    codes = {code for code, units in held.items() if units > 0} | set(targets or {})
    known = [code for code in order if code in codes]
    return known + sorted(codes - set(known))


def _value_of(code: str, units: Decimal, navs: Mapping[str, Decimal]) -> Decimal:
    if units == 0:
        return ZERO_MONEY
    if code not in navs:
        raise WealthWiseError("NAV_UNAVAILABLE", f"no NAV available for asset class {code}")
    return position_value(units, navs[code])


def compute_drift(held: Mapping[str, Decimal], navs: Mapping[str, Decimal],
                  targets: Mapping[str, Decimal] | None, order: Sequence[str]) -> DriftReport:
    """Value each asset class and compare current% with target% (drift = |current − target|)."""
    codes = _ordered_codes(held, targets, order)
    units = {code: held.get(code, Decimal("0")).quantize(UNITS_QUANTUM) for code in codes}
    values = {code: _value_of(code, units[code], navs) for code in codes}
    total = sum(values.values(), ZERO_MONEY)
    if total == 0:
        status = DriftStatus.NO_HOLDINGS
    elif targets is None:
        status = DriftStatus.NO_RECOMMENDATION
    else:
        status = DriftStatus.OK
    lines = []
    for code in codes:
        current = quantize_half_even(values[code] * HUNDRED / total, PERCENT_PLACES) if total > 0 else None
        target = None if targets is None else targets.get(code, ZERO_PCT)
        drift = abs(current - target) if status is DriftStatus.OK else None
        lines.append(DriftLine(asset_class_code=code, units=units[code], nav=navs.get(code), value=values[code],
                               current_pct=current, target_pct=target, drift_pct=drift))
    drifts = [line.drift_pct for line in lines if line.drift_pct is not None]
    return DriftReport(total_value=total, lines=tuple(lines), max_drift_pct=max(drifts) if drifts else None,
                       status=status)


def exceeds_threshold(max_drift_pct: Decimal | None, threshold_pct: Decimal) -> bool:
    """BR-15: strictly greater than the configured threshold."""
    return max_drift_pct is not None and max_drift_pct > threshold_pct
