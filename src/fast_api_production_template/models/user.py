from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .role import Role

if TYPE_CHECKING:
    from .post import Post
    from .refresh_token import RefreshToken


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Login identifier: must be unique so it maps 1:1 to an account.
    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    # Argon2 hash — never the plaintext password.
    hashed_password: Mapped[str] = mapped_column(String(128))
    # RBAC role, defaults to the least-privileged role.
    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)

    list_post: Mapped[list["Post"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, role={self.role!r})"
