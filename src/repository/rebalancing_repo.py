"""Append-only rebalancing proposals, lines, decisions and stub orders (NFR-02)."""

import sqlite3
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.types.enums import RebalancingStatus, StubOrderStatus, TradeAction
from src.types.errors import WealthWiseError
from src.types.fixed_point import MONEY_PLACES, PERCENT_PLACES, UNITS_PLACES, from_scaled_int, to_scaled_int
from src.types.portfolio import RebalanceLine


@dataclass(frozen=True)
class DecisionRecord:
    status: RebalancingStatus
    reason: str | None
    actor_user_id: str | None
    decided_at: str


@dataclass(frozen=True)
class StubOrderRecord:
    id: str
    asset_class_code: str
    action: TradeAction
    units: Decimal
    status: StubOrderStatus
    created_at: str


@dataclass(frozen=True)
class RebalancingRecord:
    id: str
    customer_id: str
    portfolio_recommendation_id: str
    template_version: int
    nav_date: str
    threshold_pct: Decimal
    total_value: Decimal
    max_drift_pct: Decimal
    created_at: str
    lines: tuple[RebalanceLine, ...]
    decision: DecisionRecord | None
    orders: tuple[StubOrderRecord, ...]

    @property
    def status(self) -> RebalancingStatus:
        return self.decision.status if self.decision else RebalancingStatus.OPEN


def _pct(raw: int) -> Decimal:
    return from_scaled_int(raw, PERCENT_PLACES)


def insert_rebalancing(conn: sqlite3.Connection, *, customer_id: str, portfolio_recommendation_id: str,
                       template_version: int, nav_date: str, threshold: Decimal, total_value: Decimal,
                       max_drift: Decimal, lines: list[RebalanceLine], now: str) -> str:
    rebalancing_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO rebalancing_recommendations (id, customer_id, portfolio_recommendation_id, template_version,"
        " nav_date, threshold_bp, total_value_paise, max_drift_bp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (rebalancing_id, customer_id, portfolio_recommendation_id, template_version, nav_date,
         to_scaled_int(threshold, PERCENT_PLACES), to_scaled_int(total_value, MONEY_PLACES),
         to_scaled_int(max_drift, PERCENT_PLACES), now),
    )
    conn.executemany(
        "INSERT INTO rebalancing_lines (rebalancing_id, asset_class_code, current_bp, target_bp, drift_bp, action,"
        " units_scaled, trade_value_paise) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(rebalancing_id, ln.asset_class_code, to_scaled_int(ln.current_pct, PERCENT_PLACES),
          to_scaled_int(ln.target_pct, PERCENT_PLACES), to_scaled_int(ln.drift_pct, PERCENT_PLACES),
          ln.action.value, to_scaled_int(ln.units, UNITS_PLACES), to_scaled_int(ln.trade_value, MONEY_PLACES))
         for ln in lines],
    )
    return rebalancing_id


def insert_decision(conn: sqlite3.Connection, *, rebalancing_id: str, status: RebalancingStatus,
                    reason: str | None, actor_user_id: str | None, now: str) -> None:
    try:
        conn.execute(
            "INSERT INTO rebalancing_decisions (id, rebalancing_id, status, reason, actor_user_id, decided_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), rebalancing_id, status.value, reason, actor_user_id, now),
        )
    except sqlite3.IntegrityError as error:
        raise WealthWiseError("RECOMMENDATION_NOT_OPEN", "recommendation already has a decision") from error


def insert_stub_orders(conn: sqlite3.Connection, *, rebalancing_id: str, lines: tuple[RebalanceLine, ...],
                       now: str) -> int:
    orders = [ln for ln in lines if ln.action is not TradeAction.HOLD]
    conn.executemany(
        "INSERT INTO stub_orders (id, rebalancing_id, asset_class_code, action, units_scaled, status, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(str(uuid.uuid4()), rebalancing_id, ln.asset_class_code, ln.action.value,
          to_scaled_int(ln.units, UNITS_PLACES), StubOrderStatus.STUB_SUBMITTED.value, now) for ln in orders],
    )
    return len(orders)


def _lines(conn: sqlite3.Connection, rebalancing_id: str) -> tuple[RebalanceLine, ...]:
    rows = conn.execute(
        "SELECT l.* FROM rebalancing_lines l JOIN asset_classes a ON a.code = l.asset_class_code"
        " WHERE l.rebalancing_id = ? ORDER BY a.display_order, a.code", (rebalancing_id,))
    return tuple(
        RebalanceLine(asset_class_code=r["asset_class_code"], current_pct=_pct(r["current_bp"]),
                      target_pct=_pct(r["target_bp"]), drift_pct=_pct(r["drift_bp"]), action=TradeAction(r["action"]),
                      units=from_scaled_int(r["units_scaled"], UNITS_PLACES),
                      trade_value=from_scaled_int(r["trade_value_paise"], MONEY_PLACES))
        for r in rows
    )


def _decision(conn: sqlite3.Connection, rebalancing_id: str) -> DecisionRecord | None:
    r = conn.execute("SELECT * FROM rebalancing_decisions WHERE rebalancing_id = ?", (rebalancing_id,)).fetchone()
    if r is None:
        return None
    return DecisionRecord(status=RebalancingStatus(r["status"]), reason=r["reason"],
                          actor_user_id=r["actor_user_id"], decided_at=r["decided_at"])


def _orders(conn: sqlite3.Connection, rebalancing_id: str) -> tuple[StubOrderRecord, ...]:
    rows = conn.execute("SELECT * FROM stub_orders WHERE rebalancing_id = ? ORDER BY rowid", (rebalancing_id,))
    return tuple(StubOrderRecord(id=r["id"], asset_class_code=r["asset_class_code"], action=TradeAction(r["action"]),
                                 units=from_scaled_int(r["units_scaled"], UNITS_PLACES),
                                 status=StubOrderStatus(r["status"]), created_at=r["created_at"]) for r in rows)


def _to_record(conn: sqlite3.Connection, r: sqlite3.Row) -> RebalancingRecord:
    return RebalancingRecord(
        id=r["id"], customer_id=r["customer_id"], portfolio_recommendation_id=r["portfolio_recommendation_id"],
        template_version=r["template_version"], nav_date=r["nav_date"], threshold_pct=_pct(r["threshold_bp"]),
        total_value=from_scaled_int(r["total_value_paise"], MONEY_PLACES), max_drift_pct=_pct(r["max_drift_bp"]),
        created_at=r["created_at"], lines=_lines(conn, r["id"]), decision=_decision(conn, r["id"]),
        orders=_orders(conn, r["id"]),
    )


def find_rebalancing(conn: sqlite3.Connection, rebalancing_id: str) -> RebalancingRecord | None:
    row = conn.execute("SELECT * FROM rebalancing_recommendations WHERE id = ?", (rebalancing_id,)).fetchone()
    return None if row is None else _to_record(conn, row)


def list_for_customer(conn: sqlite3.Connection, customer_id: str) -> list[RebalancingRecord]:
    rows = conn.execute("SELECT * FROM rebalancing_recommendations WHERE customer_id = ?"
                        " ORDER BY created_at DESC, rowid DESC", (customer_id,)).fetchall()
    return [_to_record(conn, row) for row in rows]


def open_ids_for_customer(conn: sqlite3.Connection, customer_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT r.id FROM rebalancing_recommendations r LEFT JOIN rebalancing_decisions d ON d.rebalancing_id = r.id"
        " WHERE r.customer_id = ? AND d.id IS NULL ORDER BY r.rowid", (customer_id,))
    return [row[0] for row in rows]
