"""Append-only portfolio recommendations and their allocation lines (NFR-02)."""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.types.enums import HorizonBucket, RiskBand
from src.types.fixed_point import PERCENT_PLACES, from_scaled_int, to_scaled_int


@dataclass(frozen=True)
class RecommendationRecord:
    id: str
    customer_id: str
    goal_id: str
    risk_band_assignment_id: str
    risk_band: RiskBand
    horizon_bucket: HorizonBucket
    template_version: int
    as_of_date: date
    input_fingerprint: str
    created_at: str
    allocation: dict[str, Decimal]


def insert_recommendation(conn: sqlite3.Connection, *, customer_id: str, goal_id: str, assignment_id: str,
                          band: RiskBand, horizon: HorizonBucket, template_version: int, as_of: date,
                          fingerprint: str, allocation: dict[str, Decimal], now: str) -> str:
    recommendation_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO portfolio_recommendations (id, customer_id, goal_id, risk_band_assignment_id, risk_band,"
        " horizon_bucket, template_version, as_of_date, input_fingerprint, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (recommendation_id, customer_id, goal_id, assignment_id, band.value, horizon.value, template_version,
         as_of.isoformat(), fingerprint, now),
    )
    conn.executemany(
        "INSERT INTO portfolio_recommendation_lines (recommendation_id, asset_class_code, target_bp)"
        " VALUES (?, ?, ?)",
        [(recommendation_id, code, to_scaled_int(pct, PERCENT_PLACES)) for code, pct in allocation.items()],
    )
    return recommendation_id


def _allocation(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Decimal]:
    rows = conn.execute(
        "SELECT l.asset_class_code, l.target_bp FROM portfolio_recommendation_lines l"
        " JOIN asset_classes a ON a.code = l.asset_class_code WHERE l.recommendation_id = ?"
        " ORDER BY a.display_order, a.code", (recommendation_id,),
    ).fetchall()
    return {r["asset_class_code"]: from_scaled_int(r["target_bp"], PERCENT_PLACES) for r in rows}


def _to_record(conn: sqlite3.Connection, row: sqlite3.Row) -> RecommendationRecord:
    return RecommendationRecord(
        id=row["id"], customer_id=row["customer_id"], goal_id=row["goal_id"],
        risk_band_assignment_id=row["risk_band_assignment_id"], risk_band=RiskBand(row["risk_band"]),
        horizon_bucket=HorizonBucket(row["horizon_bucket"]), template_version=row["template_version"],
        as_of_date=date.fromisoformat(row["as_of_date"]), input_fingerprint=row["input_fingerprint"],
        created_at=row["created_at"], allocation=_allocation(conn, row["id"]),
    )


def latest_for_customer(conn: sqlite3.Connection, customer_id: str) -> RecommendationRecord | None:
    row = conn.execute(
        "SELECT * FROM portfolio_recommendations WHERE customer_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (customer_id,),
    ).fetchone()
    return None if row is None else _to_record(conn, row)


def customers_with_recommendations(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT DISTINCT customer_id FROM portfolio_recommendations ORDER BY 1")]
