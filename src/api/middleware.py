"""Correlation-ID middleware and structured request logging (NFR-06)."""

import logging
import re
import time
import uuid

from fastapi import Request, Response

from src.config.request_context import correlation_scope

log = logging.getLogger("wealthwise.http")

HEADER = "X-Correlation-ID"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _correlation_id(request: Request) -> str:
    incoming = request.headers.get(HEADER)
    return incoming if incoming and _SAFE_ID.match(incoming) else uuid.uuid4().hex


async def correlation_middleware(request: Request, call_next) -> Response:
    correlation_id = _correlation_id(request)
    started = time.perf_counter()
    with correlation_scope(correlation_id):
        response = await call_next(request)
        route = request.scope.get("route")
        log.info(
            "http_request",
            extra={
                "method": request.method,
                "path": getattr(route, "path", "unmatched"),
                "status": response.status_code,
                "duration_ms": int((time.perf_counter() - started) * 1000),
            },
        )
    response.headers[HEADER] = correlation_id
    return response
