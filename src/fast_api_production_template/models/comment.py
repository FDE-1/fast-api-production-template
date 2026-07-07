from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .post import Post


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"))
    content: Mapped[str] = mapped_column(String(50))

    post: Mapped["Post"] = relationship(back_populates="list_comment")

    def __repr__(self) -> str:
        return f"Comment(id={self.id!r}, post_id={self.post_id!r} ,content={self.content!r})"
