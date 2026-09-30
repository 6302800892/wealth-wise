"""Customer portfolio controllers (/me/holdings). CUSTOMER role only (NFR-04)."""

from fastapi import APIRouter, Depends

from src.api.deps import customer_user, get_ctx
from src.api.schemas import HoldingRequest
from src.service import holdings_service
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
