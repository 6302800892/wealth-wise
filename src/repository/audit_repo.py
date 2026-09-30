"""Append-only audit log (NFR-02). details_json must never contain PII."""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    id: str
    actor_user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    correlation_id: str
    details: dict[str, Any]
    created_at: str


def insert_audit(conn: sqlite3.Connection, *, actor_user_id: str | None, action: str, entity_type: str,
                 entity_id: str, correlation_id: str, details: dict[str, Any], now: str) -> str:
    audit_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO audit_log (id, actor_user_id, action, entity_type, entity_id, correlation_id,"
        " details_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (audit_id, actor_user_id, action, entity_type, entity_id, correlation_id,
         json.dumps(details, sort_keys=True), now),
    )
    return audit_id


def list_for_entities(conn: sqlite3.Connection, entity_ids: list[str]) -> list[AuditRecord]:
    if not entity_ids:
        return []
    marks = ",".join("?" for _ in entity_ids)
    rows = conn.execute(
        f"SELECT * FROM audit_log WHERE entity_id IN ({marks}) ORDER BY created_at DESC, rowid DESC",
        entity_ids,
    ).fetchall()
    return [
        AuditRecord(
            id=r["id"], actor_user_id=r["actor_user_id"], action=r["action"], entity_type=r["entity_type"],
            entity_id=r["entity_id"], correlation_id=r["correlation_id"],
            details=json.loads(r["details_json"]), created_at=r["created_at"],
        )
        for r in rows
    ]
