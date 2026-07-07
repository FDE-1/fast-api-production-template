from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .user import User


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    content: Mapped[str] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="list_post")
    list_comment: Mapped[list["Comment"]] = relationship(back_populates="post")

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, user_id={self.user_id!r} ,content={self.content!r})"
