"""Wire representation of rebalancing proposals (all quantities as decimal strings, NFR-01)."""

from typing import Any

from src.repository.rebalancing_repo import RebalancingRecord
from src.types.fixed_point import to_wire


def rebalancing_view(record: RebalancingRecord) -> dict[str, Any]:
    decision = record.decision
    return {
        "recommendation_id": record.id,
        "portfolio_recommendation_id": record.portfolio_recommendation_id,
        "status": record.status.value,
        "nav_date": record.nav_date,
        "template_version": record.template_version,
        "threshold_pct": to_wire(record.threshold_pct),
        "max_drift_pct": to_wire(record.max_drift_pct),
        "total_value": to_wire(record.total_value),
        "created_at": record.created_at,
        "lines": [
            {"asset_class_code": ln.asset_class_code, "current_pct": to_wire(ln.current_pct),
             "target_pct": to_wire(ln.target_pct), "drift_pct": to_wire(ln.drift_pct), "action": ln.action.value,
             "units": to_wire(ln.units), "trade_value": to_wire(ln.trade_value)}
            for ln in record.lines
        ],
        "decision": None if decision is None else {
            "status": decision.status.value, "reason": decision.reason,
            "actor_user_id": decision.actor_user_id, "decided_at": decision.decided_at,
        },
        "stub_orders": [
            {"order_id": o.id, "asset_class_code": o.asset_class_code, "action": o.action.value,
             "units": to_wire(o.units), "status": o.status.value, "created_at": o.created_at}
            for o in record.orders
        ],
    }
