"""Request-scoped correlation ID (NFR-06), stored in a context variable."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

NO_CORRELATION = "-"

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default=NO_CORRELATION)


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


@contextmanager
def correlation_scope(value: str) -> Iterator[None]:
    token = _correlation_id.set(value)
    try:
        yield
    finally:
        _correlation_id.reset(token)
