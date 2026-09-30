"""NFR-02: append-only tables reject UPDATE and DELETE at the database level."""

import pytest

from src.repository.db import connect

APPEND_ONLY_TABLES = [
    "audit_log",
    "schema_migrations",
    "risk_assessments",
    "risk_band_assignments",
    "risk_band_overrides",
    "portfolio_recommendations",
    "portfolio_recommendation_lines",
    "nav_prices",
]


@pytest.fixture
def conn(app, settings):
    connection = connect(settings.db_path)
    yield connection
    connection.close()


def _triggers(conn, table):
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND tbl_name = ?", (table,)
    ).fetchall()
    return [row[0].upper() for row in rows]


@pytest.mark.parametrize("table", APPEND_ONLY_TABLES)
def test_table_has_abort_triggers_for_update_and_delete(conn, table):
    triggers = _triggers(conn, table)
    assert any("BEFORE UPDATE" in t and "RAISE(ABORT" in t for t in triggers), f"{table}: no update guard"
    assert any("BEFORE DELETE" in t and "RAISE(ABORT" in t for t in triggers), f"{table}: no delete guard"


def test_audit_log_rejects_update_and_delete(conn):
    conn.execute(
        "INSERT INTO audit_log (id, actor_user_id, action, entity_type, entity_id, correlation_id,"
        " details_json, created_at) VALUES ('a1', NULL, 'TEST', 'test', 'e1', '-', '{}', '2026-09-30T00:00:00Z')"
    )
    with pytest.raises(Exception, match="append-only"):
        conn.execute("UPDATE audit_log SET action = 'X' WHERE id = 'a1'")
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM audit_log WHERE id = 'a1'")
