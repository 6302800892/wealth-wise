"""E2E — responsive layout (spec §13): phone menu toggle and stacked tables below 640px."""

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.snapshots import screenshot

pytestmark = pytest.mark.e2e


def test_navigation_adapts_to_viewport(ui):
    ui.login("customer.alpha")
    toggle = ui.get_by_test_id("menu-toggle")
    nav_link = ui.get_by_test_id("nav-holdings")
    if ui.viewport_name == "mobile":
        expect(toggle).to_be_visible()
        expect(nav_link).to_be_hidden()
        toggle.click()
        expect(nav_link).to_be_visible()
        screenshot(ui, "menu-open")
        nav_link.click()
    else:
        expect(toggle).to_be_hidden()
        nav_link.click()
    expect(ui.get_by_test_id("holdings-table")).to_be_visible()


def test_tables_stack_into_cards_on_phones(ui):
    ui.login("customer.alpha")
    ui.goto("/#/holdings")
    header = ui.get_by_test_id("holdings-table").locator("thead")
    if ui.viewport_name == "mobile":
        expect(header).to_be_hidden()
    else:
        expect(header).to_be_visible()


def test_login_page_renders_at_both_widths(ui):
    ui.goto("/#/login")
    expect(ui.get_by_test_id("login-form")).to_be_visible()
    screenshot(ui, "login")


@pytest.mark.parametrize("path", ["/#/admin/templates", "/#/advisor/customers"])
def test_customer_cannot_open_other_role_pages(ui, path):
    """NFR-04 in the UI: a customer is redirected away from advisor/admin routes."""
    if ui.viewport_name == "mobile":
        pytest.skip("routing guard is viewport independent")
    ui.login("customer.alpha")
    ui.goto(path)
    expect(ui).to_have_url(re.compile(r".*#/dashboard$"))
