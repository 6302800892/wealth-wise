"""Risk-profile use cases: questionnaire, assessment submission and effective band (AC-01, AC-10.4)."""

import logging

from src.domain.risk_band_scorer import assess
from src.repository import policy_repo, risk_repo
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.types.enums import BandSource
from src.types.errors import WealthWiseError
from src.types.identity import AuthUser
from src.types.policy import RuleSet

log = logging.getLogger(__name__)


def active_rule_set(ctx: ServiceContext) -> RuleSet:
    version = policy_repo.active_rule_set_version(ctx.conn)
    loaded = policy_repo.get_rule_set(ctx.conn, version) if version else None
    if loaded is None:
        raise WealthWiseError("RULE_SET_NOT_ACTIVE", "no published risk rule set is available")
    return loaded[1]


def questionnaire(ctx: ServiceContext) -> dict:
    """Questions and options of the active rule set. Scores are not exposed to customers."""
    rule_set = active_rule_set(ctx)
    return {
        "rule_set_version": rule_set.version,
        "questions": [
            {"question_id": q.id, "text": q.text,
             "options": [{"option_id": o.id, "text": o.text} for o in q.options]}
            for q in rule_set.questions
        ],
    }


def submit_assessment(ctx: ServiceContext, user: AuthUser, rule_set_version: int,
                      answers: list[tuple[str, str]]) -> dict:
    rule_set = active_rule_set(ctx)
    if rule_set_version != rule_set.version:
        raise WealthWiseError(
            "RULE_SET_NOT_ACTIVE", f"rule set v{rule_set_version} is not active; reload the questionnaire",
            {"active_version": rule_set.version},
        )
    result = assess(rule_set, answers)
    now = ctx.now_iso()
    with transaction(ctx.conn):
        assessment_id = risk_repo.insert_assessment(
            ctx.conn, customer_id=user.customer_id, rule_set_version=rule_set.version, answers=list(answers),
            total_score=result.total_score, band=result.risk_band, now=now,
        )
        risk_repo.insert_assignment(
            ctx.conn, customer_id=user.customer_id, band=result.risk_band, source=BandSource.QUESTIONNAIRE,
            assessment_id=assessment_id, override_id=None, rule_set_version=rule_set.version,
            assigned_by=user.user_id, now=now,
        )
        ctx.audit(actor_user_id=user.user_id, action="RISK_ASSESSMENT_SUBMITTED", entity_type="customer",
                  entity_id=user.customer_id, details={"assessment_id": assessment_id,
                                                      "rule_set_version": rule_set.version})
    log.info("risk_assessment_submitted", extra={"customer_id": user.customer_id, "assessment_id": assessment_id})
    return {
        "assessment_id": assessment_id,
        "rule_set_version": rule_set.version,
        "total_score": result.total_score,
        "risk_band": result.risk_band.value,
        "assigned_at": now,
    }


def risk_profile(ctx: ServiceContext, customer_id: str) -> dict:
    """Effective band = latest assignment (BR-05). Advisor notes are never exposed here."""
    assignment = risk_repo.latest_assignment(ctx.conn, customer_id)
    if assignment is None:
        return {"customer_id": customer_id, "risk_band": None, "source": None,
                "rule_set_version": None, "assigned_at": None}
    return {
        "customer_id": customer_id,
        "risk_band": assignment.risk_band.value,
        "source": assignment.source.value,
        "rule_set_version": assignment.rule_set_version,
        "assigned_at": assignment.assigned_at,
    }
