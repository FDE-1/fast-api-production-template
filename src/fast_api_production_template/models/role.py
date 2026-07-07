from enum import Enum


class Role(str, Enum):
    """RBAC roles. Stored as its string value in the DB."""

    USER = "user"
    ADMIN = "admin"
