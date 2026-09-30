"""NFR-04: every operation except the public allow-list sits behind the auth boundary,
and role-scoped prefixes reject every other role. Verified behaviourally against the OpenAPI surface."""

import re

PUBLIC_OPERATIONS = {("GET", "/health"), ("POST", "/api/v1/auth/login")}
ROLE_PREFIXES = {"/api/v1/me": "customer.alpha", "/api/v1/advisor": "advisor.one", "/api/v1/admin": "admin.one"}
ALL_USERS = set(ROLE_PREFIXES.values())


def _operations(client):
    schema = client.get("/openapi.json").json()
    for path, operations in schema["paths"].items():
        for method in operations:
            yield method.upper(), path


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path)


def test_public_operations_exist(client):
    assert PUBLIC_OPERATIONS <= set(_operations(client))


def test_all_non_public_operations_require_authentication(client):
    unguarded = []
    for method, path in _operations(client):
        if (method, path) in PUBLIC_OPERATIONS:
            continue
        response = client.request(method, _concrete(path), json={})
        if response.status_code != 401:
            unguarded.append(f"{method} {path} -> {response.status_code}")
    assert unguarded == []


def test_role_scoped_operations_reject_other_roles(client, auth):
    headers = {user: auth(user) for user in ALL_USERS}
    leaks = []
    for method, path in _operations(client):
        owner = next((user for prefix, user in ROLE_PREFIXES.items() if path.startswith(prefix)), None)
        if owner is None:
            continue
        for intruder in ALL_USERS - {owner}:
            response = client.request(method, _concrete(path), json={}, headers=headers[intruder])
            if response.status_code != 403:
                leaks.append(f"{intruder}: {method} {path} -> {response.status_code}")
    assert leaks == []
