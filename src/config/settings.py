"""Validated application settings loaded from WEALTHWISE_* environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from src.types.fixed_point import PERCENT_PLACES, parse_fixed

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _path(name: str) -> str:
    return str(PROJECT_ROOT / name)


@dataclass(frozen=True)
class Settings:
    db_path: str = _path("data/wealthwise.db")
    migrations_dir: str = _path("migrations")
    seed_dir: str = _path("seed")
    frontend_dist: str = _path("frontend/dist")
    nav_feed_path: str = _path("seed/nav_feed.csv")
    drift_threshold_pct: Decimal = Decimal("5.00")
    nav_refresh_interval_seconds: int = 0
    session_ttl_minutes: int = 60
    log_level: str = "INFO"
    seed_on_start: bool = True
    demo_password: str = "WealthWise@2026"
    password_hash_iterations: int = 120_000
    business_date: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000


def _bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_PARSERS = {
    "WEALTHWISE_DB_PATH": ("db_path", str),
    "WEALTHWISE_DRIFT_THRESHOLD_PCT": (
        "drift_threshold_pct",
        lambda raw: parse_fixed(raw, PERCENT_PLACES, "WEALTHWISE_DRIFT_THRESHOLD_PCT"),
    ),
    "WEALTHWISE_NAV_REFRESH_INTERVAL_SECONDS": ("nav_refresh_interval_seconds", int),
    "WEALTHWISE_SESSION_TTL_MINUTES": ("session_ttl_minutes", int),
    "WEALTHWISE_LOG_LEVEL": ("log_level", str),
    "WEALTHWISE_SEED_ON_START": ("seed_on_start", _bool),
    "WEALTHWISE_DEMO_PASSWORD": ("demo_password", str),
    "WEALTHWISE_BUSINESS_DATE": ("business_date", str),
    "WEALTHWISE_HOST": ("host", str),
    "WEALTHWISE_PORT": ("port", int),
}


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build Settings from the environment; unknown variables are ignored."""
    source = os.environ if env is None else env
    overrides = {}
    for variable, (field, parse) in _PARSERS.items():
        if variable in source and source[variable] != "":
            overrides[field] = parse(source[variable])
    return Settings(**overrides)
