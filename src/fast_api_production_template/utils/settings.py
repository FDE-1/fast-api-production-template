from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite://"
    echo_sql: bool = False

    secret_key: str = "dev-only-insecure-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    user_rate_limit: str = "30/minute"
    login_rate_limit: str = "5/minute"
    default_limits: list[str] = ["60/minute"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")


settings = Settings()
