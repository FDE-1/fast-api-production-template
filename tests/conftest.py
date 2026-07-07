from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fast_api_production_template.dependencies import get_db
from fast_api_production_template.main import app
from fast_api_production_template.models import Base, Comment, Post, User
from fast_api_production_template.security import hash_password

SEED_PASSWORD = "secret123"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")

if TEST_DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Iterator[None]:
    """Clear rate-limit counters between tests so shared IP/user keys don't
    bleed across cases and trip the global default_limits."""
    from fast_api_production_template.utils.rate_limit import limiter

    limiter.reset()
    yield


@pytest.fixture
def db_session() -> Iterator[Session]:
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def seeded(db_session: Session) -> Session:
    alice = User(name="alice", hashed_password=hash_password(SEED_PASSWORD), role="user")
    db_session.add(alice)
    db_session.flush()

    posts = [
        Post(user_id=alice.id, content="hello world"),
        Post(user_id=alice.id, content="second post"),
        Post(user_id=alice.id, content="hello again"),
    ]
    db_session.add_all(posts)
    db_session.flush()

    db_session.add(Comment(post_id=posts[0].id, content="nice"))
    db_session.commit()
    return db_session


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient, seeded: Session) -> dict[str, str]:
    """Log the seeded user in and return a real Bearer access-token header."""
    resp = client.post("/auth/login", json={"username": "alice", "password": SEED_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
