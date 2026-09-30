"""GET /health — public liveness and DB check (NFR-07)."""

from fastapi import APIRouter, Depends

from src.api.deps import get_ctx
from src.service import health_service
from src.service.context import ServiceContext

router = APIRouter(tags=["health"])


@router.get("/health")
def health(ctx: ServiceContext = Depends(get_ctx)) -> dict[str, str]:
    return health_service.check(ctx)
