"""BR-25: stub daily NAV feed and the NAV refresh cycle (ingest → goal snapshots → rebalancing)."""

import csv
import logging
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.config.clock import Clock
from src.config.settings import Settings
from src.repository import asset_class_repo, nav_repo
from src.repository.db import transaction
from src.service.context import ServiceContext, open_context
from src.types.errors import WealthWiseError
from src.types.fixed_point import NAV_PLACES, parse_fixed, to_wire

log = logging.getLogger(__name__)

CASH_CODE = "CASH"
CASH_NAV = Decimal("1.0000")


def _read_feed(path: str) -> dict[str, dict[str, Decimal]]:
    feed: dict[str, dict[str, Decimal]] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            nav = parse_fixed(row["nav"], NAV_PLACES, "nav")
            feed.setdefault(row["nav_date"], {})[row["asset_class_code"]] = nav
    return feed


def _next_prices(ctx: ServiceContext) -> tuple[str, dict[str, Decimal]]:
    feed = _read_feed(ctx.settings.nav_feed_path)
    latest = nav_repo.latest_nav_date(ctx.conn)
    previous = nav_repo.latest_nav_per_class(ctx.conn)
    upcoming = sorted(d for d in feed if latest is None or d > latest)
    if upcoming:
        return upcoming[0], {**previous, **feed[upcoming[0]]}
    if latest is None:
        raise WealthWiseError("NAV_FEED_EMPTY", "the NAV feed has no prices to ingest")
    return (date.fromisoformat(latest) + timedelta(days=1)).isoformat(), dict(previous)


def ingest_next_day(ctx: ServiceContext) -> str:
    """Ingest the next feed date (or carry prices forward one calendar day when the feed is exhausted)."""
    nav_date, prices = _next_prices(ctx)
    active = [a.code for a in asset_class_repo.list_asset_classes(ctx.conn, active_only=True)]
    if CASH_CODE in active:
        prices[CASH_CODE] = CASH_NAV
    navs = {code: prices[code] for code in active if code in prices}
    with transaction(ctx.conn):
        nav_repo.insert_navs(ctx.conn, nav_date=nav_date, navs=navs, now=ctx.now_iso())
    log.info("nav_ingested", extra={"nav_date": nav_date, "asset_classes": len(navs)})
    return nav_date


def current_nav_map(ctx: ServiceContext) -> dict[str, Decimal]:
    return nav_repo.latest_nav_per_class(ctx.conn)


def latest_navs(ctx: ServiceContext) -> dict[str, Any]:
    return {
        "nav_date": nav_repo.latest_nav_date(ctx.conn),
        "navs": {code: to_wire(nav) for code, nav in current_nav_map(ctx).items()},
    }


def run_refresh_cycle(ctx: ServiceContext) -> dict[str, Any]:
    """One daily refresh (BR-25). Sprint 2 scope: ingest the next NAV day."""
    with transaction(ctx.conn):
        nav_date = ingest_next_day(ctx)
    log.info("nav_refresh_completed", extra={"nav_date": nav_date})
    return {"nav_date": nav_date}


def run_refresh_cycle_standalone(settings: Settings, clock: Clock) -> dict[str, Any]:
    with open_context(settings, clock) as ctx:
        return run_refresh_cycle(ctx)
