"""Asset-class master data."""

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class AssetClassRecord:
    code: str
    name: str
    display_order: int
    is_active: bool


def _to_asset_class(row: sqlite3.Row) -> AssetClassRecord:
    return AssetClassRecord(
        code=row["code"], name=row["name"], display_order=row["display_order"], is_active=bool(row["is_active"])
    )


def list_asset_classes(conn: sqlite3.Connection, *, active_only: bool = False) -> list[AssetClassRecord]:
    sql = "SELECT * FROM asset_classes"
    if active_only:
        sql += " WHERE is_active = 1"
    rows = conn.execute(sql + " ORDER BY display_order, code").fetchall()
    return [_to_asset_class(row) for row in rows]


def find_asset_class(conn: sqlite3.Connection, code: str) -> AssetClassRecord | None:
    row = conn.execute("SELECT * FROM asset_classes WHERE code = ?", (code,)).fetchone()
    return None if row is None else _to_asset_class(row)


def insert_asset_class(conn: sqlite3.Connection, *, code: str, name: str, display_order: int, now: str) -> None:
    conn.execute(
        "INSERT INTO asset_classes (code, name, display_order, is_active, created_at, updated_at)"
        " VALUES (?, ?, ?, 1, ?, ?)",
        (code, name, display_order, now, now),
    )


def update_asset_class(conn: sqlite3.Connection, *, code: str, name: str, display_order: int,
                       is_active: bool, now: str) -> None:
    conn.execute(
        "UPDATE asset_classes SET name = ?, display_order = ?, is_active = ?, updated_at = ? WHERE code = ?",
        (name, display_order, int(is_active), now, code),
    )


def display_order_codes(conn: sqlite3.Connection) -> list[str]:
    return [row[0] for row in conn.execute("SELECT code FROM asset_classes ORDER BY display_order, code")]
