"""Holdings persistence. Units are stored as integers scaled by 10 000 (NFR-01)."""

import sqlite3
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.types.fixed_point import UNITS_PLACES, from_scaled_int, to_scaled_int


@dataclass(frozen=True)
class HoldingRecord:
    id: str
    customer_id: str
    goal_id: str | None
    asset_class_code: str
    units: Decimal


def _to_holding(row: sqlite3.Row) -> HoldingRecord:
    return HoldingRecord(id=row["id"], customer_id=row["customer_id"], goal_id=row["goal_id"],
                         asset_class_code=row["asset_class_code"],
                         units=from_scaled_int(row["units_scaled"], UNITS_PLACES))


def upsert_holding(conn: sqlite3.Connection, *, customer_id: str, goal_id: str | None, asset_class_code: str,
                   units: Decimal, now: str) -> None:
    scaled = to_scaled_int(units, UNITS_PLACES)
    updated = conn.execute(
        "UPDATE holdings SET units_scaled = ?, updated_at = ? WHERE customer_id = ?"
        " AND COALESCE(goal_id, '') = COALESCE(?, '') AND asset_class_code = ?",
        (scaled, now, customer_id, goal_id, asset_class_code),
    ).rowcount
    if updated == 0:
        conn.execute(
            "INSERT INTO holdings (id, customer_id, goal_id, asset_class_code, units_scaled, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), customer_id, goal_id, asset_class_code, scaled, now, now),
        )


def list_holdings(conn: sqlite3.Connection, customer_id: str) -> list[HoldingRecord]:
    rows = conn.execute(
        "SELECT h.* FROM holdings h JOIN asset_classes a ON a.code = h.asset_class_code WHERE h.customer_id = ?"
        " ORDER BY a.display_order, COALESCE(h.goal_id, '')", (customer_id,),
    ).fetchall()
    return [_to_holding(row) for row in rows]


def list_goal_holdings(conn: sqlite3.Connection, goal_id: str) -> list[HoldingRecord]:
    return [_to_holding(r) for r in conn.execute("SELECT * FROM holdings WHERE goal_id = ?", (goal_id,))]


def customers_with_holdings(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT DISTINCT customer_id FROM holdings WHERE units_scaled > 0 ORDER BY 1")]


def units_by_class(holdings: list[HoldingRecord]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for holding in holdings:
        totals[holding.asset_class_code] = totals.get(holding.asset_class_code, Decimal("0")) + holding.units
    return totals
