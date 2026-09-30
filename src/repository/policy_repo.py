"""Versioned rule sets and allocation template sets. Published versions are immutable (DB triggers)."""

import json
import sqlite3
from dataclasses import dataclass
from decimal import Decimal

from src.types.enums import HorizonBucket, RiskBand, VersionStatus
from src.types.fixed_point import PERCENT_PLACES, from_scaled_int, to_scaled_int
from src.types.policy import RuleSet, TemplateRows, TemplateSet, rule_set_from_definition


@dataclass(frozen=True)
class VersionMeta:
    version: int
    status: VersionStatus
    created_by: str | None
    created_at: str
    published_by: str | None
    published_at: str | None


def _meta(row: sqlite3.Row) -> VersionMeta:
    return VersionMeta(
        version=row["version"], status=VersionStatus(row["status"]), created_by=row["created_by"],
        created_at=row["created_at"], published_by=row["published_by"], published_at=row["published_at"],
    )


# ---- risk rule sets -------------------------------------------------------------------------

def active_rule_set_version(conn: sqlite3.Connection) -> int | None:
    return conn.execute("SELECT MAX(version) FROM risk_rule_set_versions WHERE status = 'PUBLISHED'").fetchone()[0]


def get_rule_set(conn: sqlite3.Connection, version: int) -> tuple[VersionMeta, RuleSet] | None:
    row = conn.execute("SELECT * FROM risk_rule_set_versions WHERE version = ?", (version,)).fetchone()
    if row is None:
        return None
    return _meta(row), rule_set_from_definition(version, json.loads(row["definition_json"]))


def list_rule_set_versions(conn: sqlite3.Connection) -> list[VersionMeta]:
    return [_meta(r) for r in conn.execute("SELECT * FROM risk_rule_set_versions ORDER BY version DESC")]


def insert_rule_set_draft(conn: sqlite3.Connection, *, version: int, definition: dict, actor: str, now: str) -> None:
    conn.execute(
        "INSERT INTO risk_rule_set_versions (version, status, definition_json, created_by, created_at)"
        " VALUES (?, 'DRAFT', ?, ?, ?)",
        (version, json.dumps(definition, sort_keys=True), actor, now),
    )


def update_rule_set_draft(conn: sqlite3.Connection, *, version: int, definition: dict) -> None:
    conn.execute("UPDATE risk_rule_set_versions SET definition_json = ? WHERE version = ? AND status = 'DRAFT'",
                 (json.dumps(definition, sort_keys=True), version))


def publish_rule_set(conn: sqlite3.Connection, *, version: int, actor: str, now: str) -> None:
    conn.execute("UPDATE risk_rule_set_versions SET status = 'PUBLISHED', published_by = ?, published_at = ?"
                 " WHERE version = ? AND status = 'DRAFT'", (actor, now, version))


def next_rule_set_version(conn: sqlite3.Connection) -> int:
    return (conn.execute("SELECT MAX(version) FROM risk_rule_set_versions").fetchone()[0] or 0) + 1


# ---- allocation template sets ---------------------------------------------------------------

def active_template_version(conn: sqlite3.Connection) -> int | None:
    return conn.execute(
        "SELECT MAX(version) FROM allocation_template_set_versions WHERE status = 'PUBLISHED'").fetchone()[0]


def get_template_meta(conn: sqlite3.Connection, version: int) -> VersionMeta | None:
    row = conn.execute("SELECT * FROM allocation_template_set_versions WHERE version = ?", (version,)).fetchone()
    return None if row is None else _meta(row)


def get_template_set(conn: sqlite3.Connection, version: int) -> TemplateSet | None:
    if get_template_meta(conn, version) is None:
        return None
    rows: dict[tuple[RiskBand, HorizonBucket], dict[str, Decimal]] = {}
    for r in conn.execute(
        "SELECT r.* FROM allocation_template_rows r JOIN asset_classes a ON a.code = r.asset_class_code"
        " WHERE r.template_version = ? ORDER BY a.display_order, a.code", (version,)
    ):
        key = (RiskBand(r["risk_band"]), HorizonBucket(r["horizon_bucket"]))
        rows.setdefault(key, {})[r["asset_class_code"]] = from_scaled_int(r["target_bp"], PERCENT_PLACES)
    return TemplateSet(version=version, rows=rows)


def list_template_versions(conn: sqlite3.Connection) -> list[VersionMeta]:
    return [_meta(r) for r in conn.execute("SELECT * FROM allocation_template_set_versions ORDER BY version DESC")]


def next_template_version(conn: sqlite3.Connection) -> int:
    return (conn.execute("SELECT MAX(version) FROM allocation_template_set_versions").fetchone()[0] or 0) + 1


def insert_template_draft(conn: sqlite3.Connection, *, version: int, actor: str, now: str) -> None:
    conn.execute("INSERT INTO allocation_template_set_versions (version, status, created_by, created_at)"
                 " VALUES (?, 'DRAFT', ?, ?)", (version, actor, now))


def replace_template_rows(conn: sqlite3.Connection, *, version: int, rows: TemplateRows) -> None:
    conn.execute("DELETE FROM allocation_template_rows WHERE template_version = ?", (version,))
    conn.executemany(
        "INSERT INTO allocation_template_rows (template_version, risk_band, horizon_bucket, asset_class_code,"
        " target_bp) VALUES (?, ?, ?, ?, ?)",
        [(version, band.value, horizon.value, code, to_scaled_int(pct, PERCENT_PLACES))
         for (band, horizon), row in rows.items() for code, pct in row.items()],
    )


def publish_template(conn: sqlite3.Connection, *, version: int, actor: str, now: str) -> None:
    conn.execute("UPDATE allocation_template_set_versions SET status = 'PUBLISHED', published_by = ?,"
                 " published_at = ? WHERE version = ? AND status = 'DRAFT'", (actor, now, version))
