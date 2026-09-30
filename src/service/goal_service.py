"""Goal use cases (AC-03): create, list, view, update and archive."""

import dataclasses
import logging
from datetime import date
from typing import Any

from src.domain.goal_policy import validate_goal, validate_name, validate_target_amount, validate_target_date
from src.repository import goals_repo
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.types.enums import GoalPriority, GoalType
from src.types.errors import not_found
from src.types.fixed_point import MONEY_PLACES, parse_fixed, to_wire
from src.types.goals import Goal

log = logging.getLogger(__name__)


def goal_view(goal: Goal) -> dict[str, Any]:
    return {
        "goal_id": goal.id,
        "name": goal.name,
        "goal_type": goal.goal_type.value,
        "target_amount": to_wire(goal.target_amount),
        "target_date": goal.target_date.isoformat(),
        "priority": goal.priority.value,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "archived": goal.archived_at is not None,
    }


def create_goal(ctx: ServiceContext, customer_id: str, *, name: str, goal_type: GoalType, target_amount: str,
                target_date: date, priority: GoalPriority) -> dict[str, Any]:
    amount = parse_fixed(target_amount, MONEY_PLACES, "target_amount")
    cleaned = validate_goal(name, amount, target_date, ctx.clock.today())
    with transaction(ctx.conn):
        goal_id = goals_repo.insert_goal(
            ctx.conn, customer_id=customer_id, name=cleaned, goal_type=goal_type, target_amount=amount,
            target_date=target_date, priority=priority, now=ctx.now_iso(),
        )
    log.info("goal_created", extra={"customer_id": customer_id, "goal_id": goal_id})
    return get_goal(ctx, customer_id, goal_id)


def list_goals(ctx: ServiceContext, customer_id: str) -> list[dict[str, Any]]:
    return [goal_view(g) for g in goals_repo.list_active_goals(ctx.conn, customer_id)]


def load_goal(ctx: ServiceContext, customer_id: str, goal_id: str) -> Goal:
    goal = goals_repo.find_goal(ctx.conn, customer_id, goal_id)
    if goal is None:
        raise not_found("goal")
    return goal


def get_goal(ctx: ServiceContext, customer_id: str, goal_id: str) -> dict[str, Any]:
    return goal_view(load_goal(ctx, customer_id, goal_id))


def _apply_changes(ctx: ServiceContext, goal: Goal, changes: dict[str, Any]) -> Goal:
    updates: dict[str, Any] = {}
    if changes.get("name") is not None:
        updates["name"] = validate_name(changes["name"])
    if changes.get("goal_type") is not None:
        updates["goal_type"] = GoalType(changes["goal_type"])
    if changes.get("priority") is not None:
        updates["priority"] = GoalPriority(changes["priority"])
    if changes.get("target_amount") is not None:
        updates["target_amount"] = parse_fixed(changes["target_amount"], MONEY_PLACES, "target_amount")
        validate_target_amount(updates["target_amount"])
    if changes.get("target_date") is not None:
        validate_target_date(changes["target_date"], ctx.clock.today())
        updates["target_date"] = changes["target_date"]
    if changes.get("archived") is not None:
        updates["archived_at"] = ctx.now_iso() if changes["archived"] else None
    return dataclasses.replace(goal, **updates)


def update_goal(ctx: ServiceContext, customer_id: str, goal_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    goal = _apply_changes(ctx, load_goal(ctx, customer_id, goal_id), changes)
    with transaction(ctx.conn):
        goals_repo.update_goal(ctx.conn, goal, ctx.now_iso())
    log.info("goal_updated", extra={"customer_id": customer_id, "goal_id": goal_id})
    return get_goal(ctx, customer_id, goal_id)
