"""Asset-class master administration."""

from typing import Any

from src.domain.version_policy import validate_asset_class
from src.repository import advisor_repo, asset_class_repo, policy_repo
from src.repository.asset_class_repo import AssetClassRecord
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.types.errors import WealthWiseError, not_found


def _view(record: AssetClassRecord) -> dict[str, Any]:
    return {"code": record.code, "name": record.name, "display_order": record.display_order,
            "is_active": record.is_active}


def list_asset_classes(ctx: ServiceContext) -> list[dict[str, Any]]:
    return [_view(a) for a in asset_class_repo.list_asset_classes(ctx.conn)]


def create_asset_class(ctx: ServiceContext, actor: str, *, code: str, name: str, display_order: int) -> dict:
    cleaned = validate_asset_class(code, name, display_order)
    if asset_class_repo.find_asset_class(ctx.conn, code) is not None:
        raise WealthWiseError("ASSET_CLASS_EXISTS", f"asset class {code} already exists")
    with transaction(ctx.conn):
        asset_class_repo.insert_asset_class(ctx.conn, code=code, name=cleaned, display_order=display_order,
                                            now=ctx.now_iso())
        ctx.audit(actor_user_id=actor, action="ASSET_CLASS_CREATED", entity_type="asset_class", entity_id=code)
    return _view(asset_class_repo.find_asset_class(ctx.conn, code))


def update_asset_class(ctx: ServiceContext, actor: str, code: str, changes: dict[str, Any]) -> dict:
    current = asset_class_repo.find_asset_class(ctx.conn, code)
    if current is None:
        raise not_found("asset class")
    name = changes.get("name") if changes.get("name") is not None else current.name
    order = changes.get("display_order") if changes.get("display_order") is not None else current.display_order
    active = changes.get("is_active") if changes.get("is_active") is not None else current.is_active
    cleaned = validate_asset_class(code, name, order)
    active_version = policy_repo.active_template_version(ctx.conn)
    if not active and active_version and advisor_repo.asset_class_in_template(ctx.conn, code, active_version):
        raise WealthWiseError("ASSET_CLASS_IN_USE", f"{code} is allocated in active template v{active_version}")
    with transaction(ctx.conn):
        asset_class_repo.update_asset_class(ctx.conn, code=code, name=cleaned, display_order=order,
                                            is_active=active, now=ctx.now_iso())
        ctx.audit(actor_user_id=actor, action="ASSET_CLASS_UPDATED", entity_type="asset_class", entity_id=code)
    return _view(asset_class_repo.find_asset_class(ctx.conn, code))
