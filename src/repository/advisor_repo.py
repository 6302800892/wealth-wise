"""Advisor manual recommendations (append-only) and template usage lookups."""

import sqlite3
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ManualRecommendationRecord:
    id: str
    customer_id: str
    advisor_user_id: str
    note: str
    created_at: str


def insert_manual_recommendation(conn: sqlite3.Connection, *, customer_id: str, advisor_user_id: str,
                                 note: str, now: str) -> str:
    record_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO manual_recommendations (id, customer_id, advisor_user_id, note, created_at)"
        " VALUES (?, ?, ?, ?, ?)", (record_id, customer_id, advisor_user_id, note, now))
    return record_id


def list_manual_recommendations(conn: sqlite3.Connection, customer_id: str) -> list[ManualRecommendationRecord]:
    rows = conn.execute("SELECT * FROM manual_recommendations WHERE customer_id = ?"
                        " ORDER BY created_at DESC, rowid DESC", (customer_id,)).fetchall()
    return [ManualRecommendationRecord(id=r["id"], customer_id=r["customer_id"], advisor_user_id=r["advisor_user_id"],
                                       note=r["note"], created_at=r["created_at"]) for r in rows]


def asset_class_in_template(conn: sqlite3.Connection, code: str, template_version: int) -> bool:
    row = conn.execute("SELECT 1 FROM allocation_template_rows WHERE asset_class_code = ? AND template_version = ?"
                       " AND target_bp > 0 LIMIT 1", (code, template_version)).fetchone()
    return row is not None
