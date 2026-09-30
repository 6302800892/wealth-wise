"""E2E — advisor override (AC-09) and admin template versioning (AC-02, AC-10)."""

import pytest
from playwright.sync_api import expect

from tests.e2e.snapshots import screenshot

pytestmark = pytest.mark.e2e


@pytest.mark.ac("AC-09")
def test_advisor_overrides_band_with_audit(ui):
    """AC-09: the advisor overrides alpha to a new band with a note; the audit trail records it."""
    target = "CONSERVATIVE" if ui.viewport_name == "desktop" else "AGGRESSIVE"
    ui.login("advisor.one")
    ui.get_by_test_id("customer-link").filter(has_text="Aarav Alpha").click()
    expect(ui.get_by_test_id("customer-name")).to_have_text("Aarav Alpha")
    ui.get_by_test_id("override-band").select_option(target)
    ui.get_by_test_id("override-reason").select_option("CHANGE_IN_CIRCUMSTANCES")
    ui.get_by_test_id("override-note").fill(f"E2E override on {ui.viewport_name}")
    ui.get_by_test_id("override-submit").click()
    table = ui.get_by_test_id("override-table")
    expect(table).to_contain_text(f"→ {target}")
    expect(table).to_contain_text(f"E2E override on {ui.viewport_name}")
    screenshot(ui, "advisor-override")


@pytest.mark.ac("AC-02")
@pytest.mark.ac("AC-10")
def test_admin_cannot_publish_bad_template_then_publishes_fixed_one(ui):
    """AC-02.2 / AC-10.1: a 99.00 row blocks publishing; fixing it to 100.00 publishes a new version."""
    if ui.viewport_name == "mobile":
        pytest.skip("template editor journey runs once, on desktop (versions are global state)")
    ui.login("admin.one")
    ui.goto("/#/admin/templates")
    ui.get_by_test_id("create-draft").click()
    cell = ui.get_by_test_id("cell-MODERATE-MEDIUM-CASH")
    cell.fill("4.00")
    expect(ui.get_by_test_id("sum-MODERATE-MEDIUM")).to_have_text("99.00")
    ui.get_by_test_id("save-draft").click()
    expect(ui.get_by_test_id("template-message")).to_have_text("Draft saved")
    ui.get_by_test_id("publish-draft").click()
    expect(ui.get_by_test_id("error-notice")).to_contain_text("ALLOCATION_SUM_INVALID")
    screenshot(ui, "admin-template-invalid")
    ui.get_by_test_id("cell-MODERATE-MEDIUM-CASH").fill("5.00")
    expect(ui.get_by_test_id("sum-MODERATE-MEDIUM")).to_have_text("100.00")
    ui.get_by_test_id("save-draft").click()
    expect(ui.get_by_test_id("template-message")).to_have_text("Draft saved")
    ui.get_by_test_id("publish-draft").click()
    expect(ui.get_by_test_id("template-message")).to_have_text("Published v2")
    expect(ui.get_by_test_id("template-versions")).to_contain_text("PUBLISHED")


@pytest.mark.ac("AC-08")
def test_admin_runs_nav_refresh(ui):
    """AC-08: running the daily refresh ingests the next NAV day and snapshots goals."""
    ui.login("admin.one")
    ui.goto("/#/admin/nav")
    ui.get_by_test_id("run-refresh").click()
    expect(ui.get_by_test_id("refresh-summary")).to_contain_text("goal snapshots")
