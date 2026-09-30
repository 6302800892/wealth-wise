"""Holdings and drift use cases (AC-05). Targets come from the customer's latest recommendation (BR-14)."""

import logging
from typing import Any

from src.domain.drift_calculator import compute_drift
from src.repository import asset_class_repo, goals_repo, holdings_repo, nav_repo, recommendation_repo
from src.repository.db import transaction
from src.repository.recommendation_repo import RecommendationRecord
from src.service.context import ServiceContext
from src.types.errors import not_found, validation_error
from src.types.fixed_point import UNITS_PLACES, parse_fixed, to_wire, to_wire_or_none
from src.types.portfolio import DriftReport

log = logging.getLogger(__name__)


def record_holding(ctx: ServiceContext, customer_id: str, *, asset_class_code: str, goal_id: str | None,
                   units: str) -> dict[str, Any]:
    quantity = parse_fixed(units, UNITS_PLACES, "units")
    if quantity < 0:
        raise validation_error("units", "units must be zero or positive")
    asset_class = asset_class_repo.find_asset_class(ctx.conn, asset_class_code)
    if asset_class is None or not asset_class.is_active:
        raise not_found("asset class")
    if goal_id is not None and goals_repo.find_goal(ctx.conn, customer_id, goal_id) is None:
        raise not_found("goal")
    with transaction(ctx.conn):
        holdings_repo.upsert_holding(ctx.conn, customer_id=customer_id, goal_id=goal_id,
                                     asset_class_code=asset_class_code, units=quantity, now=ctx.now_iso())
    log.info("holding_recorded", extra={"customer_id": customer_id, "asset_class_code": asset_class_code})
    return holdings_view(ctx, customer_id)


def drift_report(ctx: ServiceContext, customer_id: str) -> tuple[DriftReport, RecommendationRecord | None]:
    holdings = holdings_repo.list_holdings(ctx.conn, customer_id)
    recommendation = recommendation_repo.latest_for_customer(ctx.conn, customer_id)
    report = compute_drift(
        holdings_repo.units_by_class(holdings),
        nav_repo.latest_nav_per_class(ctx.conn),
        recommendation.allocation if recommendation else None,
        asset_class_repo.display_order_codes(ctx.conn),
    )
    return report, recommendation


def holdings_view(ctx: ServiceContext, customer_id: str) -> dict[str, Any]:
    report, recommendation = drift_report(ctx, customer_id)
    threshold = ctx.settings.drift_threshold_pct
    names = {a.code: a.name for a in asset_class_repo.list_asset_classes(ctx.conn)}
    return {
        "customer_id": customer_id,
        "nav_date": nav_repo.latest_nav_date(ctx.conn),
        "total_value": to_wire(report.total_value),
        "drift_status": report.status.value,
        "max_drift_pct": to_wire_or_none(report.max_drift_pct),
        "threshold_pct": to_wire(threshold),
        "recommendation_id": recommendation.id if recommendation else None,
        "template_version": recommendation.template_version if recommendation else None,
        "lines": [
            {
                "asset_class_code": line.asset_class_code,
                "asset_class_name": names.get(line.asset_class_code, line.asset_class_code),
                "units": to_wire(line.units),
                "nav": to_wire_or_none(line.nav),
                "value": to_wire(line.value),
                "current_pct": to_wire_or_none(line.current_pct),
                "target_pct": to_wire_or_none(line.target_pct),
                "drift_pct": to_wire_or_none(line.drift_pct),
                "exceeds_threshold": line.drift_pct is not None and line.drift_pct > threshold,
            }
            for line in report.lines
        ],
        "positions": [
            {"goal_id": h.goal_id, "asset_class_code": h.asset_class_code, "units": to_wire(h.units)}
            for h in holdings_repo.list_holdings(ctx.conn, customer_id)
        ],
    }
