"""Customer portfolio controllers: holdings, goal progress and rebalancing. CUSTOMER role only (NFR-04)."""

from fastapi import APIRouter, Depends

from src.api.deps import customer_user, get_ctx
from src.api.schemas import DismissRequest, HoldingRequest
from src.service import goal_progress_service, holdings_service, rebalancing_service
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/me", tags=["customer-portfolio"], dependencies=[Depends(customer_user)])


@router.get("/holdings")
def get_holdings(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return holdings_service.holdings_view(ctx, user.customer_id)


@router.post("/holdings")
def record_holding(body: HoldingRequest, user: AuthUser = Depends(customer_user),
                   ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return holdings_service.record_holding(
        ctx, user.customer_id, asset_class_code=body.asset_class_code, goal_id=body.goal_id, units=body.units
    )


@router.get("/goals/{goal_id}/progress")
def goal_progress(goal_id: str, user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return goal_progress_service.progress_view(ctx, user.customer_id, goal_id)


@router.post("/rebalancing/evaluate")
def evaluate_rebalancing(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return rebalancing_service.evaluate(ctx, user.customer_id)


@router.get("/rebalancing")
def list_rebalancing(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    items = rebalancing_service.list_for_customer(ctx, user.customer_id)
    return {"items": items, "next_cursor": None, "total": len(items)}


@router.post("/rebalancing/{rebalancing_id}/accept")
def accept_rebalancing(rebalancing_id: str, user: AuthUser = Depends(customer_user),
                       ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return rebalancing_service.accept(ctx, user, rebalancing_id)


@router.post("/rebalancing/{rebalancing_id}/dismiss")
def dismiss_rebalancing(rebalancing_id: str, body: DismissRequest | None = None,
                        user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return rebalancing_service.dismiss(ctx, user, rebalancing_id, body.reason if body else None)
