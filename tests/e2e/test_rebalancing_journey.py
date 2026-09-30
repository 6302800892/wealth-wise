"""E2E — drifted customer: holdings/drift → rebalancing proposal → accept (AC-05, AC-06, AC-07, AC-08)."""

import pytest
from playwright.sync_api import expect

from tests.e2e.snapshots import check_aria, screenshot

pytestmark = pytest.mark.e2e


@pytest.mark.ac("AC-05")
def test_holdings_show_portfolio_e1_drift(ui):
    """AC-05: alpha's portfolio totals ₹10,00,000.00 and EQUITY drift 10.00% is flagged."""
    ui.login("customer.alpha")
    ui.goto("/#/holdings")
    expect(ui.get_by_test_id("holdings-total")).to_have_text("₹10,00,000.00")
    expect(ui.get_by_test_id("drift-EQUITY")).to_have_text("10.00%")
    expect(ui.get_by_test_id("drift-GOLD")).to_have_text("0.00%")
    check_aria(ui.get_by_test_id("holdings-table"), f"holdings-e1-{ui.viewport_name}")
    screenshot(ui, "holdings")


@pytest.mark.ac("AC-08")
def test_dashboard_shows_alert_and_goal_progress(ui):
    """AC-06 / AC-08: dashboard warns about drift and shows the home goal at 25.00%."""
    ui.login("customer.alpha")
    expect(ui.get_by_test_id("rebalancing-alert")).to_contain_text("10.00%")
    expect(ui.get_by_test_id("goal-progress")).to_contain_text("25.00%")
    screenshot(ui, "dashboard")


@pytest.mark.ac("AC-06")
@pytest.mark.ac("AC-07")
def test_accepting_the_proposal_places_stub_orders(ui):
    """AC-06 / AC-07: proposal shows SELL 666.6666 EQUITY and BUY 4000.0000 DEBT; accepting closes it."""
    ui.login("customer.alpha")
    ui.goto("/#/rebalancing")
    ui.get_by_test_id("evaluate-drift").click()
    lines = ui.get_by_test_id("proposal-lines")
    expect(lines).to_contain_text("666.6666")
    expect(lines).to_contain_text("4000.0000")
    check_aria(lines, f"rebalancing-proposal-e1-{ui.viewport_name}")
    screenshot(ui, "rebalancing-open")
    ui.get_by_test_id("accept-proposal").click()
    expect(ui.get_by_test_id("no-open-proposal")).to_be_visible()
    expect(ui.get_by_test_id("rebalancing-history")).to_contain_text("ACCEPTED")
