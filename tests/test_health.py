"""Health probe tests: liveness always up, readiness reflects the DB."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from fast_api_production_template.dependencies import get_db
from fast_api_production_template.main import app


def test_liveness(client: TestClient) -> None:
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}


def test_readiness_ok(client: TestClient) -> None:
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_readiness_db_down_returns_503(client: TestClient) -> None:
    class BoomSession:
        def execute(self, *args: object, **kwargs: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    def broken_db() -> Iterator[BoomSession]:
        yield BoomSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        resp = client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 503
    assert resp.json() == {"detail": "database unavailable"}
