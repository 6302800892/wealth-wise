"""Append-only risk assessments, advisor overrides and band assignments (NFR-02)."""

import json
import sqlite3
import uuid
from dataclasses import dataclass

from src.types.enums import BandSource, OverrideReason, RiskBand


@dataclass(frozen=True)
class AssignmentRecord:
    id: str
    customer_id: str
    risk_band: RiskBand
    source: BandSource
    assessment_id: str | None
    override_id: str | None
    rule_set_version: int | None
    assigned_by: str
    assigned_at: str


@dataclass(frozen=True)
class OverrideRecord:
    id: str
    customer_id: str
    previous_band: RiskBand | None
    new_band: RiskBand
    reason_code: OverrideReason
    note: str
    actor_user_id: str
    created_at: str


def insert_assessment(conn: sqlite3.Connection, *, customer_id: str, rule_set_version: int,
                      answers: list[tuple[str, str]], total_score: int, band: RiskBand, now: str) -> str:
    assessment_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO risk_assessments (id, customer_id, rule_set_version, answers_json, total_score,"
        " computed_band, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (assessment_id, customer_id, rule_set_version, json.dumps(answers), total_score, band.value, now),
    )
    return assessment_id


def insert_override(conn: sqlite3.Connection, *, customer_id: str, previous_band: RiskBand | None,
                    new_band: RiskBand, reason: OverrideReason, note: str, actor: str, now: str) -> str:
    override_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO risk_band_overrides (id, customer_id, previous_band, new_band, reason_code, note,"
        " actor_user_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (override_id, customer_id, previous_band.value if previous_band else None, new_band.value,
         reason.value, note, actor, now),
    )
    return override_id


def insert_assignment(conn: sqlite3.Connection, *, customer_id: str, band: RiskBand, source: BandSource,
                      assessment_id: str | None, override_id: str | None, rule_set_version: int | None,
                      assigned_by: str, now: str) -> str:
    assignment_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO risk_band_assignments (id, customer_id, risk_band, source, assessment_id, override_id,"
        " rule_set_version, assigned_by, assigned_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (assignment_id, customer_id, band.value, source.value, assessment_id, override_id,
         rule_set_version, assigned_by, now),
    )
    return assignment_id


def latest_assignment(conn: sqlite3.Connection, customer_id: str) -> AssignmentRecord | None:
    row = conn.execute(
        "SELECT * FROM risk_band_assignments WHERE customer_id = ? ORDER BY assigned_at DESC, rowid DESC LIMIT 1",
        (customer_id,),
    ).fetchone()
    if row is None:
        return None
    return AssignmentRecord(
        id=row["id"], customer_id=row["customer_id"], risk_band=RiskBand(row["risk_band"]),
        source=BandSource(row["source"]), assessment_id=row["assessment_id"], override_id=row["override_id"],
        rule_set_version=row["rule_set_version"], assigned_by=row["assigned_by"], assigned_at=row["assigned_at"],
    )


def list_overrides(conn: sqlite3.Connection, customer_id: str) -> list[OverrideRecord]:
    rows = conn.execute(
        "SELECT * FROM risk_band_overrides WHERE customer_id = ? ORDER BY created_at DESC, rowid DESC",
        (customer_id,),
    ).fetchall()
    return [
        OverrideRecord(
            id=r["id"], customer_id=r["customer_id"],
            previous_band=RiskBand(r["previous_band"]) if r["previous_band"] else None,
            new_band=RiskBand(r["new_band"]), reason_code=OverrideReason(r["reason_code"]), note=r["note"],
            actor_user_id=r["actor_user_id"], created_at=r["created_at"],
        )
        for r in rows
    ]
