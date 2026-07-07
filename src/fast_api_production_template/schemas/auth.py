from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Registration payload."""

    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Credentials for /auth/login."""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """Body for /auth/refresh — the opaque refresh token."""

    refresh_token: str


class Token(BaseModel):
    """Token pair returned by login/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
