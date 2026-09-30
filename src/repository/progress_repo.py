"""Append-only goal progress snapshots, one per goal per NAV date (BR-19)."""

import sqlite3
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.types.fixed_point import MONEY_PLACES, PERCENT_PLACES, from_scaled_int, to_scaled_int


@dataclass(frozen=True)
class SnapshotRecord:
    goal_id: str
    nav_date: str
    current_value: Decimal
    target_amount: Decimal
    percent_complete: Decimal


def insert_snapshot_if_absent(conn: sqlite3.Connection, *, goal_id: str, nav_date: str, current_value: Decimal,
                              target_amount: Decimal, percent_complete: Decimal, now: str) -> bool:
    cursor = conn.execute(
        "INSERT OR IGNORE INTO goal_progress_snapshots (id, goal_id, nav_date, current_value_paise,"
        " target_amount_paise, percent_complete_bp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), goal_id, nav_date, to_scaled_int(current_value, MONEY_PLACES),
         to_scaled_int(target_amount, MONEY_PLACES), to_scaled_int(percent_complete, PERCENT_PLACES), now),
    )
    return cursor.rowcount == 1


def list_snapshots(conn: sqlite3.Connection, goal_id: str) -> list[SnapshotRecord]:
    rows = conn.execute("SELECT * FROM goal_progress_snapshots WHERE goal_id = ? ORDER BY nav_date DESC",
                        (goal_id,)).fetchall()
    return [
        SnapshotRecord(goal_id=r["goal_id"], nav_date=r["nav_date"],
                       current_value=from_scaled_int(r["current_value_paise"], MONEY_PLACES),
                       target_amount=from_scaled_int(r["target_amount_paise"], MONEY_PLACES),
                       percent_complete=from_scaled_int(r["percent_complete_bp"], PERCENT_PLACES))
        for r in rows
    ]
