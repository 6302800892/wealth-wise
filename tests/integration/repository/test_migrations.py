"""NFR-05: migrations are append-only and tamper-evident."""

import shutil

import pytest

from src.config.settings import PROJECT_ROOT
from src.repository.db import connect
from src.repository.migrations import apply_migrations
from src.types.errors import MigrationIntegrityError

MIGRATIONS = PROJECT_ROOT / "migrations"


def test_migrations_apply_once_and_are_idempotent(tmp_path):
    conn = connect(str(tmp_path / "m.db"))
    first = apply_migrations(conn, MIGRATIONS)
    second = apply_migrations(conn, MIGRATIONS)
    assert first, "expected at least one migration to apply"
    assert second == []
    recorded = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert recorded == len(first)


def test_modified_applied_migration_blocks_startup(tmp_path):
    local = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, local)
    conn = connect(str(tmp_path / "m.db"))
    apply_migrations(conn, local)
    first_file = sorted(local.glob("*.sql"))[0]
    first_file.write_text(first_file.read_text() + "\n-- tampered\n")
    with pytest.raises(MigrationIntegrityError):
        apply_migrations(conn, local)


def test_deleted_applied_migration_blocks_startup(tmp_path):
    local = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS, local)
    conn = connect(str(tmp_path / "m.db"))
    apply_migrations(conn, local)
    sorted(local.glob("*.sql"))[-1].unlink()
    with pytest.raises(MigrationIntegrityError):
        apply_migrations(conn, local)


def test_schema_migrations_is_append_only(tmp_path):
    conn = connect(str(tmp_path / "m.db"))
    apply_migrations(conn, MIGRATIONS)
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM schema_migrations")
