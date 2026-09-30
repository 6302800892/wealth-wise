"""Request dependencies: service context and the role-based authentication boundary (NFR-04)."""

from collections.abc import Callable, Iterator

from fastapi import Depends, Header, Request

from src.service import auth_service
from src.service.context import ServiceContext, open_context
from src.types.enums import Role
from src.types.errors import WealthWiseError
from src.types.identity import AuthUser


def get_ctx(request: Request) -> Iterator[ServiceContext]:
    with open_context(request.app.state.settings, request.app.state.clock) as ctx:
        yield ctx


def bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def require_authenticated(
    ctx: ServiceContext = Depends(get_ctx), token: str | None = Depends(bearer_token)
) -> AuthUser:
    return auth_service.authenticate(ctx, token)


require_authenticated.__wealthwise_auth__ = "ANY"


def require_role(role: Role) -> Callable[..., AuthUser]:
    def dependency(user: AuthUser = Depends(require_authenticated)) -> AuthUser:
        if user.role != role:
            raise WealthWiseError("FORBIDDEN", f"this endpoint requires the {role.value} role")
        return user

    dependency.__wealthwise_auth__ = role.value
    dependency.__name__ = f"require_{role.value.lower()}"
    return dependency


customer_user = require_role(Role.CUSTOMER)
advisor_user = require_role(Role.ADVISOR)
admin_user = require_role(Role.ADMIN)
