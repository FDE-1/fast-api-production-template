"""HTTP-level tests for the FastAPI routes, auth and middleware."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_read_user_ok(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "name": "alice", "role": "user"}


def test_read_user_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/999", headers=auth_headers)
    assert resp.status_code == 404


def test_missing_auth_returns_401(client: TestClient, seeded: Session) -> None:
    resp = client.get("/users/1")
    assert resp.status_code == 401


def test_bad_token_returns_401(client: TestClient, seeded: Session) -> None:
    resp = client.get("/users/1", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_user_posts_ok(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1/posts", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_user_posts_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1/posts?skip=1&limit=1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == 2


def test_user_posts_filter(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1/posts?q=hello", headers=auth_headers)
    assert {p["id"] for p in resp.json()} == {1, 3}


def test_limit_out_of_range_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1/posts?limit=9999", headers=auth_headers)
    assert resp.status_code == 422  # Query(le=100)


def test_post_comments_ok(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/posts/1/comments", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["content"] == "nice"


def test_correlation_id_generated(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/users/1", headers=auth_headers)
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) > 0


def test_correlation_id_echoed(client: TestClient, auth_headers: dict[str, str]) -> None:
    headers = {**auth_headers, "X-Request-ID": "my-trace-42"}
    resp = client.get("/users/1", headers=headers)
    assert resp.headers["x-request-id"] == "my-trace-42"


def test_background_email_task(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    # Patch the name as bound in the router module (imported via `from ..services`).
    monkeypatch.setattr(
        "fast_api_production_template.routers.user_route.send_welcome_email",
        lambda email: calls.append(email),
    )
    resp = client.get("/users/1", headers=auth_headers)
    assert resp.status_code == 200
    assert calls == ["alice@example.com"]
