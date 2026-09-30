"""NFR-04: every route except the public allow-list declares an auth/role dependency."""

from fastapi.routing import APIRoute

PUBLIC_ROUTES = {("GET", "/health"), ("POST", "/api/v1/auth/login")}


def _dependency_calls(dependant):
    for dependency in dependant.dependencies:
        yield dependency.call
        yield from _dependency_calls(dependency)


def _is_guard(call) -> bool:
    return getattr(call, "__wealthwise_auth__", None) is not None


def _api_routes(app):
    return [route for route in app.routes if isinstance(route, APIRoute)]


def test_all_non_public_routes_are_guarded(app):
    unguarded = []
    for route in _api_routes(app):
        for method in route.methods:
            if (method, route.path) in PUBLIC_ROUTES:
                continue
            if not any(_is_guard(call) for call in _dependency_calls(route.dependant)):
                unguarded.append(f"{method} {route.path}")
    assert unguarded == []


def test_role_scoped_prefixes_use_matching_role(app):
    expected = {"/api/v1/me": "CUSTOMER", "/api/v1/advisor": "ADVISOR", "/api/v1/admin": "ADMIN"}
    for route in _api_routes(app):
        for prefix, role in expected.items():
            if route.path.startswith(prefix):
                roles = {getattr(c, "__wealthwise_auth__", None) for c in _dependency_calls(route.dependant)}
                assert role in roles, f"{route.path} must require {role}"


def test_public_routes_exist(app):
    paths = {(m, r.path) for r in _api_routes(app) for m in r.methods}
    assert PUBLIC_ROUTES <= paths
