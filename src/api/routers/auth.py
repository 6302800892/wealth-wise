"""Authentication endpoints: login (public), logout and current user."""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from src.api.deps import bearer_token, get_ctx, require_authenticated
from src.service import auth_service
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


def _user_body(user: AuthUser) -> dict:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value,
        "customer_id": user.customer_id,
        "display_name": user.display_name,
    }


@router.post("/login")
def login(body: LoginRequest, ctx: ServiceContext = Depends(get_ctx)) -> dict:
    token, user = auth_service.login(ctx, body.username, body.password)
    return {"token": token, **_user_body(user)}


@router.post("/logout", status_code=204)
def logout(
    _: AuthUser = Depends(require_authenticated),
    token: str | None = Depends(bearer_token),
    ctx: ServiceContext = Depends(get_ctx),
) -> Response:
    auth_service.logout(ctx, token or "")
    return Response(status_code=204)


@router.get("/me")
def me(user: AuthUser = Depends(require_authenticated)) -> dict:
    return _user_body(user)
