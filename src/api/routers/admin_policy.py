"""Admin policy-versioning controllers: risk rule sets and allocation templates (AC-10). ADMIN only."""

from fastapi import APIRouter, Depends

from src.api.deps import admin_user, get_ctx
from src.api.schemas import RuleSetDefinition, TemplateDraftRequest
from src.service import policy_admin_service as policies
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/admin", tags=["admin-policy"], dependencies=[Depends(admin_user)])


@router.get("/risk-rule-sets")
def list_rule_sets(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.list_rule_sets(ctx)


@router.post("/risk-rule-sets", status_code=201)
def create_rule_set_draft(user: AuthUser = Depends(admin_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.create_rule_set_draft(ctx, user.user_id)


@router.get("/risk-rule-sets/{version}")
def get_rule_set(version: int, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.rule_set_view(ctx, version)


@router.put("/risk-rule-sets/{version}")
def update_rule_set(version: int, body: RuleSetDefinition, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.update_rule_set_draft(ctx, version, body.model_dump(mode="json"))


@router.post("/risk-rule-sets/{version}/publish")
def publish_rule_set(version: int, user: AuthUser = Depends(admin_user),
                     ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.publish_rule_set(ctx, version, user.user_id)


@router.get("/allocation-templates")
def list_templates(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.list_templates(ctx)


@router.post("/allocation-templates", status_code=201)
def create_template_draft(user: AuthUser = Depends(admin_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.create_template_draft(ctx, user.user_id)


@router.get("/allocation-templates/{version}")
def get_template(version: int, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.template_view(ctx, version)


@router.put("/allocation-templates/{version}")
def update_template(version: int, body: TemplateDraftRequest, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.update_template_draft(ctx, version, [row.model_dump(mode="json") for row in body.rows])


@router.post("/allocation-templates/{version}/publish")
def publish_template(version: int, user: AuthUser = Depends(admin_user),
                     ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return policies.publish_template(ctx, version, user.user_id)
