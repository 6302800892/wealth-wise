"""Snapshot helpers. ARIA snapshots are the asserted baseline; PNG screenshots are committed visual evidence.

Set UPDATE_SNAPSHOTS=1 to rewrite baselines deliberately (spec-is-truth: review the diff before committing).
"""

import os
from pathlib import Path

from playwright.sync_api import Locator, Page, expect

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SCREENSHOT_DIR = SNAPSHOT_DIR / "screenshots"


def check_aria(locator: Locator, name: str) -> None:
    path = SNAPSHOT_DIR / f"{name}.aria.yml"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1" or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(locator.aria_snapshot() + "\n", encoding="utf-8")
    expect(locator).to_match_aria_snapshot(path.read_text(encoding="utf-8"))


def screenshot(page: Page, name: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOT_DIR / f"{name}-{page.viewport_name}.png"), full_page=True)
