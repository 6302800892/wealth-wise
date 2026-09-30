"""Customer persistence. Customer rows contain PII; never log their fields (NFR-03)."""

import sqlite3
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerRecord:
    id: str
    full_name: str
    email: str
    date_of_birth: str
    kyc_verified: bool


def _to_customer(row: sqlite3.Row | None) -> CustomerRecord | None:
    if row is None:
        return None
    return CustomerRecord(
        id=row["id"],
        full_name=row["full_name"],
        email=row["email"],
        date_of_birth=row["date_of_birth"],
        kyc_verified=bool(row["kyc_verified"]),
    )


def insert_customer(conn: sqlite3.Connection, *, full_name: str, email: str, date_of_birth: str,
                    kyc_verified: bool, now: str) -> str:
    customer_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO customers (id, full_name, email, date_of_birth, kyc_verified, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (customer_id, full_name, email, date_of_birth, int(kyc_verified), now, now),
    )
    return customer_id


def find_customer(conn: sqlite3.Connection, customer_id: str) -> CustomerRecord | None:
    return _to_customer(conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone())


def list_customers(conn: sqlite3.Connection) -> list[CustomerRecord]:
    rows = conn.execute("SELECT * FROM customers ORDER BY full_name, id").fetchall()
    return [_to_customer(row) for row in rows]


def list_kyc_verified_ids(conn: sqlite3.Connection) -> list[str]:
    return [row[0] for row in conn.execute("SELECT id FROM customers WHERE kyc_verified = 1 ORDER BY id")]
