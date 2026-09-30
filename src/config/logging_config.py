"""Structured JSON logging with correlation IDs (NFR-06) and PII redaction (NFR-03)."""

import json
import logging
import sys
from datetime import UTC, datetime

from src.config.request_context import get_correlation_id

# Keys that may carry PII or financial-position data. They are never serialised.
REDACTED_KEYS = frozenset(
    {
        "full_name", "name", "email", "date_of_birth", "dob", "note", "reason",
        "units", "value", "amount", "target_amount", "current_value", "total", "total_value",
        "nav", "percent_complete", "password", "token", "authorization", "answers",
    }
)

_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Render each record as one JSON object; only safe `extra` fields are included."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_ATTRS or key.lower() in REDACTED_KEYS:
                continue
            payload[key] = value if isinstance(value, (str, int, bool)) or value is None else str(value)
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(noisy).handlers = []
        logging.getLogger(noisy).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
