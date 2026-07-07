"""Authentication service.

Owns the auth business rules — registration, login, refresh-token rotation
and logout — by composing the repository layer and the crypto primitives in
``security``. It raises domain errors (``utils.errors``); translating them to
HTTP lives in the router layer.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .. import security
from ..models import Role, User
from ..repositories import RefreshTokenRepository, UserRepository
from ..schemas import Token
from ..utils.errors import InvalidCredentialsError, UsernameTakenError


class AuthService:
    """Coordinates users + refresh tokens for the auth flows."""

    def __init__(
        self,
        *,
        users: UserRepository | None = None,
        refresh_tokens: RefreshTokenRepository | None = None,
    ) -> None:
        self._users = users or UserRepository()
        self._refresh = refresh_tokens or RefreshTokenRepository()

    def register(
        self, session: Session, *, username: str, password: str, role: str = Role.USER.value
    ) -> User:
        """Create an account. Raises if the username is taken."""
        if self._users.get_by_username(session, username) is not None:
            raise UsernameTakenError(username)
        return self._users.create(
            session,
            username=username,
            hashed_password=security.hash_password(password),
            role=role,
        )

    def login(self, session: Session, *, username: str, password: str) -> Token:
        """Verify credentials and issue a fresh access+refresh pair."""
        user = self._users.get_by_username(session, username)
        if user is None or not security.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        return self._issue_tokens(session, user)

    def refresh(self, session: Session, *, refresh_token: str) -> Token:
        """Rotate a refresh token: validate, revoke the old, issue a new pair."""
        token_hash = security.hash_refresh_token(refresh_token)
        stored = self._refresh.get_active(session, token_hash)
        if stored is None:
            raise InvalidCredentialsError
        user = self._users.get(session, stored.user_id)
        if user is None:
            raise InvalidCredentialsError
        # Rotation: the presented token is single-use.
        self._refresh.revoke(session, stored)
        return self._issue_tokens(session, user)

    def logout(self, session: Session, *, refresh_token: str) -> None:
        """Revoke the presented refresh token (idempotent)."""
        stored = self._refresh.get_active(session, security.hash_refresh_token(refresh_token))
        if stored is not None:
            self._refresh.revoke(session, stored)

    def _issue_tokens(self, session: Session, user: User) -> Token:
        """Mint an access JWT and persist a new opaque refresh token."""
        access = security.create_access_token(user_id=user.id, role=user.role)
        raw_refresh = security.generate_refresh_token()
        self._refresh.add(
            session,
            user_id=user.id,
            token_hash=security.hash_refresh_token(raw_refresh),
            expires_at=security.refresh_expiry(),
        )
        return Token(access_token=access, refresh_token=raw_refresh)
