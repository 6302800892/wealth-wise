"""API routers (controllers). Each role-scoped router declares its role guard at router level."""

from src.api.routers import auth

ROUTERS = [auth.router]
