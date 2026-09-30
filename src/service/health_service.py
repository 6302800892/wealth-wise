"""Health check (NFR-07): a cheap DB round-trip only."""

from src.repository.db import ping
from src.service.context import ServiceContext


def check(ctx: ServiceContext) -> dict[str, str]:
    return {"status": "ok", "db": "ok" if ping(ctx.conn) else "error"}
