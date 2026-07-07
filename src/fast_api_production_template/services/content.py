"""Content service: read-side orchestration for users, posts, comments."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Comment, Post, User
from ..repositories import CommentRepository, PostRepository, UserRepository


class Service:
    """Application service coordinating the repository layer.

    Repositories are injectable to keep the service unit-testable; sensible
    defaults are constructed when none are supplied.
    """

    def __init__(
        self,
        *,
        users: UserRepository | None = None,
        posts: PostRepository | None = None,
        comments: CommentRepository | None = None,
    ) -> None:
        self._users = users or UserRepository()
        self._posts = posts or PostRepository()
        self._comments = comments or CommentRepository()

    def get_user(self, session: Session, id: int) -> User | None:
        """Return the user with the given id."""
        return self._users.get(session, id)

    def get_user_posts(
        self,
        session: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
        sort: str = "id",
    ) -> list[Post]:
        """Return a page of the user's posts for the given query."""
        return self._posts.list_for_user(session, user_id, skip=skip, limit=limit, q=q, sort=sort)

    def get_post_comments(
        self,
        session: Session,
        post_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
        sort: str = "id",
    ) -> list[Comment]:
        """Return a page of the post's comments for the given query."""
        return self._comments.list_for_post(session, post_id, skip=skip, limit=limit, q=q)
