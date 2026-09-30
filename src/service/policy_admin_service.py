"""Admin policy versioning (AC-10, AC-02): drafts cloned from the active version, validated publish."""

import logging
from decimal import Decimal
from typing import Any

from src.domain.allocation_template_validator import check_publishable, check_row_ranges
from src.domain.version_policy import ensure_draft, validate_rule_set
from src.repository import asset_class_repo, policy_repo
from src.repository.db import transaction
from src.repository.policy_repo import VersionMeta
from src.service.context import ServiceContext
from src.types.enums import HorizonBucket, RiskBand, VersionStatus
from src.types.errors import WealthWiseError, not_found
from src.types.fixed_point import PERCENT_PLACES, parse_fixed, to_wire
from src.types.policy import TemplateRows, rule_set_from_definition, rule_set_to_definition

log = logging.getLogger(__name__)


def _meta_view(meta: VersionMeta) -> dict[str, Any]:
    return {"version": meta.version, "status": meta.status.value, "created_by": meta.created_by,
            "created_at": meta.created_at, "published_by": meta.published_by, "published_at": meta.published_at}


def _no_draft(metas: list[VersionMeta]) -> None:
    if any(m.status is VersionStatus.DRAFT for m in metas):
        raise WealthWiseError("DRAFT_ALREADY_EXISTS", "a draft already exists; edit or publish it first")


# ---- risk rule sets -------------------------------------------------------------------------

def _rule_set(ctx: ServiceContext, version: int):
    loaded = policy_repo.get_rule_set(ctx.conn, version)
    if loaded is None:
        raise not_found("rule set version")
    return loaded


def rule_set_view(ctx: ServiceContext, version: int) -> dict[str, Any]:
    meta, rule_set = _rule_set(ctx, version)
    return {**_meta_view(meta), "definition": rule_set_to_definition(rule_set)}


def list_rule_sets(ctx: ServiceContext) -> dict[str, Any]:
    return {"active_version": policy_repo.active_rule_set_version(ctx.conn),
            "items": [_meta_view(m) for m in policy_repo.list_rule_set_versions(ctx.conn)]}


def create_rule_set_draft(ctx: ServiceContext, actor: str) -> dict[str, Any]:
    _no_draft(policy_repo.list_rule_set_versions(ctx.conn))
    _, active = _rule_set(ctx, policy_repo.active_rule_set_version(ctx.conn))
    version = policy_repo.next_rule_set_version(ctx.conn)
    with transaction(ctx.conn):
        policy_repo.insert_rule_set_draft(ctx.conn, version=version, definition=rule_set_to_definition(active),
                                          actor=actor, now=ctx.now_iso())
    return rule_set_view(ctx, version)


def update_rule_set_draft(ctx: ServiceContext, version: int, definition: dict[str, Any]) -> dict[str, Any]:
    meta, _ = _rule_set(ctx, version)
    ensure_draft(meta.status)
    parsed = rule_set_from_definition(version, definition)
    with transaction(ctx.conn):
        policy_repo.update_rule_set_draft(ctx.conn, version=version, definition=rule_set_to_definition(parsed))
    return rule_set_view(ctx, version)


def publish_rule_set(ctx: ServiceContext, version: int, actor: str) -> dict[str, Any]:
    meta, rule_set = _rule_set(ctx, version)
    ensure_draft(meta.status)
    validate_rule_set(rule_set)
    with transaction(ctx.conn):
        policy_repo.publish_rule_set(ctx.conn, version=version, actor=actor, now=ctx.now_iso())
        ctx.audit(actor_user_id=actor, action="RULE_SET_PUBLISHED", entity_type="risk_rule_set",
                  entity_id=str(version), details={"version": version})
    log.info("rule_set_published", extra={"version": version})
    return rule_set_view(ctx, version)


# ---- allocation templates -------------------------------------------------------------------

def _template_meta(ctx: ServiceContext, version: int) -> VersionMeta:
    meta = policy_repo.get_template_meta(ctx.conn, version)
    if meta is None:
        raise not_found("template version")
    return meta


def template_view(ctx: ServiceContext, version: int) -> dict[str, Any]:
    meta = _template_meta(ctx, version)
    template = policy_repo.get_template_set(ctx.conn, version)
    rows = [{"risk_band": band.value, "horizon_bucket": horizon.value,
             "allocations": {code: to_wire(pct) for code, pct in row.items()}}
            for (band, horizon), row in template.rows.items()]
    return {**_meta_view(meta), "rows": rows}


def list_templates(ctx: ServiceContext) -> dict[str, Any]:
    return {"active_version": policy_repo.active_template_version(ctx.conn),
            "items": [_meta_view(m) for m in policy_repo.list_template_versions(ctx.conn)]}


def create_template_draft(ctx: ServiceContext, actor: str) -> dict[str, Any]:
    _no_draft(policy_repo.list_template_versions(ctx.conn))
    active = policy_repo.get_template_set(ctx.conn, policy_repo.active_template_version(ctx.conn))
    version = policy_repo.next_template_version(ctx.conn)
    with transaction(ctx.conn):
        policy_repo.insert_template_draft(ctx.conn, version=version, actor=actor, now=ctx.now_iso())
        policy_repo.replace_template_rows(ctx.conn, version=version, rows=active.rows)
    return template_view(ctx, version)


def parse_rows(rows: list[dict[str, Any]]) -> TemplateRows:
    parsed: dict[tuple[RiskBand, HorizonBucket], dict[str, Decimal]] = {}
    for row in rows:
        key = (RiskBand(row["risk_band"]), HorizonBucket(row["horizon_bucket"]))
        parsed[key] = {code: parse_fixed(pct, PERCENT_PLACES, f"{key[0].value}/{key[1].value} {code}")
                       for code, pct in row["allocations"].items()}
    return parsed


def update_template_draft(ctx: ServiceContext, version: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    ensure_draft(_template_meta(ctx, version).status)
    parsed = parse_rows(rows)
    check_row_ranges(parsed)
    known = {a.code for a in asset_class_repo.list_asset_classes(ctx.conn)}
    unknown = sorted({code for row in parsed.values() for code in row} - known)
    if unknown:
        raise WealthWiseError("VALIDATION_FAILED", f"unknown asset classes: {unknown}")
    with transaction(ctx.conn):
        policy_repo.replace_template_rows(ctx.conn, version=version, rows=parsed)
    return template_view(ctx, version)


def publish_template(ctx: ServiceContext, version: int, actor: str) -> dict[str, Any]:
    ensure_draft(_template_meta(ctx, version).status)
    template = policy_repo.get_template_set(ctx.conn, version)
    active_codes = [a.code for a in asset_class_repo.list_asset_classes(ctx.conn, active_only=True)]
    check_publishable(template.rows, active_codes)
    with transaction(ctx.conn):
        policy_repo.publish_template(ctx.conn, version=version, actor=actor, now=ctx.now_iso())
        ctx.audit(actor_user_id=actor, action="TEMPLATE_PUBLISHED", entity_type="allocation_template",
                  entity_id=str(version), details={"version": version})
    log.info("template_published", extra={"version": version})
    return template_view(ctx, version)
