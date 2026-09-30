"""Startup sequence: apply migrations, then seed demo data when configured."""

import logging
from pathlib import Path

from src.config.clock import Clock
from src.config.settings import Settings
from src.repository.migrations import apply_migrations
from src.service import seed_service
from src.service.context import open_context

log = logging.getLogger(__name__)


def bootstrap(settings: Settings, clock: Clock) -> None:
    with open_context(settings, clock) as ctx:
        applied = apply_migrations(ctx.conn, Path(settings.migrations_dir))
        log.info("migrations_applied", extra={"count": len(applied)})
        if settings.seed_on_start:
            seed_service.seed_if_empty(ctx)
