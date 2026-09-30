"""NFR-03: running the main journeys never writes PII or financial-position values to the logs."""

import io
import logging

from src.config.logging_config import JsonFormatter
from tests.integration.api.helpers import create_goal, profile_customer

SENTINELS = ["Aarav Alpha", "alpha@example.test", "1988-04-12", "1000000.00", "600000.00", "2000000.00",
             "4000.0000", "Sentinel private note", "Test-Only-Password"]


def test_journeys_do_not_log_pii(client, auth):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    previous_level = root.level
    root.setLevel(logging.DEBUG)
    try:
        alpha, beta, advisor = auth("customer.alpha"), auth("customer.beta"), auth("advisor.one")
        client.get("/api/v1/me/holdings", headers=alpha)
        rebalancing = client.post("/api/v1/me/rebalancing/evaluate", headers=alpha).json()["rebalancing"]
        client.post(f"/api/v1/me/rebalancing/{rebalancing['recommendation_id']}/dismiss",
                    json={"reason": "Sentinel private note"}, headers=alpha)
        profile_customer(client, beta)
        create_goal(client, beta, amount="2000000.00")
        customer_id = client.get("/api/v1/auth/me", headers=alpha).json()["customer_id"]
        client.post(f"/api/v1/advisor/customers/{customer_id}/risk-band-overrides",
                    json={"new_band": "AGGRESSIVE", "reason_code": "ADVISOR_ASSESSMENT",
                          "note": "Sentinel private note"}, headers=advisor)
        client.get(f"/api/v1/advisor/customers/{customer_id}/portfolio", headers=advisor)
        client.post("/api/v1/admin/nav/refresh", headers=auth("admin.one"))
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)
    output = stream.getvalue()
    assert "http_request" in output, "expected request logs to be captured"
    leaked = [s for s in SENTINELS if s in output]
    assert leaked == []
