from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .errors import CustomApiError
from .logger import logger

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def setup_exception_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Log the info"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(request_id)
        try:
            with logger.contextualize(request_id=request_id):
                logger.info("--> {} {}", request.method, request.url.path)
                response = await call_next(request)
                logger.info("<-- {} {}", response.status_code, request.url.path)
        finally:
            request_id_ctx.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(CustomApiError)
    async def custom_api_handler(request: Request, exc: CustomApiError) -> JSONResponse:
        """Api handler"""
        return JSONResponse(
            status_code=404, content={"message": f"Something went wrong in {exc.args[0]}"}
        )
