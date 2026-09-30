"""Goal tracker (AC-08): live progress and one snapshot per goal on each NAV refresh."""

from decimal import Decimal
from typing import Any

from src.domain.goal_progress_calculator import goal_status, goal_value, percent_complete
from src.repository import goals_repo, holdings_repo, nav_repo, progress_repo
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.service.goal_service import load_goal
from src.types.fixed_point import to_wire
from src.types.goals import Goal


def _progress(ctx: ServiceContext, goal: Goal, navs: dict[str, Decimal]) -> tuple[Decimal, Decimal]:
    positions = [(h.asset_class_code, h.units) for h in holdings_repo.list_goal_holdings(ctx.conn, goal.id)]
    value = goal_value(positions, navs)
    return value, percent_complete(value, goal.target_amount)


def snapshot_all(ctx: ServiceContext, nav_date: str) -> int:
    """Snapshot every active goal for `nav_date`; returns how many new snapshots were written."""
    navs = nav_repo.latest_nav_per_class(ctx.conn)
    written = 0
    with transaction(ctx.conn):
        for goal in goals_repo.list_all_active_goals(ctx.conn):
            value, pct = _progress(ctx, goal, navs)
            written += progress_repo.insert_snapshot_if_absent(
                ctx.conn, goal_id=goal.id, nav_date=nav_date, current_value=value,
                target_amount=goal.target_amount, percent_complete=pct, now=ctx.now_iso(),
            )
    return written


def progress_view(ctx: ServiceContext, customer_id: str, goal_id: str) -> dict[str, Any]:
    goal = load_goal(ctx, customer_id, goal_id)
    value, pct = _progress(ctx, goal, nav_repo.latest_nav_per_class(ctx.conn))
    return {
        "goal_id": goal.id,
        "name": goal.name,
        "target_amount": to_wire(goal.target_amount),
        "current_value": to_wire(value),
        "percent_complete": to_wire(pct),
        "status": goal_status(pct).value,
        "nav_date": nav_repo.latest_nav_date(ctx.conn),
        "history": [
            {"nav_date": s.nav_date, "current_value": to_wire(s.current_value),
             "percent_complete": to_wire(s.percent_complete), "status": goal_status(s.percent_complete).value}
            for s in progress_repo.list_snapshots(ctx.conn, goal.id)
        ],
    }
