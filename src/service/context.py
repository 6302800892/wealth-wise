"""Per-use-case service context: one DB connection, settings and the injected clock."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from src.config.clock import Clock, iso_timestamp
from src.config.request_context import get_correlation_id
from src.config.settings import Settings
from src.repository import audit_repo
from src.repository.db import Connection, connect


@dataclass
class ServiceContext:
    conn: Connection
    settings: Settings
    clock: Clock

    def now_iso(self) -> str:
        return iso_timestamp(self.clock.now())

    def audit(self, *, actor_user_id: str | None, action: str, entity_type: str, entity_id: str,
              details: dict[str, Any] | None = None) -> str:
        """Write an audit row. `details` must hold IDs and codes only, never PII (NFR-03)."""
        return audit_repo.insert_audit(
            self.conn, actor_user_id=actor_user_id, action=action, entity_type=entity_type,
            entity_id=entity_id, correlation_id=get_correlation_id(), details=details or {}, now=self.now_iso(),
        )


@contextmanager
def open_context(settings: Settings, clock: Clock) -> Iterator[ServiceContext]:
    conn = connect(settings.db_path)
    try:
        yield ServiceContext(conn=conn, settings=settings, clock=clock)
    finally:
        conn.close()
