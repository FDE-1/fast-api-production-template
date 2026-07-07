"""Per-user rate limiting via slowapi.

The limit bucket is keyed by the authenticated user id (from the JWT), so
each account gets its own quota regardless of IP. Unauthenticated / invalid
tokens fall back to the client IP.
"""

from __future__ import annotations

import jwt
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ..security import decode_access_token
from .settings import settings


def user_id_key(request: Request) -> str:
    """Rate-limit key: ``user:<id>`` for a valid access token, else the IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = decode_access_token(auth[len("Bearer ") :])
            if payload.get("type") == "access":
                return f"user:{payload['sub']}"
        except jwt.PyJWTError:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=user_id_key, default_limits=settings.default_limits)  # type: ignore[arg-type]


def setup_rate_limiter(app: FastAPI) -> None:
    """Wire the limiter + 429 handler onto the app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
