"""Users and sessions persistence."""

import sqlite3
import uuid
from dataclasses import dataclass

from src.types.enums import Role


@dataclass(frozen=True)
class UserRecord:
    id: str
    username: str
    password_hash: str
    role: Role
    customer_id: str | None
    display_name: str


def _to_user(row: sqlite3.Row | None) -> UserRecord | None:
    if row is None:
        return None
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        role=Role(row["role"]),
        customer_id=row["customer_id"],
        display_name=row["display_name"],
    )


def insert_user(conn: sqlite3.Connection, *, username: str, password_hash: str, role: Role,
                customer_id: str | None, display_name: str, now: str) -> str:
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (id, username, password_hash, role, customer_id, display_name, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, password_hash, role.value, customer_id, display_name, now, now),
    )
    return user_id


def find_by_username(conn: sqlite3.Connection, username: str) -> UserRecord | None:
    return _to_user(conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone())


def find_by_id(conn: sqlite3.Connection, user_id: str) -> UserRecord | None:
    return _to_user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def count_users(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def insert_session(conn: sqlite3.Connection, *, token_hash: str, user_id: str, expires_at: str, now: str) -> None:
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (token_hash, user_id, expires_at, now),
    )


def find_session_user(conn: sqlite3.Connection, token_hash: str, now: str) -> UserRecord | None:
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires_at > ?",
        (token_hash, now),
    ).fetchone()
    return _to_user(row)


def delete_session(conn: sqlite3.Connection, token_hash: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
