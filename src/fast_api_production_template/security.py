from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from .utils.settings import settings

_password_hash = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    """Return an Argon2 hash of the plaintext password."""
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time check of a plaintext against a stored hash."""
    return _password_hash.verify(plain, hashed)


def create_access_token(*, user_id: int, role: str) -> str:
    """Sign a short-lived access JWT carrying the subject and RBAC role."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify signature + expiry and return the claims. Raises on invalid."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def generate_refresh_token() -> str:
    """Cryptographically-random opaque token handed to the client."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex digest — only this is persisted, never the raw token."""
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_expiry() -> datetime:
    """Absolute expiry timestamp for a newly issued refresh token."""
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
