"""Append-only daily NAV prices (NFR-02). NAV is stored scaled by 10 000."""

import sqlite3
from decimal import Decimal

from src.types.fixed_point import NAV_PLACES, from_scaled_int, to_scaled_int


def latest_nav_date(conn: sqlite3.Connection) -> str | None:
    return conn.execute("SELECT MAX(nav_date) FROM nav_prices").fetchone()[0]


def navs_on(conn: sqlite3.Connection, nav_date: str) -> dict[str, Decimal]:
    rows = conn.execute("SELECT asset_class_code, nav_scaled FROM nav_prices WHERE nav_date = ?", (nav_date,))
    return {r["asset_class_code"]: from_scaled_int(r["nav_scaled"], NAV_PLACES) for r in rows}


def latest_nav_per_class(conn: sqlite3.Connection) -> dict[str, Decimal]:
    """Most recent NAV for each asset class (a class missing on the latest date keeps its last price)."""
    rows = conn.execute(
        "SELECT p.asset_class_code, p.nav_scaled FROM nav_prices p JOIN ("
        " SELECT asset_class_code, MAX(nav_date) AS d FROM nav_prices GROUP BY asset_class_code) m"
        " ON m.asset_class_code = p.asset_class_code AND m.d = p.nav_date"
    )
    return {r["asset_class_code"]: from_scaled_int(r["nav_scaled"], NAV_PLACES) for r in rows}


def insert_navs(conn: sqlite3.Connection, *, nav_date: str, navs: dict[str, Decimal], now: str) -> None:
    conn.executemany(
        "INSERT INTO nav_prices (nav_date, asset_class_code, nav_scaled, created_at) VALUES (?, ?, ?, ?)",
        [(nav_date, code, to_scaled_int(nav, NAV_PLACES), now) for code, nav in navs.items()],
    )
