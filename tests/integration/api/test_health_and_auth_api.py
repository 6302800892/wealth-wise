"""NFR-04 / NFR-06 / NFR-07: health endpoint, authentication boundary, correlation IDs."""

import time

from tests.conftest import TEST_PASSWORD


def test_health_returns_200_within_one_second(client):
    started = time.perf_counter()
    response = client.get("/health")
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
    assert elapsed < 1.0


def test_login_returns_token_and_role(client):
    response = client.post("/api/v1/auth/login", json={"username": "customer.alpha", "password": TEST_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "CUSTOMER"
    assert len(body["token"]) >= 32


def test_login_with_wrong_password_is_rejected(client):
    response = client.post("/api/v1/auth/login", json={"username": "customer.alpha", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth):
    response = client.get("/api/v1/auth/me", headers=auth("advisor.one"))
    assert response.status_code == 200
    assert response.json()["role"] == "ADVISOR"


def test_logout_revokes_token(client, auth):
    headers = auth("admin.one")
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_correlation_id_is_echoed_and_in_error_body(client):
    response = client.get("/api/v1/auth/me", headers={"X-Correlation-ID": "abc-123"})
    assert response.headers["X-Correlation-ID"] == "abc-123"
    assert response.json()["error"]["correlation_id"] == "abc-123"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/health")
    assert len(response.headers["X-Correlation-ID"]) >= 16


def test_unknown_route_uses_error_envelope(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
