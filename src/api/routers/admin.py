"""Admin controllers (/admin/*): NAV feed operations. ADMIN role only (NFR-04)."""

from fastapi import APIRouter, Depends

from src.api.deps import admin_user, get_ctx
from src.service import nav_service
from src.service.context import ServiceContext

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_user)])


@router.post("/nav/refresh")
def refresh_nav(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return nav_service.run_refresh_cycle(ctx)


@router.get("/nav/latest")
def latest_nav(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return nav_service.latest_navs(ctx)
