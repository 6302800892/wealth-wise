"""Loads synthetic demo data (spec §14) into an empty database."""

import json
import logging
from pathlib import Path
from typing import Any

from src.repository import customers_repo, users_repo
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.service.security import hash_password
from src.types.enums import Role

log = logging.getLogger(__name__)


def _load(seed_dir: str) -> dict[str, Any]:
    return json.loads((Path(seed_dir) / "demo_seed.json").read_text(encoding="utf-8"))


def _seed_people(ctx: ServiceContext, data: dict[str, Any]) -> dict[str, str]:
    now = ctx.now_iso()
    customer_ids = {}
    for customer in data["customers"]:
        customer_ids[customer["key"]] = customers_repo.insert_customer(
            ctx.conn, full_name=customer["full_name"], email=customer["email"],
            date_of_birth=customer["date_of_birth"], kyc_verified=customer["kyc_verified"], now=now,
        )
    for user in data["users"]:
        users_repo.insert_user(
            ctx.conn, username=user["username"],
            password_hash=hash_password(ctx.settings.demo_password, ctx.settings.password_hash_iterations),
            role=Role(user["role"]), customer_id=customer_ids.get(user["customer"]) if user["customer"] else None,
            display_name=user["display_name"], now=now,
        )
    return customer_ids


def seed_if_empty(ctx: ServiceContext) -> bool:
    """Seed demo data once. Returns True when data was inserted."""
    if users_repo.count_users(ctx.conn) > 0:
        return False
    data = _load(ctx.settings.seed_dir)
    with transaction(ctx.conn):
        _seed_people(ctx, data)
    log.info("demo_seed_loaded", extra={"customers": len(data["customers"]), "users": len(data["users"])})
    return True
