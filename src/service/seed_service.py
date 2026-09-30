"""Loads synthetic demo data (spec §14) into an empty database by replaying real use cases."""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from src.repository import customers_repo, users_repo
from src.repository.db import transaction
from src.service import goal_service, holdings_service, nav_service, recommendation_service, risk_profile_service
from src.service.context import ServiceContext
from src.service.security import hash_password
from src.types.enums import GoalPriority, GoalType, Role
from src.types.identity import AuthUser

log = logging.getLogger(__name__)


def _load(seed_dir: str) -> dict[str, Any]:
    return json.loads((Path(seed_dir) / "demo_seed.json").read_text(encoding="utf-8"))


def _seed_people(ctx: ServiceContext, data: dict[str, Any]) -> None:
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


def _auth_user(ctx: ServiceContext, username: str) -> AuthUser:
    record = users_repo.find_by_username(ctx.conn, username)
    return AuthUser(user_id=record.id, username=record.username, role=record.role,
                    customer_id=record.customer_id, display_name=record.display_name)


def _replay_journey(ctx: ServiceContext, journey: dict[str, Any]) -> dict[str, str]:
    user = _auth_user(ctx, journey["username"])
    rule_set = risk_profile_service.active_rule_set(ctx)
    answers = list(journey["questionnaire_options"].items())
    risk_profile_service.submit_assessment(ctx, user, rule_set.version, answers)
    goal_ids = {}
    for goal in journey["goals"]:
        created = goal_service.create_goal(
            ctx, user.customer_id, name=goal["name"], goal_type=GoalType(goal["goal_type"]),
            target_amount=goal["target_amount"], target_date=date.fromisoformat(goal["target_date"]),
            priority=GoalPriority(goal["priority"]),
        )
        goal_ids[goal["key"]] = created["goal_id"]
    if journey.get("recommend"):
        recommendation_service.generate(ctx, user.customer_id)
    for holding in journey.get("holdings", []):
        holdings_service.record_holding(
            ctx, user.customer_id, asset_class_code=holding["asset_class_code"],
            goal_id=goal_ids[holding["goal"]], units=holding["units"],
        )
    return goal_ids


def seed_if_empty(ctx: ServiceContext) -> bool:
    """Seed demo data once, atomically. Returns True when data was inserted."""
    if users_repo.count_users(ctx.conn) > 0:
        return False
    data = _load(ctx.settings.seed_dir)
    with transaction(ctx.conn):
        _seed_people(ctx, data)
        nav_service.ingest_next_day(ctx)
        goal_ids: dict[str, str] = {}
        for journey in data.get("journeys", []):
            goal_ids.update(_replay_journey(ctx, journey))
    log.info("demo_seed_loaded", extra={"customers": len(data["customers"]), "users": len(data["users"])})
    return True
