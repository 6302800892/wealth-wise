"""Portfolio recommendation use cases (AC-02, AC-04): deterministic, versioned, idempotent."""

import logging
from typing import Any

from src.domain.eligibility_policy import ensure_goal_present, ensure_kyc_verified, ensure_risk_band
from src.domain.horizon_resolver import horizon_bucket
from src.domain.recommendation_resolver import input_fingerprint, resolve_allocation, select_primary_goal
from src.repository import asset_class_repo, customers_repo, goals_repo, policy_repo, recommendation_repo, risk_repo
from src.repository.db import transaction
from src.repository.recommendation_repo import RecommendationRecord
from src.service.context import ServiceContext
from src.types.errors import WealthWiseError, not_found
from src.types.fixed_point import to_wire
from src.types.goals import Goal

log = logging.getLogger(__name__)


def recommendation_view(ctx: ServiceContext, record: RecommendationRecord) -> dict[str, Any]:
    names = {a.code: a.name for a in asset_class_repo.list_asset_classes(ctx.conn)}
    return {
        "recommendation_id": record.id,
        "goal_id": record.goal_id,
        "risk_band": record.risk_band.value,
        "horizon_bucket": record.horizon_bucket.value,
        "template_version": record.template_version,
        "as_of_date": record.as_of_date.isoformat(),
        "input_fingerprint": record.input_fingerprint,
        "allocation": [
            {"asset_class_code": code, "asset_class_name": names.get(code, code), "target_pct": to_wire(pct)}
            for code, pct in record.allocation.items()
        ],
        "total_pct": to_wire(sum(record.allocation.values())),
        "created_at": record.created_at,
    }


def ensure_customer_eligible(ctx: ServiceContext, customer_id: str) -> None:
    customer = customers_repo.find_customer(ctx.conn, customer_id)
    if customer is None:
        raise not_found("customer")
    ensure_kyc_verified(customer.kyc_verified)


def _target_goal(ctx: ServiceContext, customer_id: str, goal_id: str | None) -> Goal:
    goals = goals_repo.list_active_goals(ctx.conn, customer_id)
    if goal_id is not None:
        match = next((g for g in goals if g.id == goal_id), None)
        if match is None:
            raise not_found("goal")
        return match
    primary = select_primary_goal([g.ref() for g in goals])
    ensure_goal_present(primary.id if primary else None)
    return next(g for g in goals if g.id == primary.id)


def generate(ctx: ServiceContext, customer_id: str, goal_id: str | None = None) -> tuple[dict[str, Any], bool]:
    """Return (recommendation, created). Identical inputs return the existing recommendation (BR-11)."""
    ensure_customer_eligible(ctx, customer_id)
    assignment = risk_repo.latest_assignment(ctx.conn, customer_id)
    band = ensure_risk_band(assignment.risk_band if assignment else None)
    goal = _target_goal(ctx, customer_id, goal_id)
    template_version = policy_repo.active_template_version(ctx.conn)
    template = policy_repo.get_template_set(ctx.conn, template_version) if template_version else None
    if template is None:
        raise WealthWiseError("TEMPLATE_NOT_ACTIVE", "no published allocation template is available")
    as_of = ctx.clock.today()
    horizon = horizon_bucket(as_of, goal.target_date)
    allocation = resolve_allocation(template, band, horizon)
    fingerprint = input_fingerprint(band, horizon, template.version, goal.id)
    latest = recommendation_repo.latest_for_customer(ctx.conn, customer_id)
    if latest is not None and latest.input_fingerprint == fingerprint:
        return recommendation_view(ctx, latest), False
    with transaction(ctx.conn):
        recommendation_id = recommendation_repo.insert_recommendation(
            ctx.conn, customer_id=customer_id, goal_id=goal.id, assignment_id=assignment.id, band=band,
            horizon=horizon, template_version=template.version, as_of=as_of, fingerprint=fingerprint,
            allocation=allocation, now=ctx.now_iso(),
        )
        ctx.audit(actor_user_id=None, action="PORTFOLIO_RECOMMENDATION_CREATED", entity_type="customer",
                  entity_id=customer_id, details={"recommendation_id": recommendation_id,
                                                 "template_version": template.version})
    log.info("recommendation_created", extra={"customer_id": customer_id, "recommendation_id": recommendation_id})
    return recommendation_view(ctx, recommendation_repo.latest_for_customer(ctx.conn, customer_id)), True


def latest(ctx: ServiceContext, customer_id: str) -> dict[str, Any]:
    record = recommendation_repo.latest_for_customer(ctx.conn, customer_id)
    if record is None:
        raise not_found("recommendation")
    return recommendation_view(ctx, record)
