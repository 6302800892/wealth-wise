"""Goal persistence. Amounts are stored as integer paise (NFR-01)."""

import sqlite3
import uuid
from datetime import date
from decimal import Decimal

from src.types.enums import GoalPriority, GoalType
from src.types.fixed_point import MONEY_PLACES, from_scaled_int, to_scaled_int
from src.types.goals import Goal

_ORDER = "CASE priority WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 ELSE 2 END, target_date, created_at, id"


def _to_goal(row: sqlite3.Row) -> Goal:
    return Goal(
        id=row["id"], customer_id=row["customer_id"], name=row["name"], goal_type=GoalType(row["goal_type"]),
        target_amount=from_scaled_int(row["target_amount_paise"], MONEY_PLACES),
        target_date=date.fromisoformat(row["target_date"]), priority=GoalPriority(row["priority"]),
        created_at=row["created_at"], updated_at=row["updated_at"], archived_at=row["archived_at"],
    )


def insert_goal(conn: sqlite3.Connection, *, customer_id: str, name: str, goal_type: GoalType,
                target_amount: Decimal, target_date: date, priority: GoalPriority, now: str) -> str:
    goal_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO goals (id, customer_id, name, goal_type, target_amount_paise, target_date, priority,"
        " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (goal_id, customer_id, name, goal_type.value, to_scaled_int(target_amount, MONEY_PLACES),
         target_date.isoformat(), priority.value, now, now),
    )
    return goal_id


def find_goal(conn: sqlite3.Connection, customer_id: str, goal_id: str) -> Goal | None:
    row = conn.execute("SELECT * FROM goals WHERE id = ? AND customer_id = ?", (goal_id, customer_id)).fetchone()
    return None if row is None else _to_goal(row)


def list_active_goals(conn: sqlite3.Connection, customer_id: str) -> list[Goal]:
    rows = conn.execute(
        f"SELECT * FROM goals WHERE customer_id = ? AND archived_at IS NULL ORDER BY {_ORDER}", (customer_id,)
    ).fetchall()
    return [_to_goal(row) for row in rows]


def list_all_active_goals(conn: sqlite3.Connection) -> list[Goal]:
    rows = conn.execute(f"SELECT * FROM goals WHERE archived_at IS NULL ORDER BY customer_id, {_ORDER}").fetchall()
    return [_to_goal(row) for row in rows]


def update_goal(conn: sqlite3.Connection, goal: Goal, now: str) -> None:
    conn.execute(
        "UPDATE goals SET name = ?, goal_type = ?, target_amount_paise = ?, target_date = ?, priority = ?,"
        " archived_at = ?, updated_at = ? WHERE id = ?",
        (goal.name, goal.goal_type.value, to_scaled_int(goal.target_amount, MONEY_PLACES),
         goal.target_date.isoformat(), goal.priority.value, goal.archived_at, now, goal.id),
    )
