# FastAPI Production Template

A production-ready FastAPI starter built around a clean, layered architecture.
It ships with JWT authentication (access + rotating refresh tokens), role-based
access control, Alembic migrations, Prometheus metrics, health probes, rate
limiting, and a strict quality gate (mypy `--strict`, Ruff, 90% test coverage).

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.139-009688">
  <img alt="Typing" src="https://img.shields.io/badge/mypy-strict-2a6db2">
  <img alt="Coverage" src="https://img.shields.io/badge/coverage-%E2%89%A590%25-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-black">
</p>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Request Lifecycle](#request-lifecycle)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Database & Migrations](#database--migrations)
- [Observability](#observability)
- [Testing & Quality](#testing--quality)
- [Deployment](#deployment)
- [License](#license)

---

## Features

| Domain | What you get |
|---|---|
| **Architecture** | Strict layering: `routers → services → repositories → models` |
| **Auth** | JWT access tokens + rotating refresh tokens, logout/revocation |
| **Authorization** | Role-based access control (RBAC) via FastAPI dependencies |
| **Password hashing** | Argon2 through `pwdlib` |
| **Validation** | Pydantic v2 schemas at every boundary |
| **Persistence** | SQLAlchemy 2.0 (typed ORM), Alembic migrations |
| **Rate limiting** | Per-route limits via `slowapi` |
| **Observability** | Prometheus `/metrics`, structured logging (`loguru`) |
| **Health** | Kubernetes-style `live` / `ready` probes |
| **Quality** | `mypy --strict`, Ruff (lint + format), Pytest ≥ 90% coverage |
| **Delivery** | Multi-stage Docker image (non-root), Docker Compose with Postgres |

---

## Architecture

The application follows a **layered (onion) architecture**. Each layer only
talks to the one directly beneath it, keeping HTTP concerns, business logic, and
data access cleanly separated and independently testable.

```
        ┌─────────────────────────────────────────────────────┐
 HTTP   │                     Routers                          │  FastAPI endpoints
        │      (auth, users, posts, comments, health, ...)     │  request/response only
        └───────────────────────────┬─────────────────────────┘
                                     │ Pydantic schemas (validation)
        ┌───────────────────────────▼─────────────────────────┐
 Logic  │                     Services                         │  business rules
        │        (auth, content, email) — orchestration        │  transactions, policy
        └───────────────────────────┬─────────────────────────┘
                                     │ domain calls
        ┌───────────────────────────▼─────────────────────────┐
 Data   │                   Repositories                       │  data access
        │      (user, post, comment, refresh_token)            │  queries, pagination
        └───────────────────────────┬─────────────────────────┘
                                     │ SQLAlchemy ORM
        ┌───────────────────────────▼─────────────────────────┐
 Models │                      Models                          │  SQLAlchemy tables
        │        (user, role, post, comment, refresh_token)    │  + Alembic migrations
        └───────────────────────────┬─────────────────────────┘
                                     │
                              ┌──────▼──────┐
                              │  Database   │  Postgres (prod) / SQLite (dev)
                              └─────────────┘

 Cross-cutting: security (JWT), dependencies (DI), rate_limit, metrics,
                logger, exception handling, settings.
```

**Layer responsibilities**

- **Routers** — declare endpoints, parse/validate input with Pydantic schemas,
  serialize output. No business logic. Own HTTP status codes and error mapping.
- **Services** — the business core. Enforce rules (e.g. unique username, token
  rotation, credential checks) and own the transaction boundary (`commit`).
- **Repositories** — the only layer that builds queries. Encapsulate persistence
  and pagination; return domain models.
- **Models** — SQLAlchemy 2.0 typed ORM entities; the source of truth for the
  schema, versioned by Alembic.
- **Cross-cutting** — `security` (JWT encode/decode), `dependencies` (DI wiring:
  session, current user, `require_role`), rate limiting, metrics, logging, and
  centralized exception handling wired in `main.py`.

---

## Project Layout

```
.
├── src/fast_api_production_template/
│   ├── main.py               # App factory: routers, middleware, lifespan
│   ├── database.py           # Engine + session factory
│   ├── dependencies.py       # DI: SessionDep, CurrentUserDep, require_role
│   ├── security.py           # JWT encode/decode, password hashing
│   ├── models/               # SQLAlchemy ORM entities
│   │   ├── user.py  role.py  post.py  comment.py  refresh_token.py
│   ├── repositories/         # Data access + pagination
│   ├── services/             # Business logic (auth, content, email)
│   ├── schemas/              # Pydantic request/response models
│   ├── routers/              # HTTP endpoints
│   └── utils/                # settings, logger, metrics, rate_limit, errors
├── alembic/                  # Migration environment + versions
├── tests/                    # Pytest suite (api, auth, service, health)
├── Dockerfile                # Multi-stage, non-root runtime
├── docker-compose.yml        # App + Postgres + migration job
├── Makefile                  # install / lint / typecheck / test / all
└── pyproject.toml            # Single source of truth (deps + tooling)
```

---

## Request Lifecycle

Example: `POST /auth/login`

```
Client ──▶ Rate limiter (slowapi)  ── 5/minute guard
        ──▶ Router (auth_route)     ── validate LoginRequest schema
        ──▶ Service (auth)          ── verify credentials, issue token pair
        ──▶ Repository (user,       ── load user, persist refresh token
             refresh_token)
        ──▶ Model / DB              ── SQLAlchemy commit
        ◀── Token { access, refresh } serialized back to client
```

Metrics middleware records latency/counters and errors flow through the
centralized exception handler on every request.

---

## Quick Start

### Prerequisites

- Python **3.10+**
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- Docker + Docker Compose (optional, for the Postgres stack)

### Local development (SQLite)

```bash
git clone <this-repo> my-api
cd my-api

# Install deps + dev tooling + pre-commit hooks
make install

# Apply migrations
alembic upgrade head

# Run the API with autoreload
uvicorn fast_api_production_template.main:app --reload
```

Open the interactive docs at **http://127.0.0.1:8000/docs**.

### Full stack with Postgres (Docker Compose)

```bash
export APP_SECRET_KEY="$(openssl rand -hex 32)"
docker compose up --build
```

Compose starts Postgres, runs the Alembic migration job, then boots the API on
port `8000` — each with health checks.

---

## Configuration

All settings are environment variables prefixed with **`APP_`** (loaded from a
`.env` file if present). Defaults live in `utils/settings.py`.

| Variable | Default | Description |
|---|---|---|
| `APP_DATABASE_URL` | `sqlite://` | SQLAlchemy connection URL |
| `APP_ECHO_SQL` | `false` | Log emitted SQL |
| `APP_SECRET_KEY` | `dev-only-insecure-change-me` | JWT signing key — **override in prod** |
| `APP_ALGORITHM` | `HS256` | JWT signing algorithm |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token TTL |
| `APP_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `APP_USER_RATE_LIMIT` | `30/minute` | Default per-user route limit |
| `APP_LOGIN_RATE_LIMIT` | `5/minute` | Auth endpoints limit |
| `APP_DEFAULT_LIMITS` | `["60/minute"]` | Global fallback limit |

> ⚠️ **Never ship the default `APP_SECRET_KEY`.** Generate a strong 32+ byte key
> (`openssl rand -hex 32`) and inject it via your secrets manager.

---

## API Reference

Interactive OpenAPI docs: `/docs` (Swagger) and `/redoc`.

### Auth — `/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | — | Create an account (role defaults to `user`) |
| `POST` | `/auth/login` | — | Exchange credentials for an access + refresh pair |
| `POST` | `/auth/refresh` | — | Rotate refresh token, issue a fresh pair |
| `POST` | `/auth/logout` | — | Revoke a refresh token (idempotent) |
| `GET`  | `/auth/me` | Bearer | Current user identity + role |
| `GET`  | `/auth/admin/ping` | Bearer + `admin` | RBAC demo (403 for non-admins) |

### Content

| Method | Path | Description |
|---|---|---|
| `GET` | `/users/{user_id}` | Fetch a user |
| `GET` | `/users/{user_id}/posts` | List a user's posts (paginated) |
| `GET` | `/posts/{post_id}/comments` | List a post's comments (paginated) |

### Operations

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness probe |
| `GET` | `/health/ready` | Readiness probe (DB reachable) |
| `GET` | `/metrics` | Prometheus exposition format |

---

## Database & Migrations

The ORM (SQLAlchemy 2.0, typed) is the source of truth; schema changes are
versioned with **Alembic**.

```bash
# Create a new revision from model changes
alembic revision --autogenerate -m "add widget table"

# Apply all pending migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1
```

SQLite is the zero-config default for local dev; point `APP_DATABASE_URL` at
Postgres for production (`postgresql+psycopg://user:pass@host:5432/db`).

---

## Observability

- **Metrics** — Prometheus counters/histograms exposed at `/metrics`; request
  latency and status codes are captured by a middleware.
- **Logging** — structured logs via `loguru`, with startup/shutdown lifecycle
  events.
- **Health probes** — `/health/live` (process up) and `/health/ready`
  (dependencies reachable) suit Kubernetes liveness/readiness checks.

---

## Testing & Quality

```bash
make lint        # Ruff check + format --check
make typecheck   # mypy --strict
make test        # Pytest with coverage (fails under 90%)
make all         # lint + typecheck + test
```

Quality gates are enforced by `pyproject.toml`:

- **mypy** in `strict` mode (`warn_unreachable`, `no_implicit_reexport`, …)
- **Ruff** with `E, W, F, I, N, UP, B, ANN, RUF` rule sets, 100-char lines
- **Pytest** with `--cov`, failing under **90%** coverage
- **pre-commit** hooks run the same checks before every commit

---

## Deployment

The `Dockerfile` builds a lean, multi-stage image:

- **Builder stage** — `uv sync --frozen` for reproducible, locked installs
- **Runtime stage** — `python:3.11-slim`, runs as a **non-root** user (uid 10001)
- Bytecode compiled, `PYTHONUNBUFFERED=1`, exposes port `8000`

```bash
docker build -t fastapi-template:latest .
docker run -p 8000:8000 \
  -e APP_SECRET_KEY="$(openssl rand -hex 32)" \
  -e APP_DATABASE_URL="postgresql+psycopg://app:app@db:5432/app" \
  fastapi-template:latest
```

The bundled `docker-compose.yml` wires the API to Postgres and runs the Alembic
migration job before the app starts, with health checks on every service.

---

## License

MIT © 2026 Frédéric Dong
