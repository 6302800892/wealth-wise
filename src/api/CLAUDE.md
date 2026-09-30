# src/api/ — controllers and the authentication boundary (NFR-04)

- Routers live in `routers/` and are registered in `routers/__init__.py::ROUTERS`, mounted under `/api/v1`.
- **Guards.** Role-scoped routers declare `dependencies=[Depends(customer_user | advisor_user | admin_user)]`. Only `GET /health` and `POST /api/v1/auth/login` are public. `tests/architecture/test_routes_have_auth.py` calls every OpenAPI operation to prove it.
- Customers act on `/me/*` only. A foreign resource returns **404**, not 403.
- **Schemas** (`schemas.py`) use `extra="forbid"`. Money, units and percentage fields are `str`, so JSON numbers are rejected with 422.
- **Errors.** Raise or let `WealthWiseError` propagate. `errors.py` maps codes to statuses and wraps everything in the §10.1 envelope with `correlation_id`. Validation errors drop the offending input values so PII is never echoed.
- Controllers stay thin: parse, call one service function, return its dict. No business rules here, and no `src.repository` imports (import-linter).
