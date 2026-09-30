"""Configurable NAV refresh schedule (BR-25). Disabled when the interval is 0."""

import asyncio
import logging

from src.config.clock import Clock
from src.config.settings import Settings

log = logging.getLogger(__name__)


def nav_refresh_loop(settings: Settings, clock: Clock) -> asyncio.Task | None:
    """Start the background refresh task; returns None when scheduling is disabled."""
    if settings.nav_refresh_interval_seconds <= 0:
        return None
    return asyncio.get_running_loop().create_task(_loop(settings, clock))


async def _loop(settings: Settings, clock: Clock) -> None:
    from src.service import nav_service  # local import keeps startup light

    while True:
        await asyncio.sleep(settings.nav_refresh_interval_seconds)
        try:
            await asyncio.to_thread(nav_service.run_refresh_cycle_standalone, settings, clock)
        except Exception as exc:  # the schedule must survive a failed cycle
            log.error("nav_refresh_failed", extra={"exception_type": type(exc).__name__})
