"""E2E — customer journey: questionnaire → goal → recommendation (AC-01, AC-03, AC-04, AC-02)."""

import pytest
from playwright.sync_api import expect

from tests.e2e.snapshots import check_aria, screenshot

pytestmark = pytest.mark.e2e

ANSWERS = ["Q1_C", "Q2_C", "Q3_C", "Q4_C", "Q5_B", "Q6_B"]  # scores 3,3,3,3,2,2 = 16


def _goal_date_suffix(viewport: str) -> str:
    return "2036-09-30" if viewport == "desktop" else "2036-10-31"


@pytest.mark.ac("AC-01")
@pytest.mark.ac("AC-03")
@pytest.mark.ac("AC-04")
def test_new_customer_profiles_sets_goal_and_gets_recommendation(ui):
    """AC-01 / AC-03 / AC-04: beta scores 16 → MODERATE, adds a 10-year goal, gets a LONG allocation summing to 100%."""
    ui.login("customer.beta")
    ui.goto("/#/risk-profile")
    for option in ANSWERS:
        ui.get_by_test_id(f"answer-{option}").check()
    ui.get_by_test_id("submit-assessment").click()
    expect(ui.get_by_test_id("assessment-score")).to_have_text("16")
    expect(ui.get_by_test_id("assessment-result").get_by_test_id("risk-band")).to_have_text("MODERATE")

    ui.goto("/#/goals")
    ui.get_by_test_id("goal-name").fill(f"Retirement {ui.viewport_name}")
    ui.get_by_test_id("goal-type").select_option("RETIREMENT")
    ui.get_by_test_id("goal-amount").fill("5000000.00")
    ui.get_by_test_id("goal-date").fill(_goal_date_suffix(ui.viewport_name))
    ui.get_by_test_id("goal-submit").click()
    expect(ui.get_by_test_id("goals-table")).to_contain_text(f"Retirement {ui.viewport_name}")

    ui.goto("/#/recommendation")
    ui.get_by_test_id("generate-recommendation").click()
    expect(ui.get_by_test_id("allocation-total")).to_have_text("100.00%")
    expect(ui.get_by_test_id("horizon")).to_have_text("Long")
    check_aria(ui.get_by_test_id("allocation-table"), f"recommendation-moderate-long-{ui.viewport_name}")
    screenshot(ui, "recommendation")


@pytest.mark.ac("AC-03")
def test_goal_validation_error_is_shown(ui):
    """AC-03.3: a zero amount is rejected by the API and the error envelope is displayed."""
    ui.login("customer.beta")
    ui.goto("/#/goals")
    ui.get_by_test_id("goal-name").fill("Invalid")
    ui.get_by_test_id("goal-amount").fill("0.00")
    ui.get_by_test_id("goal-date").fill("2030-01-31")
    ui.get_by_test_id("goal-submit").click()
    expect(ui.get_by_test_id("error-notice")).to_contain_text("VALIDATION_FAILED")


@pytest.mark.ac("AC-04")
def test_kyc_pending_customer_sees_block(ui):
    """AC-04.5: customer gamma (KYC pending) is told a recommendation needs KYC."""
    ui.login("customer.gamma")
    ui.goto("/#/recommendation")
    ui.get_by_test_id("generate-recommendation").click()
    expect(ui.get_by_test_id("error-notice")).to_contain_text("KYC_NOT_VERIFIED")
