"""Rebalancing engine (AC-06, AC-07): drift trigger, BUY/SELL proposal, accept/dismiss with audit."""

import logging
from typing import Any

from src.domain.drift_calculator import exceeds_threshold
from src.domain.rebalancing_proposer import clean_dismiss_reason, ensure_open, propose
from src.repository import customers_repo, holdings_repo, nav_repo, rebalancing_repo, recommendation_repo
from src.repository.db import transaction
from src.repository.rebalancing_repo import RebalancingRecord
from src.service.context import ServiceContext
from src.service.holdings_service import drift_report
from src.service.rebalancing_views import rebalancing_view
from src.service.recommendation_service import ensure_customer_eligible
from src.types.enums import DriftStatus, RebalancingStatus
from src.types.errors import WealthWiseError, not_found
from src.types.fixed_point import to_wire, to_wire_or_none
from src.types.identity import AuthUser

log = logging.getLogger(__name__)


def _supersede_open(ctx: ServiceContext, customer_id: str) -> int:
    open_ids = rebalancing_repo.open_ids_for_customer(ctx.conn, customer_id)
    for rebalancing_id in open_ids:
        rebalancing_repo.insert_decision(ctx.conn, rebalancing_id=rebalancing_id, status=RebalancingStatus.SUPERSEDED,
                                         reason="superseded by re-evaluation", actor_user_id=None, now=ctx.now_iso())
    return len(open_ids)


def evaluate(ctx: ServiceContext, customer_id: str) -> dict[str, Any]:
    """Supersede any OPEN proposal, then create a new one if max drift > threshold (BR-15, BR-17)."""
    ensure_customer_eligible(ctx, customer_id)
    report, recommendation = drift_report(ctx, customer_id)
    if recommendation is None:
        raise WealthWiseError("RECOMMENDATION_REQUIRED", "generate a portfolio recommendation first")
    threshold = ctx.settings.drift_threshold_pct
    created_id = None
    with transaction(ctx.conn):
        superseded = _supersede_open(ctx, customer_id)
        if exceeds_threshold(report.max_drift_pct, threshold):
            created_id = rebalancing_repo.insert_rebalancing(
                ctx.conn, customer_id=customer_id, portfolio_recommendation_id=recommendation.id,
                template_version=recommendation.template_version, nav_date=nav_repo.latest_nav_date(ctx.conn),
                threshold=threshold, total_value=report.total_value, max_drift=report.max_drift_pct,
                lines=propose(report, nav_repo.latest_nav_per_class(ctx.conn)), now=ctx.now_iso(),
            )
            ctx.audit(actor_user_id=None, action="REBALANCING_PROPOSED", entity_type="rebalancing_recommendation",
                      entity_id=created_id, details={"customer_id": customer_id,
                                                     "portfolio_recommendation_id": recommendation.id})
    log.info("rebalancing_evaluated", extra={"customer_id": customer_id, "triggered": created_id is not None})
    if created_id is None:
        reason = "NO_HOLDINGS" if report.status is DriftStatus.NO_HOLDINGS else "WITHIN_THRESHOLD"
    else:
        reason = None
    return {
        "triggered": created_id is not None,
        "reason": reason,
        "drift_status": report.status.value,
        "max_drift_pct": to_wire_or_none(report.max_drift_pct),
        "threshold_pct": to_wire(threshold),
        "superseded": superseded,
        "rebalancing": rebalancing_view(_find(ctx, created_id)) if created_id else None,
    }


def evaluate_all(ctx: ServiceContext) -> dict[str, int]:
    """Evaluate every KYC-verified customer who has holdings and a recommendation (AC-06.5)."""
    eligible = (set(customers_repo.list_kyc_verified_ids(ctx.conn))
                & set(recommendation_repo.customers_with_recommendations(ctx.conn))
                & set(holdings_repo.customers_with_holdings(ctx.conn)))
    created = superseded = 0
    for customer_id in sorted(eligible):
        result = evaluate(ctx, customer_id)
        created += int(result["triggered"])
        superseded += result["superseded"]
    return {"evaluated": len(eligible), "created": created, "superseded": superseded}


def _find(ctx: ServiceContext, rebalancing_id: str) -> RebalancingRecord:
    record = rebalancing_repo.find_rebalancing(ctx.conn, rebalancing_id)
    if record is None:
        raise not_found("rebalancing recommendation")
    return record


def _owned(ctx: ServiceContext, customer_id: str, rebalancing_id: str) -> RebalancingRecord:
    record = _find(ctx, rebalancing_id)
    if record.customer_id != customer_id:
        raise not_found("rebalancing recommendation")
    return record


def list_for_customer(ctx: ServiceContext, customer_id: str) -> list[dict[str, Any]]:
    return [rebalancing_view(r) for r in rebalancing_repo.list_for_customer(ctx.conn, customer_id)]


def accept(ctx: ServiceContext, user: AuthUser, rebalancing_id: str) -> dict[str, Any]:
    record = _owned(ctx, user.customer_id, rebalancing_id)
    ensure_open(record.status)
    with transaction(ctx.conn):
        rebalancing_repo.insert_decision(ctx.conn, rebalancing_id=record.id, status=RebalancingStatus.ACCEPTED,
                                         reason=None, actor_user_id=user.user_id, now=ctx.now_iso())
        orders = rebalancing_repo.insert_stub_orders(ctx.conn, rebalancing_id=record.id, lines=record.lines,
                                                     now=ctx.now_iso())
        ctx.audit(actor_user_id=user.user_id, action="REBALANCING_ACCEPTED", entity_type="rebalancing_recommendation",
                  entity_id=record.id, details={"customer_id": user.customer_id, "stub_orders": orders})
    log.info("rebalancing_accepted", extra={"customer_id": user.customer_id, "rebalancing_id": record.id})
    return rebalancing_view(_find(ctx, record.id))


def dismiss(ctx: ServiceContext, user: AuthUser, rebalancing_id: str, reason: str | None) -> dict[str, Any]:
    record = _owned(ctx, user.customer_id, rebalancing_id)
    ensure_open(record.status)
    cleaned = clean_dismiss_reason(reason)
    with transaction(ctx.conn):
        rebalancing_repo.insert_decision(ctx.conn, rebalancing_id=record.id, status=RebalancingStatus.DISMISSED,
                                         reason=cleaned, actor_user_id=user.user_id, now=ctx.now_iso())
        ctx.audit(actor_user_id=user.user_id, action="REBALANCING_DISMISSED", entity_type="rebalancing_recommendation",
                  entity_id=record.id, details={"customer_id": user.customer_id, "has_reason": cleaned is not None})
    log.info("rebalancing_dismissed", extra={"customer_id": user.customer_id, "rebalancing_id": record.id})
    return rebalancing_view(_find(ctx, record.id))
