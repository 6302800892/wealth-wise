"""API routers (controllers). Each role-scoped router declares its role guard at router level."""

from src.api.routers import auth, customer

ROUTERS = [auth.router, customer.questionnaire_router, customer.router]
