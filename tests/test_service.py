"""Unit tests for the Service layer (no HTTP)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from fast_api_production_template.services import Service

service = Service()


def test_get_user_found(seeded: Session) -> None:
    user = service.get_user(seeded, 1)
    assert user is not None
    assert user.name == "alice"


def test_get_user_missing(seeded: Session) -> None:
    assert service.get_user(seeded, 999) is None


def test_get_user_posts_all(seeded: Session) -> None:
    posts = service.get_user_posts(seeded, 1)
    assert len(posts) == 3


def test_get_user_posts_pagination(seeded: Session) -> None:
    posts = service.get_user_posts(seeded, 1, skip=1, limit=1)
    assert len(posts) == 1
    assert posts[0].id == 2


def test_get_user_posts_filter(seeded: Session) -> None:
    posts = service.get_user_posts(seeded, 1, q="hello")
    assert {p.id for p in posts} == {1, 3}


def test_get_user_posts_sort_desc_column(seeded: Session) -> None:
    posts = service.get_user_posts(seeded, 1, sort="user_id")
    assert [p.id for p in posts] == [1, 2, 3]


def test_get_post_comments(seeded: Session) -> None:
    comments = service.get_post_comments(seeded, 1)
    assert len(comments) == 1
    assert comments[0].content == "nice"


def test_get_post_comments_filter_empty(seeded: Session) -> None:
    assert service.get_post_comments(seeded, 1, q="zzz") == []


def test_repr_methods(seeded: Session) -> None:
    user = service.get_user(seeded, 1)
    posts = service.get_user_posts(seeded, 1)
    comments = service.get_post_comments(seeded, 1)
    assert user is not None
    assert "alice" in repr(user)
    assert "content" in repr(posts[0])
    assert "content" in repr(comments[0])
