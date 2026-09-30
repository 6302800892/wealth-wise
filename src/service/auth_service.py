"""Stub authentication with seeded users and bearer session tokens (NFR-04)."""

import logging
from datetime import timedelta

from src.config.clock import iso_timestamp
from src.repository import users_repo
from src.repository.db import transaction
from src.service.context import ServiceContext
from src.service.security import new_token, token_hash, verify_password
from src.types.errors import WealthWiseError
from src.types.identity import AuthUser

log = logging.getLogger(__name__)


def _unauthenticated(message: str = "authentication required") -> WealthWiseError:
    return WealthWiseError("UNAUTHENTICATED", message)


def _to_auth_user(record: users_repo.UserRecord) -> AuthUser:
    return AuthUser(
        user_id=record.id, username=record.username, role=record.role,
        customer_id=record.customer_id, display_name=record.display_name,
    )


def login(ctx: ServiceContext, username: str, password: str) -> tuple[str, AuthUser]:
    record = users_repo.find_by_username(ctx.conn, username)
    if record is None or not verify_password(password, record.password_hash):
        log.info("login_failed")
        raise _unauthenticated("invalid username or password")
    token = new_token()
    expires = ctx.clock.now() + timedelta(minutes=ctx.settings.session_ttl_minutes)
    with transaction(ctx.conn):
        users_repo.insert_session(
            ctx.conn, token_hash=token_hash(token), user_id=record.id,
            expires_at=iso_timestamp(expires), now=ctx.now_iso(),
        )
    log.info("login_succeeded", extra={"user_id": record.id, "role": record.role.value})
    return token, _to_auth_user(record)


def authenticate(ctx: ServiceContext, token: str | None) -> AuthUser:
    if not token:
        raise _unauthenticated()
    record = users_repo.find_session_user(ctx.conn, token_hash(token), ctx.now_iso())
    if record is None:
        raise _unauthenticated("session is invalid or expired")
    return _to_auth_user(record)


def logout(ctx: ServiceContext, token: str) -> None:
    with transaction(ctx.conn):
        users_repo.delete_session(ctx.conn, token_hash(token))
