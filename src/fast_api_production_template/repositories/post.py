from __future__ import annotations

from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from ..models import Post
from .pagination import paginate


class PostRepository:
    """Persistence access for :class:`Post` entities."""

    #: Whitelist mapping public sort keys to ORM columns. Guards against
    #: arbitrary column injection from caller-supplied ``sort`` strings.
    _SORT_COLUMNS: Final[dict[str, InstrumentedAttribute[int]]] = {
        "id": Post.id,
        "user_id": Post.user_id,
    }

    def list_for_user(
        self,
        session: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
        sort: str = "id",
    ) -> list[Post]:
        """Return a page of a user's posts, optionally filtered and sorted."""
        stmt = select(Post).where(Post.user_id == user_id)
        if q:
            stmt = stmt.where(Post.content.contains(q))
        stmt = stmt.order_by(self._SORT_COLUMNS.get(sort, Post.id))
        return list(session.scalars(paginate(stmt, skip=skip, limit=limit)).all())
