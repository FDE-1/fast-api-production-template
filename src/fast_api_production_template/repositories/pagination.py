from __future__ import annotations

from typing import Final, TypeVar

from sqlalchemy import Select

#: Hard ceiling on page size, enforced regardless of caller input.
MAX_PAGE_SIZE: Final[int] = 100

_T = TypeVar("_T")


def paginate(stmt: Select[tuple[_T]], *, skip: int, limit: int) -> Select[tuple[_T]]:
    """Apply a clamped ``OFFSET``/``LIMIT`` window to a statement."""
    return stmt.offset(max(skip, 0)).limit(min(max(limit, 0), MAX_PAGE_SIZE))
