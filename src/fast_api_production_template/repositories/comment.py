from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Comment
from .pagination import paginate


class CommentRepository:
    """Persistence access for :class:`Comment` entities."""

    def list_for_post(
        self,
        session: Session,
        post_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
    ) -> list[Comment]:
        """Return a page of a post's comments, optionally filtered."""
        stmt = select(Comment).where(Comment.post_id == post_id)
        if q:
            stmt = stmt.where(Comment.content.contains(q))
        stmt = stmt.order_by(Comment.id)
        return list(session.scalars(paginate(stmt, skip=skip, limit=limit)).all())
