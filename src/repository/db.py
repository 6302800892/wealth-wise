"""SQLite connection handling. This is the only package allowed to import sqlite3."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

Connection = sqlite3.Connection
IntegrityError = sqlite3.IntegrityError


def connect(db_path: str) -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_depth: dict[int, int] = {}


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Commit on success, roll back on any exception. Nested use joins the outermost transaction."""
    key = id(conn)
    depth = _depth.get(key, 0)
    _depth[key] = depth + 1
    try:
        yield conn
        if depth == 0:
            conn.commit()
    except BaseException:
        if depth == 0:
            conn.rollback()
        raise
    finally:
        if depth == 0:
            _depth.pop(key, None)
        else:
            _depth[key] = depth


def ping(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1").fetchone()[0] == 1


def is_constraint_violation(error: Exception) -> bool:
    return isinstance(error, sqlite3.IntegrityError)
