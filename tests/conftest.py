"""Shared pytest fixtures: isolated SQLite DB, fixed clock, app and authenticated clients."""

from collections.abc import Callable, Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.config.clock import FixedClock
from src.config.settings import Settings
from src.main import create_app

TEST_DATE = date(2026, 9, 30)
TEST_PASSWORD = "Test-Only-Password-1"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        db_path=str(tmp_path / "wealthwise-test.db"),
        demo_password=TEST_PASSWORD,
        password_hash_iterations=1_000,
        nav_refresh_interval_seconds=0,
        nav_state_path=str(tmp_path / "nav-state.json"),
    )


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(TEST_DATE)


@pytest.fixture
def app(settings: Settings, clock: FixedClock):
    return create_app(settings=settings, clock=clock)


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str = TEST_PASSWORD) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def auth(client: TestClient) -> Callable[[str], dict[str, str]]:
    """Return a function that logs a seeded user in and returns auth headers."""
    return lambda username: login(client, username)
