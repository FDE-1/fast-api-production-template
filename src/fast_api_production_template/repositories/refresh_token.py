from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import RefreshToken


class RefreshTokenRepository:
    """Persistence access for :class:`RefreshToken` entities."""

    def add(
        self, session: Session, *, user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        """Persist a freshly issued refresh token."""
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        session.add(token)
        session.flush()
        return token

    def get_active(self, session: Session, token_hash: str) -> RefreshToken | None:
        """Return a non-revoked, non-expired token matching the hash, else None."""
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
        return session.scalars(stmt).first()

    def revoke(self, session: Session, token: RefreshToken) -> None:
        """Mark a token dead (rotation or logout)."""
        token.revoked = True
        session.flush()

    def revoke_all_for_user(self, session: Session, user_id: int) -> None:
        """Kill every refresh token of a user (global logout / compromise)."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
        )
        for token in session.scalars(stmt).all():
            token.revoked = True
        session.flush()
