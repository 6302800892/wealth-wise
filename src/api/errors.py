"""Consistent error envelope (spec §10.1) and code → HTTP status mapping."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.request_context import get_correlation_id
from src.types.errors import WealthWiseError

log = logging.getLogger(__name__)

STATUS_BY_CODE = {
    "VALIDATION_FAILED": 422,
    "INVALID_ANSWERS": 422,
    "ALLOCATION_SUM_INVALID": 422,
    "BAND_UNCHANGED": 422,
    "UNAUTHENTICATED": 401,
    "FORBIDDEN": 403,
    "KYC_NOT_VERIFIED": 403,
    "NOT_FOUND": 404,
}
DEFAULT_CONFLICT = 409

_HTTP_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 401: "UNAUTHENTICATED", 403: "FORBIDDEN"}


def error_response(status: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details or {},
                      "correlation_id": get_correlation_id()}}
    return JSONResponse(status_code=status, content=body)


async def _wealthwise_error(_: Request, exc: WealthWiseError) -> JSONResponse:
    return error_response(STATUS_BY_CODE.get(exc.code, DEFAULT_CONFLICT), exc.code, exc.message, exc.details)


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Drop "input"/"ctx" so rejected client values (possibly PII) are never echoed or logged.
    errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in exc.errors()]
    return error_response(422, "VALIDATION_FAILED", "request validation failed", {"errors": errors})


async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
    return error_response(exc.status_code, code, str(exc.detail))


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", extra={"exception_type": type(exc).__name__})
    return error_response(500, "INTERNAL_ERROR", "unexpected server error")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(WealthWiseError, _wealthwise_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unhandled)
