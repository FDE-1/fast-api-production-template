import os

from sqlalchemy import create_engine

DATABASE_URL: str = os.getenv("APP_DATABASE_URL", "sqlite:///./app.db")

# check_same_thread is a SQLite-only pysqlite arg; passing it to any other
# driver (e.g. psycopg for Postgres) raises. Only set it for SQLite.
_connect_args: dict[str, object] = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    DATABASE_URL,
    echo=bool(os.getenv("APP_ECHO_SQL")),
    connect_args=_connect_args,
)
