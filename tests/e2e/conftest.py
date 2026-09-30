"""E2E fixtures: a real WealthWise server (fresh SQLite DB per module) and browser contexts per viewport."""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "WealthWise@2026"
VIEWPORTS = {"desktop": {"width": 1280, "height": 800}, "mobile": {"width": 375, "height": 812}}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_healthy(url: str, process: subprocess.Popen) -> None:
    for _ in range(80):
        if process.poll() is not None:
            raise RuntimeError("server exited during startup")
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("server did not become healthy")


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    if not (ROOT / "frontend" / "dist" / "index.html").is_file():
        pytest.skip("frontend not built: run `npm --prefix frontend run build` first")
    port = _free_port()
    env = {**os.environ, "WEALTHWISE_DB_PATH": str(tmp_path_factory.mktemp("e2e") / "e2e.db"),
           "WEALTHWISE_PORT": str(port), "WEALTHWISE_BUSINESS_DATE": "2026-09-30",
           "WEALTHWISE_LOG_LEVEL": "WARNING"}
    process = subprocess.Popen([sys.executable, "-m", "src.main"], cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_healthy(url, process)
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(params=list(VIEWPORTS), ids=list(VIEWPORTS))
def viewport(request) -> str:
    return request.param


@pytest.fixture
def ui(browser, server_url, viewport):
    """A logged-out page at the chosen viewport; `ui.login(username)` signs in through the real form."""
    context = browser.new_context(viewport=VIEWPORTS[viewport], base_url=server_url)
    page = context.new_page()
    page.viewport_name = viewport

    def login(username: str) -> None:
        page.goto("/#/login")
        page.get_by_test_id("login-username").fill(username)
        page.get_by_test_id("login-password").fill(PASSWORD)
        page.get_by_test_id("login-submit").click()
        page.get_by_test_id("logout").wait_for(state="attached")

    page.login = login
    yield page
    context.close()
