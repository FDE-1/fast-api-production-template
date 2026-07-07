from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class RefreshToken(Base):
    """A single issued refresh token.

    We store only the SHA-256 *hash* of the opaque token, never the token
    itself: a DB leak then cannot be replayed. Rotation revokes the old row
    and inserts a new one on every /auth/refresh.
    """

    __tablename__ = "refresh_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    # SHA-256 hex digest of the opaque token; unique so lookup is O(1).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    # Set True on rotation or explicit logout — a revoked token is dead.
    revoked: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"RefreshToken(id={self.id!r}, user_id={self.user_id!r}, revoked={self.revoked!r})"
