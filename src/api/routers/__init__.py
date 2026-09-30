"""API routers (controllers). Each role-scoped router declares its role guard at router level."""

from src.api.routers import admin, auth, customer, portfolio

ROUTERS = [auth.router, customer.questionnaire_router, customer.router, portfolio.router, admin.router]
