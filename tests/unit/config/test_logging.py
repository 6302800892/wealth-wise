"""NFR-03 / NFR-06: structured JSON logs with correlation IDs and PII redaction."""

import io
import json
import logging

from src.config.logging_config import JsonFormatter
from src.config.request_context import correlation_scope


def _capture(message: str, **extra) -> dict:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("test.logging")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.info(message, extra=extra)
    return json.loads(stream.getvalue().strip())


def test_log_line_is_json_with_required_fields():
    with correlation_scope("corr-123"):
        line = _capture("goal_created", goal_id="g-1")
    assert line["event"] == "goal_created"
    assert line["level"] == "INFO"
    assert line["logger"] == "test.logging"
    assert line["correlation_id"] == "corr-123"
    assert line["goal_id"] == "g-1"
    assert "ts" in line


def test_pii_and_financial_fields_are_dropped():
    line = _capture(
        "customer_event",
        customer_id="c-1",
        full_name="Sentinel Name",
        email="sentinel@example.test",
        target_amount="500000.00",
        units="10.0000",
        note="private advisor note",
        password="secret",
    )
    serialized = json.dumps(line)
    assert line["customer_id"] == "c-1"
    for leaked in ["Sentinel Name", "sentinel@example.test", "500000.00", "10.0000", "private", "secret"]:
        assert leaked not in serialized


def test_correlation_defaults_outside_request():
    line = _capture("startup")
    assert line["correlation_id"] == "-"
