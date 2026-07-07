from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import engine
from .repositories import UserRepository
from .security import decode_access_token
from .services import AuthService, Service


def get_db() -> Iterator[Session]:
    """Yield a session and guarantee it is closed after the request."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

# Reads "Authorization: Bearer <jwt>". tokenUrl powers Swagger's Authorize.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@dataclass
class CurrentUser:
    id: int
    username: str
    role: str


async def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    """Decode the access JWT, load the user, and expose identity + role.

    Loading the user fresh (not trusting the token blindly) means a deleted
    or downgraded account is rejected on its next request.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise credentials_exc from exc

    user = UserRepository().get(session, user_id)
    if user is None:
        raise credentials_exc
    return CurrentUser(id=user.id, username=user.name, role=user.role)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(*allowed: str) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    """Build a dependency that admits only the given RBAC roles (403 else)."""

    async def checker(current: CurrentUserDep) -> CurrentUser:
        if current.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current

    return checker


@dataclass
class CommonParams:
    q: str | None
    skip: int
    limit: int
    sort: str


async def common_parameters(
    q: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: str = "id",
) -> CommonParams:
    """Return in the form of an object"""
    return CommonParams(q=q, skip=skip, limit=limit, sort=sort)


CommonsDep = Annotated[CommonParams, Depends(common_parameters)]

_service_instance = Service()


def get_service() -> Service:
    """Return the instace of the service"""
    return _service_instance


ServiceDep = Annotated[Service, Depends(get_service)]

_auth_service_instance = AuthService()


def get_auth_service() -> AuthService:
    """Return the shared AuthService instance."""
    return _auth_service_instance


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
