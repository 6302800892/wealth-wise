"""Append-only, checksum-verified migration runner (NFR-05)."""

import hashlib
import re
import sqlite3
from pathlib import Path

from src.types.errors import MigrationIntegrityError

_FILENAME = re.compile(r"^\d{4}_[a-z0-9_]+\.sql$")

_BOOTSTRAP = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    checksum_sha256 TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TRIGGER IF NOT EXISTS trg_schema_migrations_no_update BEFORE UPDATE ON schema_migrations
BEGIN SELECT RAISE(ABORT, 'append-only table: schema_migrations'); END;
CREATE TRIGGER IF NOT EXISTS trg_schema_migrations_no_delete BEFORE DELETE ON schema_migrations
BEGIN SELECT RAISE(ABORT, 'append-only table: schema_migrations'); END;
"""


def _checksum(path: Path) -> str:
    # Normalise line endings so a git checkout on Windows yields the same checksum as Linux CI.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _migration_files(migrations_dir: Path) -> list[Path]:
    files = sorted(p for p in migrations_dir.glob("*.sql"))
    bad = [p.name for p in files if not _FILENAME.match(p.name)]
    if bad:
        raise MigrationIntegrityError(f"invalid migration file names: {bad}")
    return files


def _verify_applied(applied: dict[str, str], files: dict[str, str]) -> None:
    for filename, checksum in applied.items():
        if filename not in files:
            raise MigrationIntegrityError(f"applied migration {filename} was deleted")
        if files[filename] != checksum:
            raise MigrationIntegrityError(f"applied migration {filename} was modified")


def apply_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> list[str]:
    """Apply pending migrations in order and return the names applied in this call."""
    conn.executescript(_BOOTSTRAP)
    applied = {row[0]: row[1] for row in conn.execute("SELECT filename, checksum_sha256 FROM schema_migrations")}
    paths = _migration_files(Path(migrations_dir))
    checksums = {p.name: _checksum(p) for p in paths}
    _verify_applied(applied, checksums)
    newly_applied = []
    for path in paths:
        if path.name in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        record = f"INSERT INTO schema_migrations (filename, checksum_sha256) VALUES ('{path.name}', '{checksums[path.name]}');"
        conn.executescript(f"BEGIN;\n{sql}\n{record}\nCOMMIT;")
        newly_applied.append(path.name)
    return newly_applied
