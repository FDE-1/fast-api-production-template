"""Auth flow + RBAC tests: register, login, refresh rotation, logout."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fast_api_production_template.models import Role
from fast_api_production_template.services import AuthService


def _register(client: TestClient, username: str, password: str) -> None:
    resp = client.post("/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text


def test_register_returns_user(client: TestClient, db_session: Session) -> None:
    resp = client.post("/auth/register", json={"username": "carol", "password": "password123"})
    assert resp.status_code == 201
    assert resp.json() == {"id": 1, "name": "carol", "role": "user"}


def test_register_duplicate_conflicts(client: TestClient, db_session: Session) -> None:
    _register(client, "carol", "password123")
    resp = client.post("/auth/register", json={"username": "carol", "password": "password123"})
    assert resp.status_code == 409


def test_login_wrong_password(client: TestClient, db_session: Session) -> None:
    _register(client, "carol", "password123")
    resp = client.post("/auth/login", json={"username": "carol", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client: TestClient, db_session: Session) -> None:
    resp = client.post("/auth/login", json={"username": "ghost", "password": "password123"})
    assert resp.status_code == 401


def test_me_returns_identity(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "name": "alice", "role": "user"}


def test_admin_forbidden_for_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/auth/admin/ping", headers=auth_headers)
    assert resp.status_code == 403


def test_admin_allowed_for_admin(client: TestClient, db_session: Session) -> None:
    AuthService().register(
        db_session, username="root", password="password123", role=Role.ADMIN.value
    )
    db_session.commit()
    token = client.post("/auth/login", json={"username": "root", "password": "password123"}).json()[
        "access_token"
    ]
    resp = client.get("/auth/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "scope": "admin"}


def test_refresh_rotation_invalidates_old(client: TestClient, db_session: Session) -> None:
    _register(client, "carol", "password123")
    tok = client.post("/auth/login", json={"username": "carol", "password": "password123"}).json()
    old_refresh = tok["refresh_token"]

    rotated = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200

    reused = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401


def test_logout_revokes_refresh(client: TestClient, db_session: Session) -> None:
    _register(client, "carol", "password123")
    refresh = client.post(
        "/auth/login", json={"username": "carol", "password": "password123"}
    ).json()["refresh_token"]

    assert client.post("/auth/logout", json={"refresh_token": refresh}).status_code == 204
    after = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert after.status_code == 401


def test_register_after_seed_no_pk_collision(client: TestClient, seeded: Session) -> None:
    resp = client.post("/auth/register", json={"username": "dave", "password": "password123"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != 1 
