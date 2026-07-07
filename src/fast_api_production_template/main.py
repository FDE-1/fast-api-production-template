from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import engine
from .routers import auth, comments, health, metrics, posts, users
from .utils.logger import logger
from .utils.metrics import setup_metrics_middleware
from .utils.rate_limit import setup_rate_limiter
from .utils.setup import setup_exception_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Startup")
    yield
    logger.info("Shutdown: disposing engine")
    engine.dispose()


app = FastAPI(lifespan=lifespan)
setup_exception_middleware(app)
setup_metrics_middleware(app)
setup_rate_limiter(app)

app.include_router(metrics.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
