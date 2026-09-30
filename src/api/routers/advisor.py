"""Advisor workbench controllers (/advisor/*). ADVISOR role only (NFR-04)."""

from fastapi import APIRouter, Depends

from src.api.deps import advisor_user, get_ctx
from src.api.schemas import ManualRecommendationRequest, OverrideRequest
from src.service import advisor_service
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/advisor", tags=["advisor"], dependencies=[Depends(advisor_user)])


@router.get("/customers")
def list_customers(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    items = advisor_service.list_customers(ctx)
    return {"items": items, "next_cursor": None, "total": len(items)}


@router.get("/customers/{customer_id}/portfolio")
def customer_portfolio(customer_id: str, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return advisor_service.portfolio(ctx, customer_id)


@router.post("/customers/{customer_id}/risk-band-overrides", status_code=201)
def override_risk_band(customer_id: str, body: OverrideRequest, user: AuthUser = Depends(advisor_user),
                       ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return advisor_service.override_band(ctx, user, customer_id, new_band=body.new_band,
                                         reason_code=body.reason_code, note=body.note)


@router.get("/customers/{customer_id}/audit")
def customer_audit(customer_id: str, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return advisor_service.audit_history(ctx, customer_id)


@router.post("/customers/{customer_id}/manual-recommendations", status_code=201)
def manual_recommendation(customer_id: str, body: ManualRecommendationRequest,
                          user: AuthUser = Depends(advisor_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return advisor_service.log_manual_recommendation(ctx, user, customer_id, body.note)
