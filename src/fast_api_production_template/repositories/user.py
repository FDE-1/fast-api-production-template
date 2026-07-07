from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User


class UserRepository:
    """Persistence access for :class:`User` entities."""

    def get(self, session: Session, user_id: int) -> User | None:
        """Return the user with ``user_id`` or ``None`` if absent."""
        return session.scalars(select(User).where(User.id == user_id)).first()

    def get_by_username(self, session: Session, username: str) -> User | None:
        """Return the user with ``username`` or ``None`` — used at login."""
        return session.scalars(select(User).where(User.name == username)).first()

    def create(self, session: Session, *, username: str, hashed_password: str, role: str) -> User:
        """Insert a new user and flush so the generated id is available."""
        user = User(name=username, hashed_password=hashed_password, role=role)
        session.add(user)
        session.flush()
        return user
