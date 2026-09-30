"""Advisor workbench (AC-09): customer list, portfolio view, audited overrides, manual recommendations."""

import logging
from typing import Any

from src.domain.override_policy import validate_override
from src.repository import advisor_repo, audit_repo, customers_repo, rebalancing_repo, recommendation_repo, risk_repo
from src.repository.db import transaction
from src.service import goal_progress_service, holdings_service, rebalancing_service, risk_profile_service
from src.service.context import ServiceContext
from src.service.goal_service import list_goals
from src.service.recommendation_service import recommendation_view
from src.types.enums import BandSource, RebalancingStatus, RiskBand
from src.types.errors import not_found, validation_error
from src.types.identity import AuthUser

log = logging.getLogger(__name__)


def _customer(ctx: ServiceContext, customer_id: str):
    customer = customers_repo.find_customer(ctx.conn, customer_id)
    if customer is None:
        raise not_found("customer")
    return customer


def list_customers(ctx: ServiceContext) -> list[dict[str, Any]]:
    items = []
    for customer in customers_repo.list_customers(ctx.conn):
        assignment = risk_repo.latest_assignment(ctx.conn, customer.id)
        open_count = sum(r.status is RebalancingStatus.OPEN
                         for r in rebalancing_repo.list_for_customer(ctx.conn, customer.id))
        items.append({"customer_id": customer.id, "display_name": customer.full_name,
                      "kyc_verified": customer.kyc_verified,
                      "risk_band": assignment.risk_band.value if assignment else None,
                      "open_rebalancing": open_count})
    return items


def portfolio(ctx: ServiceContext, customer_id: str) -> dict[str, Any]:
    customer = _customer(ctx, customer_id)
    latest = recommendation_repo.latest_for_customer(ctx.conn, customer_id)
    goals = list_goals(ctx, customer_id)
    return {
        "customer": {"customer_id": customer.id, "display_name": customer.full_name, "email": customer.email,
                     "kyc_verified": customer.kyc_verified},
        "risk_profile": risk_profile_service.risk_profile(ctx, customer_id),
        "goals": [{**g, "progress": goal_progress_service.progress_view(ctx, customer_id, g["goal_id"])}
                  for g in goals],
        "recommendation": recommendation_view(ctx, latest) if latest else None,
        "holdings": holdings_service.holdings_view(ctx, customer_id),
        "rebalancing": rebalancing_service.list_for_customer(ctx, customer_id),
    }


def override_band(ctx: ServiceContext, advisor: AuthUser, customer_id: str, *, new_band: RiskBand,
                  reason_code: str, note: str) -> dict[str, Any]:
    """Write the override record, the ADVISOR_OVERRIDE assignment and an audit row atomically (BR-20)."""
    _customer(ctx, customer_id)
    current = risk_repo.latest_assignment(ctx.conn, customer_id)
    previous_band = current.risk_band if current else None
    reason, cleaned = validate_override(previous_band, new_band, reason_code, note)
    now = ctx.now_iso()
    with transaction(ctx.conn):
        override_id = risk_repo.insert_override(ctx.conn, customer_id=customer_id, previous_band=previous_band,
                                                new_band=new_band, reason=reason, note=cleaned,
                                                actor=advisor.user_id, now=now)
        risk_repo.insert_assignment(ctx.conn, customer_id=customer_id, band=new_band,
                                    source=BandSource.ADVISOR_OVERRIDE, assessment_id=None, override_id=override_id,
                                    rule_set_version=None, assigned_by=advisor.user_id, now=now)
        ctx.audit(actor_user_id=advisor.user_id, action="RISK_BAND_OVERRIDDEN", entity_type="customer",
                  entity_id=customer_id, details={"override_id": override_id, "reason_code": reason.value})
    log.info("risk_band_overridden", extra={"customer_id": customer_id, "override_id": override_id})
    return _override_view(risk_repo.list_overrides(ctx.conn, customer_id)[0])


def _override_view(record) -> dict[str, Any]:
    return {"override_id": record.id, "previous_band": record.previous_band.value if record.previous_band else None,
            "new_band": record.new_band.value, "reason_code": record.reason_code.value, "note": record.note,
            "actor_user_id": record.actor_user_id, "created_at": record.created_at}


def log_manual_recommendation(ctx: ServiceContext, advisor: AuthUser, customer_id: str, note: str) -> dict[str, Any]:
    _customer(ctx, customer_id)
    cleaned = note.strip()
    if not cleaned or len(cleaned) > 1000:
        raise validation_error("note", "note must be 1–1000 characters")
    with transaction(ctx.conn):
        record_id = advisor_repo.insert_manual_recommendation(ctx.conn, customer_id=customer_id,
                                                              advisor_user_id=advisor.user_id, note=cleaned,
                                                              now=ctx.now_iso())
        ctx.audit(actor_user_id=advisor.user_id, action="MANUAL_RECOMMENDATION_LOGGED", entity_type="customer",
                  entity_id=customer_id, details={"manual_recommendation_id": record_id})
    return {"manual_recommendation_id": record_id, "customer_id": customer_id, "note": cleaned,
            "advisor_user_id": advisor.user_id, "created_at": ctx.now_iso()}


def audit_history(ctx: ServiceContext, customer_id: str) -> dict[str, Any]:
    _customer(ctx, customer_id)
    rebalancing_ids = [r.id for r in rebalancing_repo.list_for_customer(ctx.conn, customer_id)]
    events = audit_repo.list_for_entities(ctx.conn, [customer_id, *rebalancing_ids])
    return {
        "overrides": [_override_view(o) for o in risk_repo.list_overrides(ctx.conn, customer_id)],
        "manual_recommendations": [
            {"manual_recommendation_id": m.id, "note": m.note, "advisor_user_id": m.advisor_user_id,
             "created_at": m.created_at}
            for m in advisor_repo.list_manual_recommendations(ctx.conn, customer_id)
        ],
        "events": [{"action": e.action, "entity_type": e.entity_type, "entity_id": e.entity_id,
                    "actor_user_id": e.actor_user_id, "created_at": e.created_at, "details": e.details}
                   for e in events],
    }
