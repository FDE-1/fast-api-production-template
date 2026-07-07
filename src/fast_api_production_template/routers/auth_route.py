from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    SessionDep,
    require_role,
)
from ..models import Role
from ..schemas import LoginRequest, RefreshRequest, Token, UserCreate, UserRead
from ..utils.errors import InvalidCredentialsError, UsernameTakenError
from ..utils.rate_limit import limiter
from ..utils.settings import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.login_rate_limit)
async def register(
    request: Request, payload: UserCreate, session: SessionDep, auth: AuthServiceDep
) -> UserRead:
    """Create an account (role defaults to 'user')."""
    try:
        user = auth.register(session, username=payload.username, password=payload.password)
    except UsernameTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        ) from exc
    session.commit()
    return UserRead(id=user.id, name=user.name, role=user.role)


@router.post("/login", response_model=Token)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request, payload: LoginRequest, session: SessionDep, auth: AuthServiceDep
) -> Token:
    """Exchange username+password for an access+refresh token pair."""
    try:
        token = auth.login(session, username=payload.username, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc
    session.commit()
    return token


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.login_rate_limit)
async def refresh(
    request: Request, payload: RefreshRequest, session: SessionDep, auth: AuthServiceDep
) -> Token:
    """Rotate the refresh token: get a new pair, invalidate the old refresh."""
    try:
        token = auth.refresh(session, refresh_token=payload.refresh_token)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc
    session.commit()
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.login_rate_limit)
async def logout(
    request: Request, payload: RefreshRequest, session: SessionDep, auth: AuthServiceDep
) -> None:
    """Revoke the given refresh token (idempotent)."""
    auth.logout(session, refresh_token=payload.refresh_token)
    session.commit()


@router.get("/me", response_model=UserRead)
@limiter.limit(settings.user_rate_limit)
async def me(request: Request, current: CurrentUserDep) -> UserRead:
    """Return the authenticated user's identity + role."""
    return UserRead(id=current.id, name=current.username, role=current.role)


@router.get(
    "/admin/ping",
    dependencies=[Depends(require_role(Role.ADMIN.value))],
)
@limiter.limit(settings.user_rate_limit)
async def admin_ping(request: Request) -> dict[str, str]:
    """Admin-only endpoint — demonstrates the RBAC guard (403 for non-admins)."""
    return {"status": "ok", "scope": "admin"}
