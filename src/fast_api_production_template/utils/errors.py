class CustomApiError(Exception):
    """Error thrown when there is an api error"""


class AuthError(CustomApiError):
    """Base class for authentication/authorization failures."""


class InvalidCredentialsError(AuthError):
    """Wrong username/password, or an invalid/expired refresh token."""


class UsernameTakenError(AuthError):
    """Registration with an already-used username."""
