"""Portfolio valuation and rebalancing value objects."""

from dataclasses import dataclass
from decimal import Decimal

from src.types.enums import DriftStatus, TradeAction


@dataclass(frozen=True)
class DriftLine:
    asset_class_code: str
    units: Decimal
    nav: Decimal | None
    value: Decimal
    current_pct: Decimal | None
    target_pct: Decimal | None
    drift_pct: Decimal | None


@dataclass(frozen=True)
class DriftReport:
    total_value: Decimal
    lines: tuple[DriftLine, ...]
    max_drift_pct: Decimal | None
    status: DriftStatus


@dataclass(frozen=True)
class RebalanceLine:
    asset_class_code: str
    current_pct: Decimal
    target_pct: Decimal
    drift_pct: Decimal
    action: TradeAction
    units: Decimal
    trade_value: Decimal
