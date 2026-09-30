"""Authenticated principal passed from the API boundary into services."""

from dataclasses import dataclass

from src.types.enums import Role


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    username: str
    role: Role
    customer_id: str | None
    display_name: str
