"""BR-25: NAV feed stub — sequential daily ingestion, CASH fixed at 1.0000, carry-forward when exhausted."""

import dataclasses
from decimal import Decimal

import pytest

from src.config.clock import FixedClock
from src.main import create_app
from src.service import nav_service
from src.service.context import open_context
from tests.conftest import TEST_DATE

FEED = """nav_date,asset_class_code,nav
2026-09-30,EQUITY,150.0000
2026-09-30,DEBT,25.0000
2026-09-30,GOLD,50.0000
2026-10-01,EQUITY,153.0000
2026-10-01,DEBT,25.1000
"""


@pytest.fixture
def feed_settings(settings, tmp_path):
    feed = tmp_path / "feed.csv"
    feed.write_text(FEED)
    configured = dataclasses.replace(settings, nav_feed_path=str(feed))
    create_app(settings=configured, clock=FixedClock(TEST_DATE))
    return configured


@pytest.fixture
def ctx(feed_settings):
    with open_context(feed_settings, FixedClock(TEST_DATE)) as context:
        yield context


def test_seed_ingests_first_feed_day_with_cash_fixed(ctx):
    latest = nav_service.latest_navs(ctx)
    assert latest["nav_date"] == "2026-09-30"
    assert latest["navs"] == {"EQUITY": "150.0000", "DEBT": "25.0000", "GOLD": "50.0000", "CASH": "1.0000"}


def test_refresh_ingests_next_day_and_carries_missing_classes(ctx):
    nav_date = nav_service.ingest_next_day(ctx)
    assert nav_date == "2026-10-01"
    navs = nav_service.latest_navs(ctx)["navs"]
    assert navs["EQUITY"] == "153.0000"
    assert navs["GOLD"] == "50.0000"  # not in feed for that day → carried forward
    assert navs["CASH"] == "1.0000"


def test_exhausted_feed_carries_forward_to_next_calendar_day(ctx):
    nav_service.ingest_next_day(ctx)
    assert nav_service.ingest_next_day(ctx) == "2026-10-02"
    assert nav_service.latest_navs(ctx)["navs"]["EQUITY"] == "153.0000"


def test_nav_values_are_decimals(ctx):
    navs = nav_service.current_nav_map(ctx)
    assert navs["DEBT"] == Decimal("25.0000")
