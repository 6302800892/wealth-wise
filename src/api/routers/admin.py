"""Admin controllers (/admin/*): NAV feed operations and the asset-class master. ADMIN role only (NFR-04)."""

from fastapi import APIRouter, Depends

from src.api.deps import admin_user, get_ctx
from src.api.schemas import AssetClassCreateRequest, AssetClassUpdateRequest
from src.service import asset_class_service, nav_service
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_user)])


@router.post("/nav/refresh")
def refresh_nav(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return nav_service.run_refresh_cycle(ctx)


@router.get("/nav/latest")
def latest_nav(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return nav_service.latest_navs(ctx)


@router.get("/asset-classes")
def list_asset_classes(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    items = asset_class_service.list_asset_classes(ctx)
    return {"items": items, "next_cursor": None, "total": len(items)}


@router.post("/asset-classes", status_code=201)
def create_asset_class(body: AssetClassCreateRequest, user: AuthUser = Depends(admin_user),
                       ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return asset_class_service.create_asset_class(ctx, user.user_id, code=body.code, name=body.name,
                                                  display_order=body.display_order)


@router.patch("/asset-classes/{code}")
def update_asset_class(code: str, body: AssetClassUpdateRequest, user: AuthUser = Depends(admin_user),
                       ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return asset_class_service.update_asset_class(ctx, user.user_id, code, body.model_dump(exclude_unset=True))
